from datetime import datetime
from hashlib import sha256
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, Header, Query, status

from app.ai.schemas import PROMPT_VERSION
from app.core.errors import ServiceUnavailableError
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.brands.repository import get_authorized_brand
from app.modules.creatives.repository import (
    get_authorized_creative,
    list_brand_creatives,
    list_creative_analyses,
)
from app.modules.creatives.schemas import (
    AnalysisJobCreate,
    CreativeAnalysisResponse,
    CreativeCreate,
    CreativeDetailResponse,
    CreativeResponse,
)
from app.modules.creatives.service import create_creative
from app.modules.jobs.dispatcher import JobDispatcher, get_job_dispatcher
from app.modules.jobs.schemas import JobAcceptedResponse
from app.modules.jobs.service import create_analysis_job, mark_job_failed

router = APIRouter(prefix="/api/v1", tags=["creatives"])


@router.post(
    "/brands/{brand_id}/creatives",
    response_model=CreativeResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_creative(
    brand_id: UUID,
    payload: Annotated[CreativeCreate, Body()],
    session: DatabaseSession,
    user: CurrentUser,
) -> CreativeResponse:
    return CreativeResponse.model_validate(create_creative(session, user, brand_id, payload))


@router.get("/brands/{brand_id}/creatives", response_model=list[CreativeResponse])
def get_creatives(
    brand_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
    competitor_id: UUID | None = None,
    ownership_type: Literal["own", "competitor", "market"] | None = None,
    media_type: Literal["image", "video", "carousel", "text"] | None = None,
    analyzed: bool | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CreativeResponse]:
    brand = get_authorized_brand(session, user, brand_id)
    creatives = list_brand_creatives(
        session,
        brand.organization_id,
        brand.id,
        competitor_id,
        ownership_type,
        media_type,
        analyzed,
        created_from,
        created_to,
        offset,
        limit,
    )
    return [CreativeResponse.model_validate(creative) for creative in creatives]


@router.get("/creatives/{creative_id}", response_model=CreativeDetailResponse)
def get_creative(
    creative_id: UUID, session: DatabaseSession, user: CurrentUser
) -> CreativeDetailResponse:
    creative = get_authorized_creative(session, user, creative_id)
    analyses = list_creative_analyses(session, creative.id, creative.organization_id)
    return CreativeDetailResponse(
        **CreativeResponse.model_validate(creative).model_dump(),
        analyses=[CreativeAnalysisResponse.model_validate(item) for item in analyses],
    )


@router.post(
    "/creatives/{creative_id}/analyses",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_creative_analysis(
    creative_id: UUID,
    payload: Annotated[AnalysisJobCreate, Body()],
    session: DatabaseSession,
    user: CurrentUser,
    dispatcher: Annotated[JobDispatcher, Depends(get_job_dispatcher)],
    idempotency_key: Annotated[str | None, Header(max_length=255)] = None,
) -> JobAcceptedResponse:
    creative = get_authorized_creative(session, user, creative_id)
    requested_key = idempotency_key
    if requested_key is None:
        requested_key = str(uuid4()) if payload.force else PROMPT_VERSION
    key_digest = sha256(requested_key.encode("utf-8")).hexdigest()
    key = f"{creative.id}:{key_digest}"
    job, created = create_analysis_job(session, user, creative, key)
    if created:
        try:
            dispatcher.dispatch_creative_analysis(job.id)
        except Exception as error:
            mark_job_failed(
                session,
                job.id,
                "JOB_ENQUEUE_FAILED",
                "분석 Job을 queue에 등록하지 못했습니다.",
            )
            raise ServiceUnavailableError(
                code="JOB_ENQUEUE_FAILED",
                message="분석 Job을 queue에 등록하지 못했습니다.",
            ) from error
    return JobAcceptedResponse(job_id=job.id, status=job.status)


@router.get("/creatives/{creative_id}/analyses", response_model=list[CreativeAnalysisResponse])
def get_creative_analysis_history(
    creative_id: UUID, session: DatabaseSession, user: CurrentUser
) -> list[CreativeAnalysisResponse]:
    creative = get_authorized_creative(session, user, creative_id)
    return [
        CreativeAnalysisResponse.model_validate(item)
        for item in list_creative_analyses(session, creative.id, creative.organization_id)
    ]
