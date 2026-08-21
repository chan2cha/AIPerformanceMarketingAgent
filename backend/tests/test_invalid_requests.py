import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.api_helpers import ApiClient, auth_headers


def test_authentication_and_invalid_payloads() -> None:
    async def scenario() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as raw_client:
            missing_auth = await raw_client.get("/api/v1/me")
            assert missing_auth.status_code == 401
            assert missing_auth.json()["error"]["code"] == "UNAUTHORIZED"

            invalid_auth = await raw_client.get(
                "/api/v1/me", headers={"Authorization": "Bearer invalid"}
            )
            assert invalid_auth.status_code == 401

            blank_name = await raw_client.post(
                "/api/v1/organizations",
                headers=auth_headers("invalid-test-user"),
                json={"name": "   "},
            )
            assert blank_name.status_code == 422
            assert blank_name.json()["error"]["code"] == "INVALID_REQUEST"

        async with ApiClient() as client:
            organization_response = await client.post(
                "/api/v1/organizations", "invalid-test-user", {"name": "Valid Org"}
            )
            organization = organization_response.json()

            invalid_url = await client.post(
                f"/api/v1/organizations/{organization['id']}/brands",
                "invalid-test-user",
                {"name": "Brand", "website": "not-a-url"},
            )
            assert invalid_url.status_code == 422

            brand_response = await client.post(
                f"/api/v1/organizations/{organization['id']}/brands",
                "invalid-test-user",
                {"name": "Valid Brand"},
            )
            brand = brand_response.json()

            null_name = await client.patch(
                f"/api/v1/brands/{brand['id']}", "invalid-test-user", {"name": None}
            )
            assert null_name.status_code == 422

            invalid_uuid = await client.get("/api/v1/brands/not-a-uuid", "invalid-test-user")
            assert invalid_uuid.status_code == 422

            invalid_period = await client.get(
                f"/api/v1/organizations/{organization['id']}/usage"
                "?from=2026-08-11T00:00:00Z&to=2026-08-10T00:00:00Z",
                "invalid-test-user",
            )
            assert invalid_period.status_code == 422
            assert invalid_period.json()["error"]["code"] == "INVALID_USAGE_PERIOD"

    asyncio.run(scenario())
