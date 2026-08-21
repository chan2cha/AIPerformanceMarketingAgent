from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.pricing import PricingCatalog
from app.ai.provider import ProviderResult
from app.ai.schemas import AI_TASK
from app.modules.usage.model import ApiUsage


def record_provider_usage(
    session: Session,
    *,
    organization_id: UUID,
    user_id: UUID | None,
    job_id: UUID,
    result: ProviderResult,
    pricing: PricingCatalog | None = None,
) -> ApiUsage:
    existing = session.scalar(
        select(ApiUsage).where(ApiUsage.job_id == job_id, ApiUsage.task == AI_TASK)
    )
    if existing is not None:
        return existing

    catalog = pricing or PricingCatalog()
    estimated_cost = catalog.estimate(
        result.provider,
        result.model,
        result.usage.input_units,
        result.usage.output_units,
        result.usage.cached_input_units,
    )
    usage = ApiUsage(
        organization_id=organization_id,
        user_id=user_id,
        job_id=job_id,
        provider=result.provider,
        model=result.model,
        task=AI_TASK,
        input_units=result.usage.input_units,
        cached_input_units=result.usage.cached_input_units,
        output_units=result.usage.output_units,
        unit_type=result.usage.unit_type,
        estimated_cost_usd=Decimal(estimated_cost),
        request_id=result.request_id,
        latency_ms=result.latency_ms,
    )
    session.add(usage)
    return usage
