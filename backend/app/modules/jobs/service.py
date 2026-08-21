from datetime import UTC, datetime
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.provider import (
    AIProvider,
    CreativeAnalysisRequest,
    PermanentProviderError,
    RetryableProviderError,
)
from app.ai.schemas import PROMPT_VERSION, SCHEMA_VERSION, CreativeAnalysisOutput
from app.core.errors import ResourceNotFoundError
from app.modules.creatives.model import Creative, CreativeAnalysis
from app.modules.jobs.model import Job
from app.modules.organizations.model import Membership
from app.modules.usage.service import record_provider_usage
from app.modules.users.model import User

JOB_TYPE = "creative_analysis"


def create_analysis_job(
    session: Session,
    user: User,
    creative: Creative,
    idempotency_key: str,
) -> tuple[Job, bool]:
    existing = session.scalar(
        select(Job).where(
            Job.organization_id == creative.organization_id,
            Job.job_type == JOB_TYPE,
            Job.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing, False

    job = Job(
        organization_id=creative.organization_id,
        user_id=user.id,
        job_type=JOB_TYPE,
        target_type="creative",
        target_id=creative.id,
        idempotency_key=idempotency_key,
    )
    session.add(job)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(
            select(Job).where(
                Job.organization_id == creative.organization_id,
                Job.job_type == JOB_TYPE,
                Job.idempotency_key == idempotency_key,
            )
        )
        if existing is None:
            raise
        return existing, False
    session.refresh(job)
    return job, True


def get_authorized_job(session: Session, user: User, job_id: UUID) -> Job:
    job = session.scalar(
        select(Job)
        .join(Membership, Membership.organization_id == Job.organization_id)
        .where(Job.id == job_id, Membership.user_id == user.id)
    )
    if job is None:
        raise ResourceNotFoundError(code="JOB_NOT_FOUND", message="Job을 찾을 수 없습니다.")
    return job


def mark_job_failed(session: Session, job_id: UUID, code: str, message: str) -> None:
    job = session.get(Job, job_id)
    if job is None or job.status == "completed":
        return
    job.status = "failed"
    job.error_code = code
    job.error_message = message
    job.finished_at = datetime.now(UTC)
    session.commit()


def process_analysis_job(session: Session, job_id: UUID, provider: AIProvider) -> Job:
    job = session.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if job is None:
        raise ResourceNotFoundError(code="JOB_NOT_FOUND", message="Job을 찾을 수 없습니다.")
    if job.status in {"processing", "completed", "failed", "cancelled"}:
        return job

    creative = session.scalar(
        select(Creative).where(
            Creative.id == job.target_id,
            Creative.organization_id == job.organization_id,
        )
    )
    if creative is None:
        mark_job_failed(
            session, job.id, "CREATIVE_NOT_FOUND", "분석 대상 Creative을 찾을 수 없습니다."
        )
        return job

    job.status = "processing"
    job.progress = 10
    job.attempts += 1
    job.error_code = None
    job.error_message = None
    job.started_at = job.started_at or datetime.now(UTC)
    session.commit()

    request = CreativeAnalysisRequest(
        creative_id=creative.id,
        title=creative.title,
        body=creative.body,
        source_url=creative.source_url,
        media_type=creative.media_type,
    )
    try:
        result = provider.analyze_creative(request)
        output = CreativeAnalysisOutput.model_validate(result.output)
    except RetryableProviderError:
        job.status = "queued"
        job.progress = 0
        job.error_code = "AI_PROVIDER_RETRYABLE"
        job.error_message = "AI provider가 일시적으로 응답하지 않았습니다."
        session.commit()
        raise
    except PermanentProviderError:
        mark_job_failed(
            session,
            job.id,
            "AI_PROVIDER_ERROR",
            "AI provider 요청을 처리할 수 없습니다.",
        )
        return job
    except ValidationError:
        mark_job_failed(
            session,
            job.id,
            "AI_SCHEMA_INVALID",
            "AI 분석 결과가 유효한 schema와 일치하지 않습니다.",
        )
        return job

    existing_analysis = session.scalar(
        select(CreativeAnalysis).where(CreativeAnalysis.job_id == job.id)
    )
    if existing_analysis is None:
        session.execute(
            update(CreativeAnalysis)
            .where(
                CreativeAnalysis.creative_id == creative.id,
                CreativeAnalysis.organization_id == job.organization_id,
                CreativeAnalysis.status == "completed",
            )
            .values(status="superseded")
        )
        analysis = CreativeAnalysis(
            organization_id=job.organization_id,
            creative_id=creative.id,
            job_id=job.id,
            status="completed",
            **output.model_dump(),
            provider=result.provider,
            model=result.model,
            prompt_version=PROMPT_VERSION,
            schema_version=SCHEMA_VERSION,
            raw_result=output.model_dump(mode="json"),
        )
        session.add(analysis)

    record_provider_usage(
        session,
        organization_id=job.organization_id,
        user_id=job.user_id,
        job_id=job.id,
        result=result,
    )
    job.status = "completed"
    job.progress = 100
    job.error_code = None
    job.error_message = None
    job.finished_at = datetime.now(UTC)
    session.commit()
    session.refresh(job)
    return job
