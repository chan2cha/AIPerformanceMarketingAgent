from uuid import UUID

from tests.api_helpers import ApiClient


async def create_brand_and_creative(
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
    creative_response = await client.post(
        f"/api/v1/brands/{brand['id']}/creatives",
        subject,
        {
            "ownership_type": "own",
            "media_type": "image",
            "title": f"Creative {suffix}",
            "body": "문제를 해결하는 명확한 광고 문구",
        },
    )
    assert creative_response.status_code == 201
    return organization, brand, creative_response.json()


class RecordingDispatcher:
    def __init__(self) -> None:
        self.job_ids: list[UUID] = []
        self.sync_job_ids: list[UUID] = []

    def dispatch_creative_analysis(self, job_id: UUID) -> None:
        self.job_ids.append(job_id)

    def dispatch_market_content_sync(self, job_id: UUID) -> None:
        self.sync_job_ids.append(job_id)
