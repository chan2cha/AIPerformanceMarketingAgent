from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, HttpUrl


class PlanResponse(BaseModel):
    code: str
    name: str
    monthly_price_usd: Decimal
    monthly_credit_usd: Decimal
    analysis_limit: int
    collection_run_limit: int
    brand_limit: int
    competitor_limit: int


class AllowanceUsageResponse(BaseModel):
    credit_remaining_usd: Decimal
    analysis_used: int
    analysis_limit: int
    collection_runs_used: int
    collection_run_limit: int


class ProviderReadinessResponse(BaseModel):
    billing: bool
    apify: bool
    openai: bool


class BillingSummaryResponse(BaseModel):
    status: Literal["inactive", "trialing", "active", "past_due", "cancelled"]
    plan: PlanResponse
    allowance: AllowanceUsageResponse
    current_period_start: datetime | None
    current_period_end: datetime | None
    provider_readiness: ProviderReadinessResponse
    enforcement_enabled: bool


class CheckoutResponse(BaseModel):
    status: Literal["inactive", "active"]
    checkout_url: HttpUrl | None = None


class PortalResponse(BaseModel):
    portal_url: HttpUrl
