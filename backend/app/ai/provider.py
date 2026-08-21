from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreativeAnalysisRequest:
    creative_id: UUID
    title: str | None
    body: str | None
    source_url: str | None
    media_type: str


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    input_units: int
    output_units: int
    unit_type: str
    cached_input_units: int = 0


@dataclass(frozen=True, slots=True)
class ProviderResult:
    output: dict[str, Any]
    provider: str
    model: str
    usage: ProviderUsage
    request_id: str | None
    latency_ms: int


class ProviderError(Exception):
    code = "AI_PROVIDER_ERROR"


class RetryableProviderError(ProviderError):
    code = "AI_PROVIDER_RETRYABLE"


class PermanentProviderError(ProviderError):
    pass


class AIProvider(Protocol):
    def analyze_creative(self, request: CreativeAnalysisRequest) -> ProviderResult: ...
