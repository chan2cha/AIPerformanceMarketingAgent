from uuid import UUID

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.integrations.ad_libraries.provider import RetryableCollectorError
from app.integrations.ad_libraries.router import AdLibraryCollectorRouter
from app.modules.ingestion.model import CollectionSource
from app.modules.ingestion.service import process_collection_job
from app.modules.jobs.model import Job
from app.modules.jobs.service import mark_job_failed
from worker.celery_app import celery_app
from worker.tasks.creative_analysis import analyze_creative_job


@celery_app.task(bind=True, name="market_content_sync.run")
def sync_market_content_job(self, job_id: str) -> None:  # type: ignore[no-untyped-def]
    settings = get_settings()
    parsed_job_id = UUID(job_id)
    with SessionLocal() as session:
        job = session.get(Job, parsed_job_id)
        source = session.get(CollectionSource, job.target_id) if job else None
        if job is None or source is None:
            mark_job_failed(
                session,
                parsed_job_id,
                "COLLECTION_SOURCE_NOT_FOUND",
                "수집 소스를 찾을 수 없습니다.",
            )
            return
        collector = AdLibraryCollectorRouter().for_platform(source.platform)
        try:
            process_collection_job(
                session,
                parsed_job_id,
                collector,
                lambda analysis_job_id: analyze_creative_job.delay(str(analysis_job_id)),
            )
        except RetryableCollectorError as error:
            if self.request.retries >= settings.collection_job_max_retries:
                mark_job_failed(
                    session,
                    parsed_job_id,
                    "COLLECTOR_RETRIES_EXHAUSTED",
                    "광고 데이터 수집 재시도 한도를 초과했습니다.",
                )
                return
            raise self.retry(
                exc=error,
                countdown=settings.collection_job_retry_delay_seconds,
                max_retries=settings.collection_job_max_retries,
            )
