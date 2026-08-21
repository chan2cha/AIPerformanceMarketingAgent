from uuid import UUID

from app.ai.provider import RetryableProviderError
from app.ai.router import AIRouter
from app.ai.schemas import AI_TASK
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.modules.jobs.service import mark_job_failed, process_analysis_job
from worker.celery_app import celery_app


@celery_app.task(bind=True, name="creative_analysis.run")
def analyze_creative_job(self, job_id: str) -> None:  # type: ignore[no-untyped-def]
    settings = get_settings()
    parsed_job_id = UUID(job_id)
    with SessionLocal() as session:
        try:
            provider = AIRouter().for_task(AI_TASK)
        except RuntimeError:
            mark_job_failed(
                session,
                parsed_job_id,
                "AI_PROVIDER_CONFIGURATION_ERROR",
                "AI provider 설정이 올바르지 않습니다.",
            )
            return
        try:
            process_analysis_job(session, parsed_job_id, provider)
        except RetryableProviderError as error:
            if self.request.retries >= settings.ai_job_max_retries:
                mark_job_failed(
                    session,
                    parsed_job_id,
                    "AI_PROVIDER_RETRIES_EXHAUSTED",
                    "AI provider 재시도 한도를 초과했습니다.",
                )
                return
            raise self.retry(
                exc=error,
                countdown=settings.ai_job_retry_delay_seconds,
                max_retries=settings.ai_job_max_retries,
            )
