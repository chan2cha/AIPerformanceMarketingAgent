from app.db.session import SessionLocal
from app.modules.ingestion.service import enqueue_due_collection_sources
from worker.celery_app import celery_app
from worker.tasks.market_content_sync import sync_market_content_job


@celery_app.task(name="market_content_schedule.run")
def schedule_market_content_syncs() -> int:
    with SessionLocal() as session:
        job_ids = enqueue_due_collection_sources(
            session,
            lambda job_id: sync_market_content_job.delay(str(job_id)),
        )
    return len(job_ids)
