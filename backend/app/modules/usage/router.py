from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.errors import AppError
from app.modules.auth.authorization import require_organization_access
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.usage.repository import summarize_organization_usage
from app.modules.usage.schemas import UsageSummaryResponse

router = APIRouter(prefix="/api/v1", tags=["usage"])


@router.get(
    "/organizations/{organization_id}/usage",
    response_model=UsageSummaryResponse,
)
def get_organization_usage(
    organization_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: datetime | None = None,
    provider: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    task: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
) -> UsageSummaryResponse:
    require_organization_access(session, user, organization_id)
    if from_ is not None and to is not None and from_ > to:
        raise AppError(
            status_code=422,
            code="INVALID_USAGE_PERIOD",
            message="사용량 조회 시작 시각은 종료 시각보다 늦을 수 없습니다.",
        )
    return summarize_organization_usage(session, organization_id, from_, to, provider, task)
