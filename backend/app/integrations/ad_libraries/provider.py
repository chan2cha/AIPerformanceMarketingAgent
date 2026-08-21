from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


class RetryableCollectorError(Exception):
    """A temporary source failure that may succeed on retry."""


class PermanentCollectorError(Exception):
    """A source request that cannot succeed without configuration changes."""


@dataclass(frozen=True)
class CollectionQuery:
    source_id: UUID
    platform: str
    scope: str
    country_code: str
    language_code: str | None
    competitor_id: UUID | None
    competitor_name: str | None
    external_identifier: str | None
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class CollectedCreative:
    external_id: str
    source_url: str
    media_type: str
    title: str | None = None
    body: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


class AdLibraryCollector(Protocol):
    def collect(self, query: CollectionQuery) -> list[CollectedCreative]: ...
