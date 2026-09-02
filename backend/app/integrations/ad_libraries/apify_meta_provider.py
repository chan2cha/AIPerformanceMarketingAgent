from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from app.integrations.ad_libraries.provider import (
    CollectedCreative,
    CollectionQuery,
    PermanentCollectorError,
    RetryableCollectorError,
)


class ApifyMetaAd(BaseModel):
    model_config = ConfigDict(extra="allow")

    ad_archive_id: str = Field(
        validation_alias=AliasChoices("adArchiveId", "adArchiveID", "ad_archive_id")
    )
    page_id: str | None = Field(
        default=None, validation_alias=AliasChoices("pageId", "pageID", "page_id")
    )
    page_name: str | None = Field(
        default=None, validation_alias=AliasChoices("pageName", "page_name")
    )
    is_active: bool | None = Field(
        default=None, validation_alias=AliasChoices("isActive", "is_active")
    )
    start_date: int | float | str | None = Field(
        default=None,
        validation_alias=AliasChoices("startDateFormatted", "startDate", "start_date"),
    )
    end_date: int | float | str | None = Field(
        default=None,
        validation_alias=AliasChoices("endDateFormatted", "endDate", "end_date"),
    )
    publisher_platforms: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("publisherPlatform", "publisher_platform", "platforms"),
    )


_AD_LIST = TypeAdapter(list[ApifyMetaAd])


class ApifyMetaCollector:
    """Collect public Meta Ad Library results through Apify's maintained Actor."""

    def __init__(
        self,
        api_token: str,
        *,
        base_url: str = "https://api.apify.com/v2",
        actor_id: str = "apify~facebook-ads-scraper",
        timeout_seconds: float = 120.0,
        max_items: int = 25,
        max_charge_usd: float = 1.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_token = api_token
        self._base_url = base_url.rstrip("/")
        self._actor_id = actor_id.replace("/", "~")
        self._timeout_seconds = timeout_seconds
        self._max_items = max_items
        self._max_charge_usd = max_charge_usd
        self._http_client = http_client

    def collect(self, query: CollectionQuery) -> list[CollectedCreative]:
        if query.platform != "meta_ad_library":
            raise PermanentCollectorError("Apify Meta collector는 Meta 소스만 지원합니다.")

        library_url = self._library_url(query)
        actor_input: dict[str, Any] = {
            "startUrls": [{"url": library_url}],
            "resultsLimit": self._max_items,
            "onlyTotal": False,
            "includeAboutPage": False,
            "isDetailsPerAd": False,
            "enrichWithEcommerceData": False,
            "activeStatus": "active",
        }
        response = self._post(actor_input)
        try:
            ads = _AD_LIST.validate_python(response.json())
        except (ValueError, ValidationError) as error:
            raise PermanentCollectorError(
                "Apify Meta Actor 응답 형식이 올바르지 않습니다."
            ) from error
        return [self._normalize(ad, query) for ad in ads[: self._max_items]]

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
            raise RetryableCollectorError("Apify Meta Actor 실행이 일시적으로 실패했습니다.")
        if response.status_code >= 400:
            raise PermanentCollectorError(
                "Apify 인증, 과금 한도 또는 Meta Actor 설정을 확인해 주세요."
            )
        return response

    def _library_url(self, query: CollectionQuery) -> str:
        external_identifier = (query.external_identifier or "").strip()
        if external_identifier.startswith(("https://www.facebook.com/", "https://facebook.com/")):
            return external_identifier

        if query.scope == "competitor":
            search_term = (query.competitor_name or external_identifier).strip()
        else:
            search_term = " ".join(query.keywords).strip()
        if not search_term:
            raise PermanentCollectorError("Meta 수집에 사용할 경쟁사명 또는 키워드가 없습니다.")

        parameters: list[tuple[str, str]] = [
            ("active_status", "active"),
            ("ad_type", "all"),
            ("country", query.country_code),
            ("is_targeted_country", "false"),
            ("media_type", "all"),
            ("search_type", "keyword_unordered"),
            ("q", search_term[:100]),
        ]
        if query.language_code:
            parameters.append(("content_languages[0]", query.language_code))
        return f"https://www.facebook.com/ads/library/?{urlencode(parameters)}"

    def _normalize(self, ad: ApifyMetaAd, query: CollectionQuery) -> CollectedCreative:
        payload = ad.model_dump(mode="python")
        body = self._first_text(payload, {"body", "body_text", "adText", "adCopy"})
        headline = self._first_text(payload, {"title", "headline", "linkTitle"})
        media_type = self._media_type(payload)
        return CollectedCreative(
            external_id=ad.ad_archive_id,
            source_url=f"https://www.facebook.com/ads/library/?id={ad.ad_archive_id}",
            media_type=media_type,
            title=headline or ad.page_name,
            body=body,
            first_seen_at=self._as_datetime(ad.start_date),
            last_seen_at=self._as_datetime(ad.end_date) or datetime.now(UTC),
            raw_payload={
                "provider": "apify",
                "actor_id": self._actor_id,
                "page_id": ad.page_id,
                "page_name": ad.page_name,
                "is_active": ad.is_active,
                "publisher_platforms": ad.publisher_platforms,
                "country_code": query.country_code,
                "public_library_data": True,
            },
        )

    @classmethod
    def _first_text(cls, value: Any, keys: set[str]) -> str | None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in keys and isinstance(child, str) and child.strip():
                    return child.strip()
                if key in keys and isinstance(child, dict):
                    nested_text = child.get("text") or child.get("value")
                    if isinstance(nested_text, str) and nested_text.strip():
                        return nested_text.strip()
            for child in value.values():
                found = cls._first_text(child, keys)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = cls._first_text(child, keys)
                if found:
                    return found
        return None

    @staticmethod
    def _media_type(payload: dict[str, Any]) -> str:
        serialized_keys = " ".join(str(key).lower() for key in _walk_keys(payload))
        if "video" in serialized_keys:
            return "video"
        if "card" in serialized_keys or "carousel" in serialized_keys:
            return "carousel"
        if "image" in serialized_keys:
            return "image"
        return "text"

    @staticmethod
    def _as_datetime(value: int | float | str | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=UTC)
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(_walk_keys(child))
    return keys
