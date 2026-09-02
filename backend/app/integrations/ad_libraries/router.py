from app.core.config import get_settings
from app.integrations.ad_libraries.apify_meta_provider import ApifyMetaCollector
from app.integrations.ad_libraries.apify_tiktok_provider import ApifyTikTokCollector
from app.integrations.ad_libraries.fake_provider import FakeAdLibraryCollector
from app.integrations.ad_libraries.provider import (
    AdLibraryCollector,
    CollectedCreative,
    PermanentCollectorError,
)


class DisabledAdLibraryCollector:
    def collect(self, query: object) -> list[CollectedCreative]:
        del query
        raise PermanentCollectorError("광고 라이브러리 수집 provider가 설정되지 않았습니다.")


class AdLibraryCollectorRouter:
    def for_platform(self, platform: str) -> AdLibraryCollector:
        settings = get_settings()
        if settings.ad_library_provider == "fake":
            return FakeAdLibraryCollector()
        if settings.ad_library_provider == "apify":
            if settings.apify_api_token is None:
                return DisabledAdLibraryCollector()
            if platform == "meta_ad_library":
                return ApifyMetaCollector(
                    api_token=settings.apify_api_token.get_secret_value(),
                    base_url=settings.apify_base_url,
                    actor_id=settings.apify_meta_actor_id,
                    timeout_seconds=settings.apify_timeout_seconds,
                    max_items=settings.apify_meta_max_items_per_sync,
                    max_charge_usd=settings.apify_meta_max_charge_usd_per_sync,
                )
            if platform != "tiktok_creative_center":
                return DisabledAdLibraryCollector()
            return ApifyTikTokCollector(
                api_token=settings.apify_api_token.get_secret_value(),
                base_url=settings.apify_base_url,
                actor_id=settings.apify_tiktok_actor_id,
                timeout_seconds=settings.apify_timeout_seconds,
                max_items=settings.apify_max_items_per_sync,
                max_charge_usd=settings.apify_max_charge_usd_per_sync,
                period_days=settings.apify_tiktok_period_days,
            )
        return DisabledAdLibraryCollector()
