import json
from uuid import uuid4

import httpx
import pytest

from app.integrations.ad_libraries.apify_meta_provider import ApifyMetaCollector
from app.integrations.ad_libraries.provider import (
    CollectionQuery,
    PermanentCollectorError,
    RetryableCollectorError,
)


def query(*, scope: str = "competitor") -> CollectionQuery:
    return CollectionQuery(
        source_id=uuid4(),
        platform="meta_ad_library",
        scope=scope,
        country_code="VN",
        language_code="vi",
        competitor_id=uuid4() if scope == "competitor" else None,
        competitor_name="Cocoon Vietnam" if scope == "competitor" else None,
        external_identifier=None,
        keywords=() if scope == "competitor" else ("kem chống nắng", "skincare"),
    )


def test_meta_collector_builds_bounded_vietnam_request_and_normalizes_ads() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith(
            "/actors/apify~facebook-ads-scraper/run-sync-get-dataset-items"
        )
        assert request.headers["authorization"] == "Bearer secret-token"
        assert request.url.params["maxItems"] == "12"
        assert request.url.params["maxTotalChargeUsd"] == "0.75"
        body = json.loads(request.content)
        assert body["resultsLimit"] == 12
        assert body["includeAboutPage"] is False
        assert body["isDetailsPerAd"] is False
        assert body["enrichWithEcommerceData"] is False
        source_url = body["startUrls"][0]["url"]
        assert "country=VN" in source_url
        assert "q=Cocoon+Vietnam" in source_url
        assert "content_languages%5B0%5D=vi" in source_url
        return httpx.Response(
            200,
            json=[
                {
                    "adArchiveId": "1181364629627816",
                    "pageId": "117696581735620",
                    "pageName": "Cocoon Vietnam",
                    "isActive": True,
                    "startDateFormatted": "2026-08-20T07:00:00.000Z",
                    "publisherPlatform": ["FACEBOOK", "INSTAGRAM"],
                    "snapshot": {
                        "body": {"text": "Da dịu mát suốt mùa hè"},
                        "title": "Chống nắng thuần chay",
                        "videos": [{"videoHdUrl": "https://temporary.example/video.mp4"}],
                    },
                }
            ],
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = ApifyMetaCollector(
        "secret-token", max_items=12, max_charge_usd=0.75, http_client=client
    ).collect(query())

    assert len(result) == 1
    assert result[0].external_id == "1181364629627816"
    assert result[0].source_url.endswith("?id=1181364629627816")
    assert result[0].media_type == "video"
    assert result[0].title == "Chống nắng thuần chay"
    assert result[0].body == "Da dịu mát suốt mùa hè"
    assert result[0].raw_payload["provider"] == "apify"
    assert "snapshot" not in result[0].raw_payload
    client.close()


def test_meta_collector_uses_industry_keywords() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        source_url = json.loads(request.content)["startUrls"][0]["url"]
        assert "q=kem+ch%E1%BB%91ng+n%E1%BA%AFng+skincare" in source_url
        return httpx.Response(200, json=[])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert ApifyMetaCollector("token", http_client=client).collect(query(scope="industry")) == []
    client.close()


@pytest.mark.parametrize("status_code", [408, 429, 500])
def test_meta_collector_maps_temporary_failures(status_code: int) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(status_code))
    )
    with pytest.raises(RetryableCollectorError):
        ApifyMetaCollector("token", http_client=client).collect(query())
    client.close()


def test_meta_collector_rejects_invalid_response_schema() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={"data": []}))
    )
    with pytest.raises(PermanentCollectorError):
        ApifyMetaCollector("token", http_client=client).collect(query())
    client.close()
