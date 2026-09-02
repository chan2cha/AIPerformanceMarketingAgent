from datetime import datetime
from typing import Any, Literal

import httpx
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from app.integrations.ad_libraries.provider import (
    CollectedCreative,
    CollectionQuery,
    PermanentCollectorError,
    RetryableCollectorError,
)


class ApifyTikTokAd(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    ad_id: str = Field(validation_alias=AliasChoices("adId", "id"))
    ad_title: str | None = Field(default=None, validation_alias=AliasChoices("adTitle", "title"))
    brand_name: str | None = Field(
        default=None, validation_alias=AliasChoices("brandName", "advertiserName")
    )
    industry: str | None = None
    objective: str | None = None
    country_code: str | None = Field(
        default=None, validation_alias=AliasChoices("countryCode", "region")
    )
    creative_center_url: str = Field(
        validation_alias=AliasChoices("creativeCenterUrl", "url")
    )
    ctr: float | None = None
    likes: int | None = None
    performance_score: float | None = Field(
        default=None, validation_alias=AliasChoices("performanceScore", "score")
    )
    scraped_at: datetime | None = Field(default=None, validation_alias="scrapedAt")


_AD_LIST = TypeAdapter(list[ApifyTikTokAd])


class ApifyTikTokCollector:
    """Collect Vietnam Top Ads through a contract-controlled Apify Actor."""

    def __init__(
        self,
        api_token: str,
        *,
        base_url: str = "https://api.apify.com/v2",
        actor_id: str = "khadinakbar~tiktok-ads-scraper",
        timeout_seconds: float = 120.0,
        max_items: int = 25,
        max_charge_usd: float = 1.0,
        period_days: Literal["7", "30", "180"] = "30",
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_token = api_token
        self._base_url = base_url.rstrip("/")
        self._actor_id = actor_id.replace("/", "~")
        self._timeout_seconds = timeout_seconds
        self._max_items = max_items
        self._max_charge_usd = max_charge_usd
        self._period_days = period_days
        self._http_client = http_client

    def collect(self, query: CollectionQuery) -> list[CollectedCreative]:
        if query.platform != "tiktok_creative_center":
            raise PermanentCollectorError("Apify TikTok collector는 TikTok 소스만 지원합니다.")
        search_term = self._search_term(query)
        if not search_term:
            raise PermanentCollectorError("TikTok 수집에 사용할 경쟁사명 또는 키워드가 없습니다.")

        actor_input: dict[str, Any] = {
            "period": self._period_days,
            "country": query.country_code,
            "keyword": search_term,
            "maxResults": self._max_items,
            "responseFormat": "detailed",
        }
        response = self._post(actor_input)
        try:
            payload = response.json()
            ads = _AD_LIST.validate_python(payload)
        except (ValueError, ValidationError) as error:
            raise PermanentCollectorError("Apify Actor 응답 schema가 올바르지 않습니다.") from error

        return [self._normalize(ad, query, actor_input) for ad in ads[: self._max_items]]

    def _post(self, actor_input: dict[str, Any]) -> httpx.Response:
        client = self._http_client or httpx.Client(timeout=self._timeout_seconds)
        owns_client = self._http_client is None
        try:
            response = client.post(
                f"{self._base_url}/actors/{self._actor_id}/run-sync-get-dataset-items",
                params={
                    "clean": "true",
                    "maxItems": self._max_items,
                    "maxTotalChargeUsd": self._max_charge_usd,
                },
                headers={"Authorization": f"Bearer {self._api_token}"},
                json=actor_input,
            )
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise RetryableCollectorError("Apify가 일시적으로 응답하지 않습니다.") from error
        finally:
            if owns_client:
                client.close()

        if response.status_code in {408, 409, 425, 429} or response.status_code >= 500:
            raise RetryableCollectorError("Apify Actor 실행이 일시적으로 실패했습니다.")
        if response.status_code >= 400:
            raise PermanentCollectorError("Apify 인증·과금 또는 Actor 설정을 확인해 주세요.")
        return response

    @staticmethod
    def _search_term(query: CollectionQuery) -> str:
        if query.scope == "competitor":
            return (query.competitor_name or query.external_identifier or "").strip()[:100]
        return " ".join(query.keywords).strip()[:100]

    def _normalize(
        self,
        ad: ApifyTikTokAd,
        query: CollectionQuery,
        actor_input: dict[str, Any],
    ) -> CollectedCreative:
        observed_at = ad.scraped_at
        return CollectedCreative(
            external_id=ad.ad_id,
            source_url=ad.creative_center_url,
            media_type="video",
            title=ad.brand_name or ad.ad_title,
            body=ad.ad_title,
            first_seen_at=observed_at,
            last_seen_at=observed_at,
            raw_payload={
                "provider": "apify",
                "actor_id": self._actor_id,
                "country_code": ad.country_code or query.country_code,
                "industry": ad.industry,
                "objective": ad.objective,
                "ctr": ad.ctr,
                "likes": ad.likes,
                "performance_score": ad.performance_score,
                "collection_window_days": actor_input["period"],
                "top_ads_sample": True,
            },
        )
