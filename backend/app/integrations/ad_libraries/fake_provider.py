from datetime import UTC, datetime
from hashlib import sha256

from app.integrations.ad_libraries.provider import CollectedCreative, CollectionQuery


class FakeAdLibraryCollector:
    """Deterministic local collector for workflow verification without network access."""

    def collect(self, query: CollectionQuery) -> list[CollectedCreative]:
        identity = query.external_identifier or query.competitor_name or "-".join(query.keywords)
        if not identity:
            return []
        digest = sha256(
            f"{query.platform}:{query.country_code}:{identity}".encode()
        ).hexdigest()[:16]
        now = datetime.now(UTC)
        label = query.competitor_name or identity
        return [
            CollectedCreative(
                external_id=f"fake-{digest}",
                source_url=f"https://example.invalid/ads/{digest}",
                media_type="video" if query.platform == "tiktok_creative_center" else "image",
                title=f"{label} 자동 수집 광고",
                body=f"{query.country_code} 시장 분석용으로 수집된 로컬 데모 광고입니다.",
                first_seen_at=now,
                last_seen_at=now,
                raw_payload={
                    "synthetic": True,
                    "platform": query.platform,
                    "country_code": query.country_code,
                },
            )
        ]
