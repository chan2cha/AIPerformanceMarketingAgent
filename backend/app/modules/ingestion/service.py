from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.schemas import PROMPT_VERSION
from app.core.errors import ResourceNotFoundError
from app.integrations.ad_libraries.provider import (
    AdLibraryCollector,
    CollectionQuery,
    PermanentCollectorError,
    RetryableCollectorError,
)
from app.modules.brands.model import Brand
from app.modules.competitors.model import Competitor
from app.modules.creatives.model import Creative
from app.modules.ingestion.model import CollectionSource
from app.modules.ingestion.schemas import CollectionSourceCreate
from app.modules.jobs.model import Job
from app.modules.jobs.service import create_analysis_job, mark_job_failed
from app.modules.users.model import User

COLLECTION_JOB_TYPE = "market_content_sync"


@dataclass(frozen=True)
class CollectionSyncResult:
    job: Job
    created_creative_ids: tuple[UUID, ...]
    analysis_job_ids: tuple[UUID, ...]


def create_collection_source(
    session: Session,
    brand: Brand,
    payload: CollectionSourceCreate,
    user_id: UUID,
) -> CollectionSource:
    competitor = None
    if payload.competitor_id is not None:
        competitor = session.scalar(
            select(Competitor).where(
                Competitor.id == payload.competitor_id,
                Competitor.brand_id == brand.id,
                Competitor.organization_id == brand.organization_id,
            )
        )
        if competitor is None:
            raise ResourceNotFoundError(
                code="COMPETITOR_NOT_FOUND", message="경쟁 브랜드를 찾을 수 없습니다."
            )

    source = CollectionSource(
        organization_id=brand.organization_id,
        brand_id=brand.id,
        competitor_id=competitor.id if competitor else None,
        created_by_user_id=user_id,
        platform=payload.platform,
        scope=payload.scope,
        external_identifier=payload.external_identifier,
        country_code=payload.country_code,
        language_code=payload.language_code,
        keywords=list(dict.fromkeys(payload.keywords)),
        sync_interval_hours=payload.sync_interval_hours,
        next_sync_at=datetime.now(UTC),
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def update_collection_source(
    session: Session,
    source: CollectionSource,
    *,
    status: str | None,
    sync_interval_hours: int | None,
) -> CollectionSource:
    now = datetime.now(UTC)
    if status is not None:
        source.status = status
        if status == "active" and (source.next_sync_at is None or source.next_sync_at > now):
            source.next_sync_at = now
    if sync_interval_hours is not None:
        source.sync_interval_hours = sync_interval_hours
        if source.status == "active":
            source.next_sync_at = now + timedelta(hours=sync_interval_hours)
    session.commit()
    session.refresh(source)
    return source


def create_collection_job(
    session: Session,
    user: User | None,
    source: CollectionSource,
    requested_key: str,
    analyze_new_creatives: bool,
) -> tuple[Job, bool]:
    key_digest = sha256(requested_key.encode("utf-8")).hexdigest()
    idempotency_key = f"{source.id}:{key_digest}:analyze={analyze_new_creatives}"
    existing = session.scalar(
        select(Job).where(
            Job.organization_id == source.organization_id,
            Job.job_type == COLLECTION_JOB_TYPE,
            Job.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing, False

    job = Job(
        organization_id=source.organization_id,
        user_id=user.id if user else None,
        job_type=COLLECTION_JOB_TYPE,
        target_type="collection_source",
        target_id=source.id,
        idempotency_key=idempotency_key,
    )
    session.add(job)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(
            select(Job).where(
                Job.organization_id == source.organization_id,
                Job.job_type == COLLECTION_JOB_TYPE,
                Job.idempotency_key == idempotency_key,
            )
        )
        if existing is None:
            raise
        return existing, False
    session.refresh(job)
    return job, True


def process_collection_job(
    session: Session,
    job_id: UUID,
    collector: AdLibraryCollector,
    dispatch_analysis: Callable[[UUID], None],
) -> CollectionSyncResult:
    job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise ResourceNotFoundError(code="JOB_NOT_FOUND", message="Job을 찾을 수 없습니다.")
    if job.status in {"processing", "completed", "failed", "cancelled"}:
        return CollectionSyncResult(job, (), ())

    source = session.scalar(
        select(CollectionSource).where(
            CollectionSource.id == job.target_id,
            CollectionSource.organization_id == job.organization_id,
        )
    )
    if source is None:
        mark_job_failed(
            session, job.id, "COLLECTION_SOURCE_NOT_FOUND", "수집 소스를 찾을 수 없습니다."
        )
        return CollectionSyncResult(job, (), ())

    competitor = session.get(Competitor, source.competitor_id) if source.competitor_id else None
    job.status = "processing"
    job.progress = 10
    job.attempts += 1
    job.error_code = None
    job.started_at = job.started_at or datetime.now(UTC)
    source.last_attempt_at = datetime.now(UTC)
    auto_analyze = job.idempotency_key.endswith("analyze=True")
    job.error_message = None
    session.commit()

    query = CollectionQuery(
        source_id=source.id,
        platform=source.platform,
        scope=source.scope,
        country_code=source.country_code,
        language_code=source.language_code,
        competitor_id=source.competitor_id,
        competitor_name=competitor.name if competitor else None,
        external_identifier=source.external_identifier,
        keywords=tuple(source.keywords),
    )
    try:
        items = collector.collect(query)
    except RetryableCollectorError:
        job.status = "queued"
        job.progress = 0
        job.error_code = "COLLECTOR_RETRYABLE"
        job.error_message = "광고 데이터 소스가 일시적으로 응답하지 않았습니다."
        source.last_error_code = job.error_code
        session.commit()
        raise
    except PermanentCollectorError:
        source.last_error_code = "COLLECTOR_UNAVAILABLE"
        source.next_sync_at = datetime.now(UTC) + timedelta(hours=source.sync_interval_hours)
        mark_job_failed(
            session,
            job.id,
            "COLLECTOR_UNAVAILABLE",
            "현재 설정으로 광고 데이터를 수집할 수 없습니다.",
        )
        return CollectionSyncResult(job, (), ())

    created: list[Creative] = []
    now = datetime.now(UTC)
    for item in items:
        creative = session.scalar(
            select(Creative).where(
                Creative.organization_id == source.organization_id,
                Creative.source == source.platform,
                Creative.source_external_id == item.external_id,
            )
        )
        if creative is None:
            creative = Creative(
                organization_id=source.organization_id,
                brand_id=source.brand_id,
                competitor_id=source.competitor_id,
                ownership_type="competitor" if source.competitor_id else "market",
                source=source.platform,
                source_external_id=item.external_id,
                source_url=item.source_url,
                media_type=item.media_type,
                title=item.title,
                body=item.body,
                first_seen_at=item.first_seen_at or now,
                last_seen_at=item.last_seen_at or now,
                raw_payload=item.raw_payload,
            )
            session.add(creative)
            session.flush()
            created.append(creative)
        else:
            creative.last_seen_at = item.last_seen_at or now

    source.last_sync_at = now
    source.last_error_code = None
    source.next_sync_at = now + timedelta(hours=source.sync_interval_hours)
    job.progress = 80
    session.commit()

    analysis_job_ids: list[UUID] = []
    if auto_analyze and job.user_id is not None:
        user = session.get(User, job.user_id)
        if user is not None:
            for creative in created:
                analysis_job, was_created = create_analysis_job(
                    session,
                    user,
                    creative,
                    f"auto:{source.id}:{creative.id}:{PROMPT_VERSION}",
                )
                if was_created:
                    try:
                        dispatch_analysis(analysis_job.id)
                    except Exception:
                        mark_job_failed(
                            session,
                            analysis_job.id,
                            "JOB_ENQUEUE_FAILED",
                            "자동 분석 Job을 queue에 등록하지 못했습니다.",
                        )
                    analysis_job_ids.append(analysis_job.id)

    job.status = "completed"
    job.progress = 100
    job.error_code = None
    job.error_message = None
    job.finished_at = datetime.now(UTC)
    session.commit()
    session.refresh(job)
    return CollectionSyncResult(
        job,
        tuple(creative.id for creative in created),
        tuple(analysis_job_ids),
    )


def enqueue_due_collection_sources(
    session: Session,
    dispatch_sync: Callable[[UUID], None],
    *,
    limit: int = 100,
) -> tuple[UUID, ...]:
    now = datetime.now(UTC)
    sources = list(
        session.scalars(
            select(CollectionSource)
            .where(
                CollectionSource.status == "active",
                CollectionSource.next_sync_at.is_not(None),
                CollectionSource.next_sync_at <= now,
            )
            .order_by(CollectionSource.next_sync_at, CollectionSource.id)
            .limit(limit)
        )
    )
    job_ids: list[UUID] = []
    for source in sources:
        scheduled_for = source.next_sync_at or now
        user = session.get(User, source.created_by_user_id) if source.created_by_user_id else None
        job, created = create_collection_job(
            session,
            user,
            source,
            f"scheduled:{scheduled_for.isoformat()}",
            analyze_new_creatives=True,
        )
        source.next_sync_at = now + timedelta(hours=source.sync_interval_hours)
        if created:
            try:
                dispatch_sync(job.id)
                job_ids.append(job.id)
            except Exception:
                source.last_error_code = "JOB_ENQUEUE_FAILED"
                mark_job_failed(
                    session,
                    job.id,
                    "JOB_ENQUEUE_FAILED",
                    "정기 광고 수집 Job을 queue에 등록하지 못했습니다.",
                )
        session.commit()
    return tuple(job_ids)
