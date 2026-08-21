import asyncio
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.modules.brands.model import Brand
from app.modules.competitors.model import Competitor
from app.modules.organizations.model import Organization
from tests.api_helpers import ApiClient


async def create_tenant_resources(
    client: ApiClient, subject: str, suffix: str
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    organization_response = await client.post(
        "/api/v1/organizations", subject, {"name": f"Organization {suffix}"}
    )
    assert organization_response.status_code == 201
    organization = organization_response.json()

    brand_response = await client.post(
        f"/api/v1/organizations/{organization['id']}/brands",
        subject,
        {"name": f"Brand {suffix}"},
    )
    assert brand_response.status_code == 201
    brand = brand_response.json()

    competitor_response = await client.post(
        f"/api/v1/brands/{brand['id']}/competitors",
        subject,
        {"name": f"Competitor {suffix}"},
    )
    assert competitor_response.status_code == 201
    return organization, brand, competitor_response.json()


def test_cross_tenant_reads_and_mutations_are_denied() -> None:
    async def scenario() -> None:
        async with ApiClient() as client:
            organization_a, brand_a, _competitor_a = await create_tenant_resources(
                client, "user-a", "A"
            )
            organization_b, brand_b, competitor_b = await create_tenant_resources(
                client, "user-b", "B"
            )

            denied_requests = [
                await client.get(f"/api/v1/organizations/{organization_b['id']}", "user-a"),
                await client.get(f"/api/v1/organizations/{organization_b['id']}/brands", "user-a"),
                await client.post(
                    f"/api/v1/organizations/{organization_b['id']}/brands",
                    "user-a",
                    {"name": "Unauthorized Brand"},
                ),
                await client.get(f"/api/v1/brands/{brand_b['id']}", "user-a"),
                await client.patch(
                    f"/api/v1/brands/{brand_b['id']}",
                    "user-a",
                    {"name": "Unauthorized Update"},
                ),
                await client.get(f"/api/v1/brands/{brand_b['id']}/competitors", "user-a"),
                await client.post(
                    f"/api/v1/brands/{brand_b['id']}/competitors",
                    "user-a",
                    {"name": "Unauthorized Competitor"},
                ),
                await client.delete(f"/api/v1/competitors/{competitor_b['id']}", "user-a"),
            ]

            assert all(response.status_code == 404 for response in denied_requests)

            own_brand_response = await client.get(f"/api/v1/brands/{brand_a['id']}", "user-a")
            assert own_brand_response.status_code == 200

            untouched_brand_response = await client.get(f"/api/v1/brands/{brand_b['id']}", "user-b")
            assert untouched_brand_response.status_code == 200
            assert untouched_brand_response.json()["name"] == "Brand B"

            untouched_competitors_response = await client.get(
                f"/api/v1/brands/{brand_b['id']}/competitors", "user-b"
            )
            assert [item["id"] for item in untouched_competitors_response.json()] == [
                competitor_b["id"]
            ]

            me_a_response = await client.get("/api/v1/me", "user-a")
            assert [item["id"] for item in me_a_response.json()["organizations"]] == [
                organization_a["id"]
            ]

    asyncio.run(scenario())


def test_database_rejects_cross_tenant_competitor_reference() -> None:
    with SessionLocal() as session:
        organization_a = Organization(name="Organization A")
        organization_b = Organization(name="Organization B")
        session.add_all([organization_a, organization_b])
        session.flush()

        brand_b = Brand(organization_id=organization_b.id, name="Brand B")
        session.add(brand_b)
        session.flush()

        session.add(
            Competitor(
                id=uuid4(),
                organization_id=organization_a.id,
                brand_id=brand_b.id,
                name="Invalid cross-tenant competitor",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
