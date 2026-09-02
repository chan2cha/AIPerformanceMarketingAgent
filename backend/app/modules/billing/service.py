from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError, ServiceUnavailableError
from app.modules.billing.model import CreditLedger, Subscription
from app.modules.billing.provider import StripeBillingProvider
from app.modules.billing.schemas import (
    AllowanceUsageResponse,
    BillingSummaryResponse,
    PlanResponse,
    ProviderReadinessResponse,
)
from app.modules.jobs.model import Job
from app.modules.organizations.model import Organization

ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}
PLAN_CODE = "pilot_40"


def _next_month(value: datetime) -> datetime:
    if value.month == 12:
        return value.replace(
            year=value.year + 1,
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    return value.replace(month=value.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _current_month() -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, _next_month(start)


def plan_from_settings(settings: Settings) -> PlanResponse:
    return PlanResponse(
        code=PLAN_CODE,
        name="$40 주간 광고 인텔리전스",
        monthly_price_usd=settings.billing_monthly_price_usd,
        monthly_credit_usd=settings.billing_monthly_credit_usd,
        analysis_limit=settings.billing_analysis_limit,
        collection_run_limit=settings.billing_collection_run_limit,
        brand_limit=settings.billing_brand_limit,
        competitor_limit=settings.billing_competitor_limit,
    )


def credit_balance(session: Session, organization_id: UUID) -> Decimal:
    value = session.scalar(
        select(func.coalesce(func.sum(CreditLedger.amount_usd), 0)).where(
            CreditLedger.organization_id == organization_id
        )
    )
    return Decimal(value or 0)


def _usage_count(
    session: Session,
    organization_id: UUID,
    job_type: str,
    period_start: datetime,
    period_end: datetime,
) -> int:
    return int(
        session.scalar(
            select(func.count(Job.id)).where(
                Job.organization_id == organization_id,
                Job.job_type == job_type,
                Job.created_at >= period_start,
                Job.created_at < period_end,
                Job.status != "cancelled",
            )
        )
        or 0
    )


def get_billing_summary(
    session: Session,
    organization_id: UUID,
    settings: Settings | None = None,
) -> BillingSummaryResponse:
    settings = settings or get_settings()
    subscription = session.scalar(
        select(Subscription).where(Subscription.organization_id == organization_id)
    )
    default_start, default_end = _current_month()
    period_start = subscription.current_period_start if subscription else default_start
    period_end = subscription.current_period_end if subscription else default_end
    if period_start is None:
        period_start = default_start
    if period_end is None:
        period_end = default_end
    status = subscription.status if subscription else "inactive"
    plan = plan_from_settings(settings)
    billing_ready = settings.billing_provider == "fake" and settings.app_env != "production"
    billing_ready = billing_ready or bool(
        settings.stripe_secret_key and settings.stripe_price_id and settings.stripe_webhook_secret
    )
    return BillingSummaryResponse(
        status=status,  # type: ignore[arg-type]
        plan=plan,
        allowance=AllowanceUsageResponse(
            credit_remaining_usd=max(credit_balance(session, organization_id), Decimal("0")),
            analysis_used=_usage_count(
                session, organization_id, "creative_analysis", period_start, period_end
            ),
            analysis_limit=plan.analysis_limit,
            collection_runs_used=_usage_count(
                session, organization_id, "market_content_sync", period_start, period_end
            ),
            collection_run_limit=plan.collection_run_limit,
        ),
        current_period_start=subscription.current_period_start if subscription else None,
        current_period_end=subscription.current_period_end if subscription else None,
        provider_readiness=ProviderReadinessResponse(
            billing=billing_ready,
            apify=settings.apify_configured,
            openai=settings.openai_configured,
        ),
        enforcement_enabled=settings.billing_enforcement_enabled,
    )


def _add_ledger_entry(
    session: Session,
    *,
    organization_id: UUID,
    subscription_id: UUID | None,
    job_id: UUID | None,
    entry_type: str,
    amount_usd: Decimal,
    idempotency_key: str,
    description: str,
    metadata: dict[str, object] | None = None,
) -> CreditLedger:
    existing = session.scalar(
        select(CreditLedger).where(
            CreditLedger.organization_id == organization_id,
            CreditLedger.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing
    entry = CreditLedger(
        organization_id=organization_id,
        subscription_id=subscription_id,
        job_id=job_id,
        entry_type=entry_type,
        amount_usd=amount_usd,
        idempotency_key=idempotency_key,
        description=description,
        entry_metadata=metadata or {},
    )
    session.add(entry)
    return entry


def activate_subscription(
    session: Session,
    *,
    organization_id: UUID,
    billing_provider: str,
    external_customer_id: str | None,
    external_subscription_id: str | None,
    status: str = "active",
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    settings: Settings | None = None,
) -> Subscription:
    settings = settings or get_settings()
    fallback_start, fallback_end = _current_month()
    period_start = period_start or fallback_start
    period_end = period_end or fallback_end
    subscription = session.scalar(
        select(Subscription)
        .where(Subscription.organization_id == organization_id)
        .with_for_update()
    )
    if subscription is None:
        subscription = Subscription(
            organization_id=organization_id,
            plan_code=PLAN_CODE,
            status=status,
            billing_provider=billing_provider,
        )
        session.add(subscription)
        session.flush()
    subscription.plan_code = PLAN_CODE
    subscription.status = status
    subscription.billing_provider = billing_provider
    subscription.external_customer_id = external_customer_id or subscription.external_customer_id
    subscription.external_subscription_id = (
        external_subscription_id or subscription.external_subscription_id
    )
    subscription.current_period_start = period_start
    subscription.current_period_end = period_end
    if status in ACTIVE_SUBSCRIPTION_STATUSES:
        grant_reference = external_subscription_id or f"{billing_provider}:{organization_id}"
        grant_key = f"grant:{grant_reference}:{period_start.isoformat()}"
        existing_grant = session.scalar(
            select(CreditLedger).where(
                CreditLedger.organization_id == organization_id,
                CreditLedger.idempotency_key == grant_key,
            )
        )
        if existing_grant is None:
            remaining = credit_balance(session, organization_id)
            if remaining > 0:
                _add_ledger_entry(
                    session,
                    organization_id=organization_id,
                    subscription_id=subscription.id,
                    job_id=None,
                    entry_type="adjustment",
                    amount_usd=-remaining,
                    idempotency_key=f"expire:{grant_key}",
                    description="이전 결제 기간의 미사용 provider credit 만료",
                )
            _add_ledger_entry(
                session,
                organization_id=organization_id,
                subscription_id=subscription.id,
                job_id=None,
                entry_type="grant",
                amount_usd=settings.billing_monthly_credit_usd,
                idempotency_key=grant_key,
                description=f"{PLAN_CODE} 월간 provider credit 지급",
                metadata={
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                },
            )
        organization = session.get(Organization, organization_id)
        if organization is not None:
            organization.plan = PLAN_CODE
    session.commit()
    session.refresh(subscription)
    return subscription


def create_fake_checkout(session: Session, organization_id: UUID) -> Subscription:
    settings = get_settings()
    if settings.app_env == "production":
        raise AppError(
            403,
            "FAKE_BILLING_DISABLED",
            "운영 환경에서는 테스트 결제를 사용할 수 없습니다.",
        )
    return activate_subscription(
        session,
        organization_id=organization_id,
        billing_provider="fake",
        external_customer_id=f"fake-customer:{organization_id}",
        external_subscription_id=f"fake-subscription:{organization_id}",
        settings=settings,
    )


def get_stripe_provider(settings: Settings | None = None) -> StripeBillingProvider:
    settings = settings or get_settings()
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise ServiceUnavailableError(
            code="BILLING_NOT_CONFIGURED",
            message="운영 결제 설정이 아직 완료되지 않았습니다.",
        )
    return StripeBillingProvider(
        secret_key=settings.stripe_secret_key.get_secret_value(),
        price_id=settings.stripe_price_id,
        success_url=settings.billing_success_url,
        cancel_url=settings.billing_cancel_url,
        api_base_url=settings.stripe_api_base_url,
    )


def prepare_job_reservation(
    session: Session,
    organization_id: UUID,
    job_type: str,
    settings: Settings | None = None,
) -> tuple[Subscription, Decimal] | None:
    settings = settings or get_settings()
    if not settings.billing_enforcement_enabled:
        return None
    subscription = session.scalar(
        select(Subscription)
        .where(Subscription.organization_id == organization_id)
        .with_for_update()
    )
    now = datetime.now(UTC)
    if (
        subscription is None
        or subscription.status not in ACTIVE_SUBSCRIPTION_STATUSES
        or subscription.current_period_end is None
        or subscription.current_period_end <= now
    ):
        raise AppError(402, "SUBSCRIPTION_REQUIRED", "$40 플랜 결제 후 사용할 수 있습니다.")
    period_start = subscription.current_period_start or now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    period_end = subscription.current_period_end
    if job_type == "creative_analysis":
        limit = settings.billing_analysis_limit
        reservation = settings.billing_analysis_reservation_usd
        message = "이번 달 AI 분석 제공량을 모두 사용했습니다."
    else:
        limit = settings.billing_collection_run_limit
        reservation = settings.billing_collection_reservation_usd
        message = "이번 달 자동 수집 제공량을 모두 사용했습니다."
    if _usage_count(session, organization_id, job_type, period_start, period_end) >= limit:
        raise AppError(429, "MONTHLY_ALLOWANCE_EXHAUSTED", message)
    if credit_balance(session, organization_id) < reservation:
        raise AppError(402, "CREDIT_EXHAUSTED", "이번 달 provider credit을 모두 사용했습니다.")
    return subscription, reservation


def ensure_plan_resource_allowed(
    session: Session,
    organization_id: UUID,
    resource: str,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    if not settings.billing_enforcement_enabled:
        return
    subscription = session.scalar(
        select(Subscription)
        .where(Subscription.organization_id == organization_id)
        .with_for_update()
    )
    if subscription is None or subscription.status not in ACTIVE_SUBSCRIPTION_STATUSES:
        raise AppError(402, "SUBSCRIPTION_REQUIRED", "$40 플랜 결제 후 설정할 수 있습니다.")
    if resource == "brand":
        from app.modules.brands.model import Brand

        count = int(
            session.scalar(
                select(func.count(Brand.id)).where(Brand.organization_id == organization_id)
            )
            or 0
        )
        limit = settings.billing_brand_limit
        message = "현재 플랜에서는 브랜드를 더 추가할 수 없습니다."
    elif resource == "competitor":
        from app.modules.competitors.model import Competitor

        count = int(
            session.scalar(
                select(func.count(Competitor.id)).where(
                    Competitor.organization_id == organization_id
                )
            )
            or 0
        )
        limit = settings.billing_competitor_limit
        message = "현재 플랜에서는 경쟁 브랜드를 더 추가할 수 없습니다."
    else:
        raise ValueError(f"Unsupported plan resource: {resource}")
    if count >= limit:
        raise AppError(409, "PLAN_RESOURCE_LIMIT_REACHED", message)


def add_job_reservation(
    session: Session,
    job: Job,
    prepared: tuple[Subscription, Decimal] | None,
) -> None:
    if prepared is None:
        return
    subscription, amount = prepared
    _add_ledger_entry(
        session,
        organization_id=job.organization_id,
        subscription_id=subscription.id,
        job_id=job.id,
        entry_type="reservation",
        amount_usd=-amount,
        idempotency_key=f"reserve:{job.id}",
        description=f"{job.job_type} provider credit 예약",
        metadata={"reserved_usd": str(amount)},
    )


def settle_job_credit(session: Session, job: Job, actual_cost_usd: Decimal) -> None:
    reservation = session.scalar(
        select(CreditLedger).where(
            CreditLedger.organization_id == job.organization_id,
            CreditLedger.job_id == job.id,
            CreditLedger.entry_type == "reservation",
        )
    )
    if reservation is None:
        return
    reserved = -Decimal(reservation.amount_usd)
    _add_ledger_entry(
        session,
        organization_id=job.organization_id,
        subscription_id=reservation.subscription_id,
        job_id=job.id,
        entry_type="release",
        amount_usd=reserved,
        idempotency_key=f"release:{job.id}",
        description=f"{job.job_type} provider credit 예약 해제",
    )
    _add_ledger_entry(
        session,
        organization_id=job.organization_id,
        subscription_id=reservation.subscription_id,
        job_id=job.id,
        entry_type="settlement",
        amount_usd=-max(actual_cost_usd, Decimal("0")),
        idempotency_key=f"settle:{job.id}",
        description=f"{job.job_type} provider credit 확정",
        metadata={"actual_cost_usd": str(actual_cost_usd)},
    )


def settle_job_reserved_credit(session: Session, job: Job) -> None:
    reservation = session.scalar(
        select(CreditLedger).where(
            CreditLedger.organization_id == job.organization_id,
            CreditLedger.job_id == job.id,
            CreditLedger.entry_type == "reservation",
        )
    )
    if reservation is not None:
        settle_job_credit(session, job, -Decimal(reservation.amount_usd))


def release_job_credit(session: Session, job: Job) -> None:
    reservation = session.scalar(
        select(CreditLedger).where(
            CreditLedger.organization_id == job.organization_id,
            CreditLedger.job_id == job.id,
            CreditLedger.entry_type == "reservation",
        )
    )
    if reservation is None:
        return
    _add_ledger_entry(
        session,
        organization_id=job.organization_id,
        subscription_id=reservation.subscription_id,
        job_id=job.id,
        entry_type="release",
        amount_usd=-Decimal(reservation.amount_usd),
        idempotency_key=f"release:{job.id}",
        description=f"{job.job_type} 실패로 provider credit 예약 해제",
    )


def apply_stripe_event(session: Session, event: dict[str, Any]) -> None:
    event_type = event.get("type")
    data = event.get("data")
    stripe_object = data.get("object") if isinstance(data, dict) else None
    if not isinstance(stripe_object, dict):
        return
    metadata = stripe_object.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    organization_value = metadata.get("organization_id") or stripe_object.get(
        "client_reference_id"
    )
    if not isinstance(organization_value, str):
        return
    try:
        organization_id = UUID(organization_value)
    except ValueError:
        return
    if session.get(Organization, organization_id) is None:
        return
    if event_type == "checkout.session.completed":
        activate_subscription(
            session,
            organization_id=organization_id,
            billing_provider="stripe",
            external_customer_id=_string_or_none(stripe_object.get("customer")),
            external_subscription_id=_string_or_none(stripe_object.get("subscription")),
        )
        return
    if event_type not in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        return
    raw_status = stripe_object.get("status")
    status_map = {
        "active": "active",
        "trialing": "trialing",
        "past_due": "past_due",
        "unpaid": "past_due",
        "canceled": "cancelled",
        "incomplete_expired": "cancelled",
    }
    status = status_map.get(str(raw_status), "inactive")
    activate_subscription(
        session,
        organization_id=organization_id,
        billing_provider="stripe",
        external_customer_id=_string_or_none(stripe_object.get("customer")),
        external_subscription_id=_string_or_none(stripe_object.get("id")),
        status=status,
        period_start=_timestamp_or_none(stripe_object.get("current_period_start")),
        period_end=_timestamp_or_none(stripe_object.get("current_period_end")),
    )


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _timestamp_or_none(value: object) -> datetime | None:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)
    return None
