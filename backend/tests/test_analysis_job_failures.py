import asyncio
from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.ai.fake_provider import FakeAIProvider
from app.ai.provider import RetryableProviderError
from app.db.session import SessionLocal
from app.main import app
from app.modules.creatives.model import CreativeAnalysis
from app.modules.jobs.dispatcher import get_job_dispatcher
from app.modules.jobs.model import Job
from app.modules.jobs.service import process_analysis_job
from app.modules.usage.model import ApiUsage
from tests.api_helpers import ApiClient
from tests.creative_helpers import RecordingDispatcher, create_brand_and_creative


def create_queued_job() -> UUID:
    dispatcher = RecordingDispatcher()
    app.dependency_overrides[get_job_dispatcher] = lambda: dispatcher

    async def scenario() -> UUID:
        async with ApiClient() as client:
            _organization, _brand, creative = await create_brand_and_creative(
                client, "owner-a", "failure"
            )
            response = await client.post(
                f"/api/v1/creatives/{creative['id']}/analyses",
                "owner-a",
                {"force": True},
            )
            assert response.status_code == 202
            return UUID(response.json()["job_id"])

    try:
        return asyncio.run(scenario())
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)


def test_retryable_provider_error_can_retry_without_duplicate_rows() -> None:
    job_id = create_queued_job()
    provider = FakeAIProvider(["retryable_error", "success"])
    with SessionLocal() as session:
        with pytest.raises(RetryableProviderError):
            process_analysis_job(session, job_id, provider)
        job = session.get(Job, job_id)
        assert job is not None
        assert job.status == "queued"
        assert job.attempts == 1
        assert job.error_code == "AI_PROVIDER_RETRYABLE"

        process_analysis_job(session, job_id, provider)
        session.expire_all()
        job = session.get(Job, job_id)
        assert job is not None
        assert job.status == "completed"
        assert job.attempts == 2
        assert session.scalar(select(func.count()).select_from(CreativeAnalysis)) == 1
        assert session.scalar(select(func.count()).select_from(ApiUsage)) == 1

        process_analysis_job(session, job_id, provider)
        assert session.scalar(select(func.count()).select_from(CreativeAnalysis)) == 1
        assert session.scalar(select(func.count()).select_from(ApiUsage)) == 1


@pytest.mark.parametrize(
    ("outcome", "expected_code"),
    [("permanent_error", "AI_PROVIDER_ERROR"), ("invalid_output", "AI_SCHEMA_INVALID")],
)
def test_provider_and_schema_failures_mark_job_failed(outcome: str, expected_code: str) -> None:
    job_id = create_queued_job()
    with SessionLocal() as session:
        process_analysis_job(session, job_id, FakeAIProvider([outcome]))
        session.expire_all()
        job = session.get(Job, job_id)
        assert job is not None
        assert job.status == "failed"
        assert job.error_code == expected_code
        assert job.finished_at is not None
        assert session.scalar(select(func.count()).select_from(CreativeAnalysis)) == 0
        assert session.scalar(select(func.count()).select_from(ApiUsage)) == 0


def test_provider_error_detail_is_not_persisted() -> None:
    class SensitiveProvider:
        def analyze_creative(self, _request: object) -> object:
            from app.ai.provider import PermanentProviderError

            raise PermanentProviderError("sk-sensitive-secret raw provider response")

    job_id = create_queued_job()
    with SessionLocal() as session:
        process_analysis_job(session, job_id, SensitiveProvider())  # type: ignore[arg-type]
        session.expire_all()
        job = session.get(Job, job_id)
        assert job is not None
        assert job.status == "failed"
        assert "sensitive" not in (job.error_message or "")
        assert "sk-" not in (job.error_message or "")
