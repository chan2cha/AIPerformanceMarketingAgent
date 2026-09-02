import os
from uuid import uuid4

import httpx
import pytest

from app.core.config import get_settings
from app.integrations.ad_libraries.apify_tiktok_provider import ApifyTikTokCollector
from app.integrations.ad_libraries.provider import (
    CollectionQuery,
    PermanentCollectorError,
    RetryableCollectorError,
)
from app.integrations.ad_libraries.router import (
    AdLibraryCollectorRouter,
    DisabledAdLibraryCollector,
)


def query(*, scope: str = "competitor") -> CollectionQuery:
    return CollectionQuery(
        source_id=uuid4(),
        platform="tiktok_creative_center",
        scope=scope,
        country_code="VN",
        language_code="vi",
        competitor_id=uuid4() if scope == "competitor" else None,
        competitor_name="Cocoon Vietnam" if scope == "competitor" else None,
        external_identifier="@cocoonvietnam" if scope == "competitor" else None,
        keywords=() if scope == "competitor" else ("kem chống nắng", "skincare"),
    )


def test_apify_collector_builds_bounded_vietnam_request_and_normalizes_ads() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith(
            "/actors/khadinakbar~tiktok-ads-scraper/run-sync-get-dataset-items"
        )
        assert request.headers["authorization"] == "Bearer secret-token"
        assert request.url.params["maxItems"] == "12"
        assert request.url.params["maxTotalChargeUsd"] == "0.75"
        body = __import__("json").loads(request.content)
        assert body == {
            "period": "30",
            "country": "VN",
            "keyword": "Cocoon Vietnam",
            "maxResults": 12,
            "responseFormat": "detailed",
        }
        return httpx.Response(
            200,
            json=[
                {
                    "type": "ad",
                    "adId": "7651891505322672144",
                    "adTitle": "Da dịu mát suốt mùa hè",
                    "brandName": "Cocoon Vietnam",
                    "industry": "Beauty & Personal Care",
                    "objective": "Conversions",
                    "countryCode": "VN",
                    "creativeCenterUrl": "https://ads.tiktok.com/business/creativecenter/topads/7651891505322672144/pc/en",
                    "ctr": 0.73,
                    "likes": 1240,
                    "performanceScore": 88,
                    "scrapedAt": "2026-08-24T04:30:00Z",
                    "videoUrl": "https://temporary.example/video.mp4",
                }
            ],
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    collector = ApifyTikTokCollector(
        "secret-token",
        max_items=12,
        max_charge_usd=0.75,
        http_client=client,
    )
    result = collector.collect(query())

    assert len(result) == 1
    assert result[0].external_id == "7651891505322672144"
    assert result[0].media_type == "video"
    assert result[0].title == "Cocoon Vietnam"
    assert result[0].raw_payload["provider"] == "apify"
    assert result[0].raw_payload["top_ads_sample"] is True
    assert "videoUrl" not in result[0].raw_payload
    client.close()


def test_apify_collector_uses_industry_keywords() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = __import__("json").loads(request.content)
        assert body["keyword"] == "kem chống nắng skincare"
        return httpx.Response(200, json=[])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert ApifyTikTokCollector("token", http_client=client).collect(query(scope="industry")) == []
    client.close()


def test_apify_collector_accepts_live_snake_case_response() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json=[
                    {
                        "ad_id": "7663707705303826452",
                        "ad_title": "Vietnam live schema",
                        "brand_name": "Larita",
                        "country_code": "VN",
                        "creative_center_url": (
                            "https://ads.tiktok.com/business/creativecenter/"
                            "topads/7663707705303826452/pc/en"
                        ),
                        "performance_score": 72,
                    }
                ],
            )
        )
    )

    result = ApifyTikTokCollector("token", http_client=client).collect(query())

    assert result[0].external_id == "7663707705303826452"
    assert result[0].title == "Larita"
    assert result[0].raw_payload["performance_score"] == 72
    client.close()


@pytest.mark.parametrize("status_code", [408, 429, 500])
def test_apify_collector_maps_temporary_failures(status_code: int) -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(status_code))
    )
    with pytest.raises(RetryableCollectorError):
        ApifyTikTokCollector("token", http_client=client).collect(query())
    client.close()


def test_apify_collector_rejects_invalid_response_schema() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={"data": []}))
    )
    with pytest.raises(PermanentCollectorError):
        ApifyTikTokCollector("token", http_client=client).collect(query())
    client.close()


def test_apify_router_stays_disabled_without_worker_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AD_LIBRARY_PROVIDER", "apify")
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    get_settings.cache_clear()
    try:
        assert isinstance(
            AdLibraryCollectorRouter().for_platform("tiktok_creative_center"),
            DisabledAdLibraryCollector,
        )
    finally:
        get_settings.cache_clear()


@pytest.mark.apify_smoke
def test_apify_vietnam_tiktok_smoke() -> None:
    if os.environ.get("RUN_APIFY_SMOKE") != "1":
        pytest.skip("Set RUN_APIFY_SMOKE=1 to allow a billable Apify Actor run.")
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        pytest.skip("APIFY_API_TOKEN is required for the billable smoke test.")

    result = ApifyTikTokCollector(token, max_items=1, max_charge_usd=0.10).collect(
        query(scope="industry")
    )
    assert len(result) >= 1
    assert result[0].source_url.startswith("https://ads.tiktok.com/")
