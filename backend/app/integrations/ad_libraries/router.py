from app.core.config import get_settings
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
        del platform
        if get_settings().ad_library_provider == "fake":
            return FakeAdLibraryCollector()
        return DisabledAdLibraryCollector()
