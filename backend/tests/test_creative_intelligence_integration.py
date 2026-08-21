import asyncio
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.main import app
from app.modules.creatives.model import CreativeAnalysis
from app.modules.jobs.dispatcher import get_job_dispatcher
from app.modules.jobs.model import Job
from app.modules.usage.model import ApiUsage
from tests.api_helpers import ApiClient
from tests.creative_helpers import RecordingDispatcher, create_brand_and_creative
from worker.tasks.creative_analysis import analyze_creative_job


def test_creative_analysis_golden_path_through_worker_task() -> None:
    dispatcher = RecordingDispatcher()
    app.dependency_overrides[get_job_dispatcher] = lambda: dispatcher

    async def scenario() -> tuple[dict[str, object], dict[str, object], UUID]:
        async with ApiClient() as client:
            organization, brand, creative = await create_brand_and_creative(
                client, "owner-a", "A"
            )
            analysis_response = await client.post(
                f"/api/v1/creatives/{creative['id']}/analyses",
                "owner-a",
                {"force": False},
            )
            assert analysis_response.status_code == 202
            assert analysis_response.json()["status"] == "queued"
            job_id = UUID(analysis_response.json()["job_id"])
            assert dispatcher.job_ids == [job_id]

            queued_response = await client.get(f"/api/v1/jobs/{job_id}", "owner-a")
            assert queued_response.json()["status"] == "queued"

            analyze_creative_job.run(str(job_id))

            completed_response = await client.get(f"/api/v1/jobs/{job_id}", "owner-a")
            assert completed_response.status_code == 200
            assert completed_response.json()["status"] == "completed"
            assert completed_response.json()["progress"] == 100
            assert completed_response.json()["attempts"] == 1

            detail_response = await client.get(f"/api/v1/creatives/{creative['id']}", "owner-a")
            assert detail_response.status_code == 200
            analyses = detail_response.json()["analyses"]
            assert len(analyses) == 1
            assert analyses[0]["provider"] == "fake"
            assert analyses[0]["prompt_version"] == "creative-analysis-v2"

            analyzed_filter = await client.get(
                f"/api/v1/brands/{brand['id']}/creatives?analyzed=true", "owner-a"
            )
            assert [item["id"] for item in analyzed_filter.json()] == [creative["id"]]
            usage_response = await client.get(
                f"/api/v1/organizations/{organization['id']}/usage", "owner-a"
            )
            assert usage_response.status_code == 200
            assert usage_response.json()["calls"] == 1
            assert float(usage_response.json()["estimated_cost_usd"]) > 0
            assert usage_response.json()["by_task"][0]["task"] == "creative_analysis"
            return brand, creative, job_id

    try:
        _brand, creative, job_id = asyncio.run(scenario())
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)

    with SessionLocal() as session:
        analysis = session.scalar(select(CreativeAnalysis).where(CreativeAnalysis.job_id == job_id))
        usage = session.scalar(select(ApiUsage).where(ApiUsage.job_id == job_id))
        assert analysis is not None
        assert analysis.creative_id == UUID(str(creative["id"]))
        assert usage is not None
        assert usage.provider == "fake"
        assert usage.task == "creative_analysis"
        assert usage.input_units > 0
        assert usage.output_units == 120
        assert usage.estimated_cost_usd > Decimal("0")


def test_analysis_request_is_idempotent() -> None:
    dispatcher = RecordingDispatcher()
    app.dependency_overrides[get_job_dispatcher] = lambda: dispatcher

    async def scenario() -> None:
        async with ApiClient() as client:
            _organization, _brand, creative = await create_brand_and_creative(
                client, "owner-a", "idempotent"
            )
            headers = {"Idempotency-Key": "creative-analysis-test-key"}
            first = await client.post(
                f"/api/v1/creatives/{creative['id']}/analyses",
                "owner-a",
                {"force": False},
                headers,
            )
            second = await client.post(
                f"/api/v1/creatives/{creative['id']}/analyses",
                "owner-a",
                {"force": False},
                headers,
            )
            assert first.status_code == second.status_code == 202
            assert first.json()["job_id"] == second.json()["job_id"]
            assert len(dispatcher.job_ids) == 1

    try:
        asyncio.run(scenario())
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)

    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Job)) == 1


def test_invalid_creative_payload_is_rejected() -> None:
    async def scenario() -> None:
        async with ApiClient() as client:
            organization_response = await client.post(
                "/api/v1/organizations", "owner-a", {"name": "Organization A"}
            )
            brand_response = await client.post(
                f"/api/v1/organizations/{organization_response.json()['id']}/brands",
                "owner-a",
                {"name": "Brand A"},
            )
            response = await client.post(
                f"/api/v1/brands/{brand_response.json()['id']}/creatives",
                "owner-a",
                {"ownership_type": "competitor", "media_type": "image", "title": "Ad"},
            )
            assert response.status_code == 422
            assert response.json()["error"]["code"] == "INVALID_REQUEST"

    asyncio.run(scenario())
