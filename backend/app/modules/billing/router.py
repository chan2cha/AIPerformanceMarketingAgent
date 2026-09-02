from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.auth.authorization import require_organization_access
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.billing.provider import verify_stripe_webhook
from app.modules.billing.schemas import BillingSummaryResponse, CheckoutResponse, PortalResponse
from app.modules.billing.service import (
    apply_stripe_event,
    create_fake_checkout,
    get_billing_summary,
    get_stripe_provider,
)

router = APIRouter(prefix="/api/v1", tags=["billing"])


def _require_billing_manager(session: DatabaseSession, user: CurrentUser, organization_id: UUID):
    organization, membership = require_organization_access(session, user, organization_id)
    if membership.role not in {"owner", "admin"}:
        raise AppError(
            403,
            "BILLING_PERMISSION_DENIED",
            "결제는 Owner 또는 Admin만 관리할 수 있습니다.",
        )
    return organization


@router.get(
    "/organizations/{organization_id}/billing",
    response_model=BillingSummaryResponse,
)
def get_organization_billing(
    organization_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
) -> BillingSummaryResponse:
    require_organization_access(session, user, organization_id)
    return get_billing_summary(session, organization_id)


@router.post(
    "/organizations/{organization_id}/billing/checkout",
    response_model=CheckoutResponse,
)
def post_organization_checkout(
    organization_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
) -> CheckoutResponse:
    organization = _require_billing_manager(session, user, organization_id)
    settings = get_settings()
    if settings.billing_provider == "fake":
        create_fake_checkout(session, organization_id)
        return CheckoutResponse(status="active")
    if settings.billing_provider != "stripe":
        raise AppError(503, "BILLING_DISABLED", "결제 기능이 아직 활성화되지 않았습니다.")
    checkout = get_stripe_provider(settings).create_checkout(
        str(organization.id), organization.name
    )
    return CheckoutResponse(status="inactive", checkout_url=checkout.url)


@router.post(
    "/organizations/{organization_id}/billing/portal",
    response_model=PortalResponse,
)
def post_organization_billing_portal(
    organization_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
) -> PortalResponse:
    _require_billing_manager(session, user, organization_id)
    summary = get_billing_summary(session, organization_id)
    if summary.status == "inactive":
        raise AppError(409, "SUBSCRIPTION_INACTIVE", "활성 구독이 없습니다.")
    from sqlalchemy import select

    from app.modules.billing.model import Subscription

    subscription = session.scalar(
        select(Subscription).where(Subscription.organization_id == organization_id)
    )
    if subscription is None or not subscription.external_customer_id:
        raise AppError(409, "BILLING_PORTAL_UNAVAILABLE", "결제 관리 정보를 찾을 수 없습니다.")
    return PortalResponse(
        portal_url=get_stripe_provider().create_portal(subscription.external_customer_id)
    )


@router.post("/billing/webhooks/stripe")
async def post_stripe_webhook(
    request: Request,
    session: DatabaseSession,
    stripe_signature: Annotated[str | None, Header(alias="stripe-signature")] = None,
) -> dict[str, bool]:
    settings = get_settings()
    if not settings.stripe_webhook_secret or not stripe_signature:
        raise AppError(400, "INVALID_WEBHOOK_SIGNATURE", "결제 webhook 서명이 없습니다.")
    payload = await request.body()
    event = verify_stripe_webhook(
        payload,
        stripe_signature,
        settings.stripe_webhook_secret.get_secret_value(),
    )
    apply_stripe_event(session, event)
    return {"received": True}
