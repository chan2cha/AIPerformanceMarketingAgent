from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class UsagePeriod(BaseModel):
    from_: datetime | None = Field(serialization_alias="from")
    to: datetime | None


class UsageByTask(BaseModel):
    task: str
    calls: int
    estimated_cost_usd: Decimal


class UsageSummaryResponse(BaseModel):
    period: UsagePeriod
    estimated_cost_usd: Decimal
    calls: int
    by_task: list[UsageByTask]
