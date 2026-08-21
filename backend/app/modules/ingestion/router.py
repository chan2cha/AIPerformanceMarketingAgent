from hashlib import sha256
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, Header, status

from app.core.errors import ServiceUnavailableError
from app.modules.auth.dependencies import CurrentUser, DatabaseSession
from app.modules.brands.repository import get_authorized_brand
from app.modules.ingestion.repository import (
    get_authorized_collection_source,
    list_brand_collection_sources,
)
from app.modules.ingestion.schemas import (
    CollectionSourceCreate,
    CollectionSourceResponse,
    CollectionSourceUpdate,
    CollectionSyncCreate,
)
from app.modules.ingestion.service import (
    create_collection_job,
    create_collection_source,
    update_collection_source,
)
from app.modules.jobs.dispatcher import JobDispatcher, get_job_dispatcher
from app.modules.jobs.schemas import JobAcceptedResponse
from app.modules.jobs.service import mark_job_failed

router = APIRouter(prefix="/api/v1", tags=["market-content-ingestion"])


@router.post(
    "/brands/{brand_id}/collection-sources",
    response_model=CollectionSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_collection_source(
    brand_id: UUID,
    payload: Annotated[CollectionSourceCreate, Body()],
    session: DatabaseSession,
    user: CurrentUser,
) -> CollectionSourceResponse:
    brand = get_authorized_brand(session, user, brand_id)
    source = create_collection_source(session, brand, payload, user.id)
    return CollectionSourceResponse.model_validate(source)


@router.get(
    "/brands/{brand_id}/collection-sources",
    response_model=list[CollectionSourceResponse],
)
def get_collection_sources(
    brand_id: UUID,
    session: DatabaseSession,
    user: CurrentUser,
) -> list[CollectionSourceResponse]:
    brand = get_authorized_brand(session, user, brand_id)
    return [
        CollectionSourceResponse.model_validate(source)
        for source in list_brand_collection_sources(session, brand.organization_id, brand.id)
    ]


@router.patch(
    "/collection-sources/{source_id}",
    response_model=CollectionSourceResponse,
)
def patch_collection_source(
    source_id: UUID,
    payload: Annotated[CollectionSourceUpdate, Body()],
    session: DatabaseSession,
    user: CurrentUser,
) -> CollectionSourceResponse:
    source = get_authorized_collection_source(session, user, source_id)
    updated = update_collection_source(
        session,
        source,
        status=payload.status,
        sync_interval_hours=payload.sync_interval_hours,
    )
    return CollectionSourceResponse.model_validate(updated)


@router.post(
    "/collection-sources/{source_id}/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_collection_sync(
    source_id: UUID,
    payload: Annotated[CollectionSyncCreate, Body()],
    session: DatabaseSession,
    user: CurrentUser,
    dispatcher: Annotated[JobDispatcher, Depends(get_job_dispatcher)],
    idempotency_key: Annotated[str | None, Header(max_length=255)] = None,
) -> JobAcceptedResponse:
    source = get_authorized_collection_source(session, user, source_id)
    requested_key = idempotency_key or str(uuid4())
    job, created = create_collection_job(
        session,
        user,
        source,
        sha256(requested_key.encode("utf-8")).hexdigest(),
        payload.analyze_new_creatives,
    )
    if created:
        try:
            dispatcher.dispatch_market_content_sync(job.id)
        except Exception as error:
            mark_job_failed(
                session,
                job.id,
                "JOB_ENQUEUE_FAILED",
                "광고 수집 Job을 queue에 등록하지 못했습니다.",
            )
            raise ServiceUnavailableError(
                code="JOB_ENQUEUE_FAILED",
                message="광고 수집 Job을 queue에 등록하지 못했습니다.",
            ) from error
    return JobAcceptedResponse(job_id=job.id, status=job.status)
