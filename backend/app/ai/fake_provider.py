from collections import deque
from collections.abc import Iterable

from app.ai.provider import (
    CreativeAnalysisRequest,
    PermanentProviderError,
    ProviderResult,
    ProviderUsage,
    RetryableProviderError,
)


class FakeAIProvider:
    """Deterministic, offline provider used by Phase 2 and tests."""

    name = "fake"
    model = "fake-creative-analysis-v1"

    def __init__(self, outcomes: Iterable[str] = ()) -> None:
        self._outcomes = deque(outcomes)

    def analyze_creative(self, request: CreativeAnalysisRequest) -> ProviderResult:
        outcome = self._outcomes.popleft() if self._outcomes else "success"
        if outcome == "retryable_error":
            raise RetryableProviderError("temporary fake provider failure")
        if outcome == "permanent_error":
            raise PermanentProviderError("permanent fake provider failure")

        output: dict[str, object] = {
            "summary": f"Fake analysis for creative {request.creative_id}",
            "hook": request.title or "명확한 첫 문장",
            "offer": None,
            "cta": "자세히 보기",
            "angle": "문제 해결",
            "emotional_triggers": ["호기심"],
            "visual_elements": [request.media_type],
            "strengths": ["메시지가 명확함"],
            "weaknesses": ["실제 성과 데이터 미반영"],
            "tags": ["fake", request.media_type],
            "confidence": 0.91,
        }
        if outcome == "invalid_output":
            output["confidence"] = 2

        input_units = len((request.title or "") + (request.body or "")) + 10
        return ProviderResult(
            output=output,
            provider=self.name,
            model=self.model,
            usage=ProviderUsage(
                input_units=input_units,
                output_units=120,
                unit_type="characters",
            ),
            request_id=f"fake-{request.creative_id}",
            latency_ms=5,
        )
