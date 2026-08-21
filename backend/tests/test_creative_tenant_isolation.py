import asyncio

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.main import app
from app.modules.brands.model import Brand
from app.modules.creatives.model import Creative
from app.modules.jobs.dispatcher import get_job_dispatcher
from app.modules.organizations.model import Organization
from tests.api_helpers import ApiClient
from tests.creative_helpers import RecordingDispatcher, create_brand_and_creative


def test_cross_tenant_creative_analysis_and_job_access_is_denied() -> None:
    dispatcher = RecordingDispatcher()
    app.dependency_overrides[get_job_dispatcher] = lambda: dispatcher

    async def scenario() -> None:
        async with ApiClient() as client:
            _org_a, brand_a, creative_a = await create_brand_and_creative(client, "user-a", "A")
            org_b, brand_b, creative_b = await create_brand_and_creative(client, "user-b", "B")
            job_response = await client.post(
                f"/api/v1/creatives/{creative_b['id']}/analyses",
                "user-b",
                {"force": False},
            )
            job_id = job_response.json()["job_id"]

            denied = [
                await client.get(f"/api/v1/brands/{brand_b['id']}/creatives", "user-a"),
                await client.post(
                    f"/api/v1/brands/{brand_b['id']}/creatives",
                    "user-a",
                    {"ownership_type": "own", "media_type": "text", "title": "Denied"},
                ),
                await client.get(f"/api/v1/creatives/{creative_b['id']}", "user-a"),
                await client.get(f"/api/v1/creatives/{creative_b['id']}/analyses", "user-a"),
                await client.post(
                    f"/api/v1/creatives/{creative_b['id']}/analyses",
                    "user-a",
                    {"force": True},
                ),
                await client.get(f"/api/v1/jobs/{job_id}", "user-a"),
                await client.get(
                    f"/api/v1/organizations/{org_b['id']}/usage", "user-a"
                ),
            ]
            assert all(response.status_code == 404 for response in denied)
            assert (
                await client.get(f"/api/v1/creatives/{creative_a['id']}", "user-a")
            ).status_code == 200
            own_list = await client.get(f"/api/v1/brands/{brand_a['id']}/creatives", "user-a")
            assert [item["id"] for item in own_list.json()] == [creative_a["id"]]

    try:
        asyncio.run(scenario())
    finally:
        app.dependency_overrides.pop(get_job_dispatcher, None)


def test_database_rejects_cross_tenant_creative_brand_reference() -> None:
    with SessionLocal() as session:
        organization_a = Organization(name="Organization A")
        organization_b = Organization(name="Organization B")
        session.add_all([organization_a, organization_b])
        session.flush()
        brand_b = Brand(organization_id=organization_b.id, name="Brand B")
        session.add(brand_b)
        session.flush()
        session.add(
            Creative(
                organization_id=organization_a.id,
                brand_id=brand_b.id,
                ownership_type="own",
                source="manual",
                media_type="text",
                title="Invalid",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
