import asyncio
from uuid import UUID

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.integrations.ad_libraries.fake_provider import FakeAdLibraryCollector
from app.integrations.ad_libraries.provider import CollectedCreative, PermanentCollectorError
from app.main import app
from app.modules.creatives.model import Creative
from app.modules.ingestion.model import CollectionSource
from app.modules.ingestion.service import enqueue_due_collection_sources, process_collection_job
from app.modules.jobs.dispatcher import get_job_dispatcher
from app.modules.jobs.model import Job
from tests.api_helpers import ApiClient
from tests.creative_helpers import RecordingDispatcher


class UnavailableCollector:
    def collect(self, query: object) -> list[CollectedCreative]:
        del query
        raise PermanentCollectorError("unsupported source")


async def create_brand_and_competitor(
    client: ApiClient, subject: str, suffix: str
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    organization_response = await client.post(
        "/api/v1/organizations", subject, {"name": f"Organization {suffix}"}
    )
    organization = organization_response.json()
    brand_response = await client.post(
        f"/api/v1/organizations/{organization['id']}/brands",
        subject,
        {"name": f"Brand {suffix}", "industry": "beauty"},
    )
    brand = brand_response.json()
    competitor_response = await client.post(
        f"/api/v1/brands/{brand['id']}/competitors",
        subject,
        {
            "name": f"Competitor {suffix}",
            "website": "https://competitor.example",
            "meta_page_id": f"meta-{suffix}",
            "tiktok_url": "https://www.tiktok.com/@competitor",
        },
    )
    assert competitor_response.status_code == 201
    return organization, brand, competitor_response.json()


def test_collection_sync_creates_deduplicated_creative_and_analysis_job() -> None:
    dispatcher = RecordingDispatcher()
    app.dependency_overrides[get_job_dispatcher] = lambda: dispatcher

    async def scenario() -> tuple[UUID, UUID, UUID]:
        async with ApiClient() as client:
            _organization, brand, competitor = await create_brand_and_competitor(
                client, "owner-a", "VN"
            )
            source_response = await client.post(
                f"/api/v1/brands/{brand['id']}/collection-sources",
                "owner-a",
                {
                    "platform": "meta_ad_library",
                    "scope": "competitor",
                    "competitor_id": competitor["id"],
                    "external_identifier": "meta-VN",
                    "country_code": "VN",
                    "language_code": "vi",
                },
            )
            assert source_response.status_code == 201
            source = source_response.json()
            sync_response = await client.post(
                f"/api/v1/collection-sources/{source['id']}/sync",
                "owner-a",
                {"analyze_new_creatives": True},
                {"Idempotency-Key": "vn-daily-sync"},
            )
            assert sync_response.status_code == 202
            sync_job_id = UUID(sync_response.json()["job_id"])
            assert dispatcher.sync_job_ids == [sync_job_id]
            return UUID(source["id"]), UUID(brand["id"]), sync_job_id

    try:
        source_id, brand_id, sync_job_id = asyncio.run(scenario())
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)

    with SessionLocal() as session:
        result = process_collection_job(
            session,
            sync_job_id,
            FakeAdLibraryCollector(),
            dispatcher.dispatch_creative_analysis,
        )
        assert result.job.status == "completed"
        assert len(result.created_creative_ids) == 1
        assert len(result.analysis_job_ids) == 1
        assert dispatcher.job_ids == list(result.analysis_job_ids)

        creative = session.scalar(
            select(Creative).where(
                Creative.brand_id == brand_id,
                Creative.source == "meta_ad_library",
            )
        )
        assert creative is not None
        assert creative.ownership_type == "competitor"
        assert creative.raw_payload["synthetic"] is True

        source = session.get(CollectionSource, source_id)
        assert source is not None
        assert source.last_sync_at is not None
        assert source.last_error_code is None

        process_collection_job(
            session,
            sync_job_id,
            FakeAdLibraryCollector(),
            dispatcher.dispatch_creative_analysis,
        )
        assert session.scalar(select(func.count()).select_from(Creative)) == 1
        assert (
            session.scalar(
                select(func.count()).select_from(Job).where(Job.job_type == "creative_analysis")
            )
            == 1
        )


def test_collection_source_rejects_cross_tenant_competitor_and_invalid_scope() -> None:
    async def scenario() -> None:
        async with ApiClient() as client:
            _organization_a, brand_a, _competitor_a = await create_brand_and_competitor(
                client, "owner-a", "A"
            )
            _organization_b, _brand_b, competitor_b = await create_brand_and_competitor(
                client, "owner-b", "B"
            )
            cross_tenant = await client.post(
                f"/api/v1/brands/{brand_a['id']}/collection-sources",
                "owner-a",
                {
                    "platform": "meta_ad_library",
                    "scope": "competitor",
                    "competitor_id": competitor_b["id"],
                    "country_code": "VN",
                },
            )
            assert cross_tenant.status_code == 404
            assert cross_tenant.json()["error"]["code"] == "COMPETITOR_NOT_FOUND"

            invalid = await client.post(
                f"/api/v1/brands/{brand_a['id']}/collection-sources",
                "owner-a",
                {
                    "platform": "tiktok_creative_center",
                    "scope": "industry",
                    "country_code": "VN",
                    "keywords": [],
                },
            )
            assert invalid.status_code == 422
            assert invalid.json()["error"]["code"] == "INVALID_REQUEST"

    asyncio.run(scenario())


def test_unavailable_collection_provider_marks_job_and_source_failed() -> None:
    dispatcher = RecordingDispatcher()
    app.dependency_overrides[get_job_dispatcher] = lambda: dispatcher

    async def scenario() -> tuple[UUID, UUID]:
        async with ApiClient() as client:
            _organization, brand, _competitor = await create_brand_and_competitor(
                client, "owner-a", "unavailable"
            )
            source_response = await client.post(
                f"/api/v1/brands/{brand['id']}/collection-sources",
                "owner-a",
                {
                    "platform": "tiktok_creative_center",
                    "scope": "industry",
                    "country_code": "VN",
                    "language_code": "vi",
                    "keywords": ["beauty"],
                },
            )
            source_id = UUID(source_response.json()["id"])
            sync_response = await client.post(
                f"/api/v1/collection-sources/{source_id}/sync",
                "owner-a",
                {"analyze_new_creatives": True},
            )
            return source_id, UUID(sync_response.json()["job_id"])

    try:
        source_id, job_id = asyncio.run(scenario())
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)

    with SessionLocal() as session:
        result = process_collection_job(
            session,
            job_id,
            UnavailableCollector(),
            dispatcher.dispatch_creative_analysis,
        )
        assert result.job.status == "failed"
        assert result.job.error_code == "COLLECTOR_UNAVAILABLE"
        source = session.get(CollectionSource, source_id)
        assert source is not None
        assert source.last_error_code == "COLLECTOR_UNAVAILABLE"


def test_scheduler_enqueues_due_active_source_once_and_skips_paused_source() -> None:
    async def create_source() -> UUID:
        async with ApiClient() as client:
            _organization, brand, competitor = await create_brand_and_competitor(
                client, "owner-a", "scheduled"
            )
            response = await client.post(
                f"/api/v1/brands/{brand['id']}/collection-sources",
                "owner-a",
                {
                    "platform": "meta_ad_library",
                    "scope": "competitor",
                    "competitor_id": competitor["id"],
                    "country_code": "VN",
                    "sync_interval_hours": 12,
                },
            )
            assert response.status_code == 201
            assert response.json()["sync_interval_hours"] == 12
            assert response.json()["next_sync_at"] is not None
            return UUID(response.json()["id"])

    source_id = asyncio.run(create_source())
    dispatcher = RecordingDispatcher()
    with SessionLocal() as session:
        first = enqueue_due_collection_sources(session, dispatcher.dispatch_market_content_sync)
        second = enqueue_due_collection_sources(session, dispatcher.dispatch_market_content_sync)
        assert len(first) == 1
        assert second == ()
        assert dispatcher.sync_job_ids == list(first)
        source = session.get(CollectionSource, source_id)
        assert source is not None
        assert source.next_sync_at is not None

    async def pause_source() -> None:
        async with ApiClient() as client:
            response = await client.patch(
                f"/api/v1/collection-sources/{source_id}",
                "owner-a",
                {"status": "paused"},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "paused"

            denied = await client.patch(
                f"/api/v1/collection-sources/{source_id}",
                "owner-b",
                {"status": "active"},
            )
            assert denied.status_code == 404

    asyncio.run(pause_source())
    with SessionLocal() as session:
        source = session.get(CollectionSource, source_id)
        assert source is not None
        source.next_sync_at = source.created_at
        session.commit()
        assert enqueue_due_collection_sources(
            session, dispatcher.dispatch_market_content_sync
        ) == ()
