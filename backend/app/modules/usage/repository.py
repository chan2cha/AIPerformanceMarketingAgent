from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.usage.model import ApiUsage
from app.modules.usage.schemas import UsageByTask, UsagePeriod, UsageSummaryResponse


def summarize_organization_usage(
    session: Session,
    organization_id: UUID,
    from_: datetime | None,
    to: datetime | None,
    provider: str | None,
    task: str | None,
) -> UsageSummaryResponse:
    filters = [ApiUsage.organization_id == organization_id]
    if from_ is not None:
        filters.append(ApiUsage.created_at >= from_)
    if to is not None:
        filters.append(ApiUsage.created_at <= to)
    if provider is not None:
        filters.append(ApiUsage.provider == provider)
    if task is not None:
        filters.append(ApiUsage.task == task)

    rows = session.execute(
        select(
            ApiUsage.task,
            func.count(ApiUsage.id),
            func.coalesce(func.sum(ApiUsage.estimated_cost_usd), 0),
        )
        .where(*filters)
        .group_by(ApiUsage.task)
        .order_by(ApiUsage.task)
    ).all()
    by_task = [
        UsageByTask(task=row_task, calls=int(calls), estimated_cost_usd=Decimal(cost))
        for row_task, calls, cost in rows
    ]
    return UsageSummaryResponse(
        period=UsagePeriod(from_=from_, to=to),
        calls=sum(item.calls for item in by_task),
        estimated_cost_usd=sum(
            (item.estimated_cost_usd for item in by_task), start=Decimal("0")
        ),
        by_task=by_task,
    )
