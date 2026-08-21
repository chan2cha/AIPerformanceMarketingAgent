import asyncio

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.modules.organizations.model import Membership, Organization
from tests.api_helpers import ApiClient


def test_tenant_core_golden_path() -> None:
    async def scenario() -> None:
        async with ApiClient() as client:
            organization_response = await client.post(
                "/api/v1/organizations", "owner-a", {"name": "Brand Company"}
            )
            assert organization_response.status_code == 201
            organization = organization_response.json()

            get_organization_response = await client.get(
                f"/api/v1/organizations/{organization['id']}", "owner-a"
            )
            assert get_organization_response.status_code == 200
            assert get_organization_response.json()["name"] == "Brand Company"

            me_response = await client.get("/api/v1/me", "owner-a")
            assert me_response.status_code == 200
            assert me_response.json()["organizations"] == [
                {
                    "id": organization["id"],
                    "name": "Brand Company",
                    "role": "owner",
                }
            ]

            brand_response = await client.post(
                f"/api/v1/organizations/{organization['id']}/brands",
                "owner-a",
                {
                    "name": "Example Beauty",
                    "website": "https://example.com",
                    "industry": "beauty",
                    "description": "스킨케어 브랜드",
                    "target_customer": "20~35세 여성",
                },
            )
            assert brand_response.status_code == 201
            brand = brand_response.json()
            assert brand["organization_id"] == organization["id"]

            brands_response = await client.get(
                f"/api/v1/organizations/{organization['id']}/brands", "owner-a"
            )
            assert brands_response.status_code == 200
            assert [item["id"] for item in brands_response.json()] == [brand["id"]]

            brand_detail_response = await client.get(f"/api/v1/brands/{brand['id']}", "owner-a")
            assert brand_detail_response.status_code == 200

            brand_update_response = await client.patch(
                f"/api/v1/brands/{brand['id']}",
                "owner-a",
                {"name": "Updated Beauty", "brand_tone": "clear"},
            )
            assert brand_update_response.status_code == 200
            assert brand_update_response.json()["name"] == "Updated Beauty"

            competitor_response = await client.post(
                f"/api/v1/brands/{brand['id']}/competitors",
                "owner-a",
                {
                    "name": "Competitor A",
                    "website": "https://competitor.example",
                    "metadata": {"source": "manual"},
                },
            )
            assert competitor_response.status_code == 201
            competitor = competitor_response.json()
            assert competitor["organization_id"] == organization["id"]
            assert competitor["brand_id"] == brand["id"]
            assert competitor["metadata"] == {"source": "manual"}

            competitors_response = await client.get(
                f"/api/v1/brands/{brand['id']}/competitors", "owner-a"
            )
            assert competitors_response.status_code == 200
            assert [item["id"] for item in competitors_response.json()] == [competitor["id"]]

            delete_response = await client.delete(
                f"/api/v1/competitors/{competitor['id']}", "owner-a"
            )
            assert delete_response.status_code == 204
            assert delete_response.content == b""

            empty_competitors_response = await client.get(
                f"/api/v1/brands/{brand['id']}/competitors", "owner-a"
            )
            assert empty_competitors_response.json() == []

    asyncio.run(scenario())

    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Organization)) == 1
        membership = session.scalar(select(Membership))
        assert membership is not None
        assert membership.role == "owner"
