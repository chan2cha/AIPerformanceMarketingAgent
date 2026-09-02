import asyncio
import hashlib
import hmac
import json
from decimal import Decimal
from urllib.parse import parse_qs
from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.core.config import Settings
from app.core.errors import AppError
from app.db.session import SessionLocal
from app.modules.billing.model import CreditLedger, Subscription
from app.modules.billing.provider import StripeBillingProvider, verify_stripe_webhook
from app.modules.billing.service import (
    add_job_reservation,
    prepare_job_reservation,
    settle_job_credit,
)
from app.modules.jobs.model import Job
from tests.api_helpers import ApiClient


def test_fake_checkout_activates_plan_once_and_is_tenant_isolated() -> None:
    async def scenario() -> tuple[str, str]:
        async with ApiClient() as client:
            organization_a = (
                await client.post("/api/v1/organizations", "billing-owner-a", {"name": "A"})
            ).json()
            organization_b = (
                await client.post("/api/v1/organizations", "billing-owner-b", {"name": "B"})
            ).json()

            initial = await client.get(
                f"/api/v1/organizations/{organization_a['id']}/billing", "billing-owner-a"
            )
            assert initial.status_code == 200
            assert initial.json()["status"] == "inactive"
            assert initial.json()["plan"]["monthly_price_usd"] == "40.00"
            assert initial.json()["allowance"]["credit_remaining_usd"] == "0"

            denied = await client.get(
                f"/api/v1/organizations/{organization_b['id']}/billing", "billing-owner-a"
            )
            assert denied.status_code == 404

            checkout = await client.post(
                f"/api/v1/organizations/{organization_a['id']}/billing/checkout",
                "billing-owner-a",
                {},
            )
            assert checkout.status_code == 200
            assert checkout.json() == {"status": "active", "checkout_url": None}

            repeated = await client.post(
                f"/api/v1/organizations/{organization_a['id']}/billing/checkout",
                "billing-owner-a",
                {},
            )
            assert repeated.status_code == 200

            summary = await client.get(
                f"/api/v1/organizations/{organization_a['id']}/billing", "billing-owner-a"
            )
            assert summary.json()["status"] == "active"
            assert summary.json()["allowance"]["credit_remaining_usd"] == "15.00000000"
            return organization_a["id"], organization_b["id"]

    organization_a_id, organization_b_id = asyncio.run(scenario())
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Subscription)) == 1
        entries = list(session.scalars(select(CreditLedger)))
        assert len(entries) == 1
        assert str(entries[0].organization_id) == organization_a_id
        assert str(entries[0].organization_id) != organization_b_id
        assert entries[0].entry_type == "grant"
        assert entries[0].amount_usd == Decimal("15.00000000")


def test_stripe_webhook_signature_validation() -> None:
    payload = json.dumps({"id": "evt_test", "type": "checkout.session.completed"}).encode()
    timestamp = 1_800_000_000
    secret = "whsec_test"
    digest = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256
    ).hexdigest()

    event = verify_stripe_webhook(
        payload,
        f"t={timestamp},v1={digest}",
        secret,
        now=timestamp,
    )
    assert event["id"] == "evt_test"

    with pytest.raises(AppError) as invalid:
        verify_stripe_webhook(
            payload,
            f"t={timestamp},v1=invalid",
            secret,
            now=timestamp,
        )
    assert invalid.value.code == "INVALID_WEBHOOK_SIGNATURE"


def test_job_credit_reservation_settlement_and_monthly_limit() -> None:
    async def activate() -> str:
        async with ApiClient() as client:
            organization = (
                await client.post("/api/v1/organizations", "credit-owner", {"name": "Credit"})
            ).json()
            response = await client.post(
                f"/api/v1/organizations/{organization['id']}/billing/checkout",
                "credit-owner",
                {},
            )
            assert response.status_code == 200
            return organization["id"]

    organization_id = UUID(asyncio.run(activate()))
    settings = Settings(
        billing_enforcement_enabled=True,
        billing_analysis_limit=1,
        billing_analysis_reservation_usd=Decimal("0.05"),
    )
    with SessionLocal() as session:
        prepared = prepare_job_reservation(
            session, organization_id, "creative_analysis", settings
        )
        assert prepared is not None
        job = Job(
            organization_id=organization_id,
            user_id=None,
            job_type="creative_analysis",
            target_type="creative",
            target_id=uuid4(),
            idempotency_key="billing-credit-test",
        )
        session.add(job)
        session.flush()
        add_job_reservation(session, job, prepared)
        session.commit()

        with pytest.raises(AppError) as exhausted:
            prepare_job_reservation(session, organization_id, "creative_analysis", settings)
        assert exhausted.value.code == "MONTHLY_ALLOWANCE_EXHAUSTED"

        settle_job_credit(session, job, Decimal("0.01"))
        session.commit()
        balance = session.scalar(
            select(func.sum(CreditLedger.amount_usd)).where(
                CreditLedger.organization_id == organization_id
            )
        )
        assert balance == Decimal("14.99000000")


def test_stripe_checkout_payload_and_production_config_guard() -> None:
    captured: dict[str, list[str]] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(parse_qs(request.content.decode()))
        assert request.headers["authorization"] == "Bearer sk_test"
        return httpx.Response(200, json={"url": "https://checkout.stripe.test/session"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = StripeBillingProvider(
        secret_key="sk_test",
        price_id="price_40",
        success_url="https://web.test/success",
        cancel_url="https://web.test/cancel",
        http_client=client,
    )
    result = provider.create_checkout(str(uuid4()), "Test Organization")
    assert result.url == "https://checkout.stripe.test/session"
    assert captured["mode"] == ["subscription"]
    assert captured["line_items[0][price]"] == ["price_40"]
    assert captured["subscription_data[metadata][organization_id]"]
    client.close()

    with pytest.raises(ValidationError):
        Settings(app_env="production", auth_mode="supabase", billing_provider="fake")
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            auth_mode="supabase",
            billing_provider="stripe",
            billing_enforcement_enabled=False,
        )
    valid = Settings(
        app_env="production",
        auth_mode="supabase",
        billing_provider="stripe",
        billing_enforcement_enabled=True,
        stripe_secret_key="sk_live",
        stripe_price_id="price_live",
        stripe_webhook_secret="whsec_live",
    )
    assert valid.billing_monthly_price_usd == Decimal("40.00")
