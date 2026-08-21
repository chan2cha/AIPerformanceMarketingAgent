from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import openai
import pytest

from app.ai.openai_provider import OpenAIProvider
from app.ai.pricing import PricingCatalog
from app.ai.provider import (
    CreativeAnalysisRequest,
    PermanentProviderError,
    RetryableProviderError,
)
from app.ai.schemas import CreativeAnalysisOutput


def creative_request() -> CreativeAnalysisRequest:
    return CreativeAnalysisRequest(
        creative_id=uuid4(),
        title="여름 수분 크림",
        body="건조한 피부를 위한 가벼운 수분 케어. 자세히 보기.",
        source_url="https://example.com/creative",
        media_type="image",
    )


def parsed_output() -> CreativeAnalysisOutput:
    return CreativeAnalysisOutput(
        summary="수분 케어 효익을 강조하는 광고입니다.",
        hook="건조한 피부",
        offer=None,
        cta="자세히 보기",
        angle="문제 해결",
        emotional_triggers=["안도감"],
        visual_elements=["제품 이미지"],
        strengths=["효익이 명확함"],
        weaknesses=["근거가 제한적임"],
        tags=["skincare"],
        confidence=0.88,
    )


class StubResponses:
    def __init__(self, response: object | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.kwargs: dict[str, object] | None = None

    def parse(self, **kwargs: object) -> object:
        self.kwargs = kwargs
        if self.error is not None:
            raise self.error
        return self.response


class StubClient:
    def __init__(self, responses: StubResponses) -> None:
        self.responses = responses


def test_openai_provider_parses_output_and_usage_without_network() -> None:
    response = SimpleNamespace(
        output_parsed=parsed_output(),
        usage=SimpleNamespace(
            input_tokens=1000,
            output_tokens=100,
            input_tokens_details=SimpleNamespace(cached_tokens=200),
        ),
        model="gpt-5.6-luna",
        _request_id="req_test_123",
    )
    responses = StubResponses(response=response)
    provider = OpenAIProvider(
        api_key="test-only-key",
        model="gpt-5.6-luna",
        timeout_seconds=5,
        client=StubClient(responses),
        prompt="test prompt",
    )

    result = provider.analyze_creative(creative_request())

    assert result.provider == "openai"
    assert result.model == "gpt-5.6-luna"
    assert result.request_id == "req_test_123"
    assert result.usage.input_units == 1000
    assert result.usage.cached_input_units == 200
    assert result.usage.output_units == 100
    assert result.usage.unit_type == "tokens"
    assert result.output["confidence"] == 0.88
    assert responses.kwargs is not None
    assert responses.kwargs["text_format"] is CreativeAnalysisOutput
    assert responses.kwargs["store"] is False


@pytest.mark.parametrize(
    ("exception_name", "expected_error"),
    [
        ("APITimeoutError", RetryableProviderError),
        ("APIConnectionError", RetryableProviderError),
        ("RateLimitError", RetryableProviderError),
    ],
)
def test_openai_transient_errors_are_retryable(
    monkeypatch: pytest.MonkeyPatch,
    exception_name: str,
    expected_error: type[Exception],
) -> None:
    class StubSDKError(Exception):
        pass

    monkeypatch.setattr(openai, exception_name, StubSDKError)
    provider = OpenAIProvider(
        api_key="test-only-key",
        model="gpt-5.6-luna",
        timeout_seconds=5,
        client=StubClient(StubResponses(error=StubSDKError("sensitive detail"))),
        prompt="test prompt",
    )
    with pytest.raises(expected_error, match="temporarily unavailable"):
        provider.analyze_creative(creative_request())


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [(500, RetryableProviderError), (400, PermanentProviderError)],
)
def test_openai_status_error_mapping(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    expected_error: type[Exception],
) -> None:
    class StubStatusError(Exception):
        def __init__(self, code: int) -> None:
            self.status_code = code

    monkeypatch.setattr(openai, "APIStatusError", StubStatusError)
    provider = OpenAIProvider(
        api_key="test-only-key",
        model="gpt-5.6-luna",
        timeout_seconds=5,
        client=StubClient(StubResponses(error=StubStatusError(status_code))),
        prompt="test prompt",
    )
    with pytest.raises(expected_error):
        provider.analyze_creative(creative_request())


def test_openai_pricing_accounts_for_cached_input() -> None:
    cost = PricingCatalog().estimate(
        "openai",
        "gpt-5.6-luna",
        input_units=1000,
        output_units=100,
        cached_input_units=200,
    )
    assert cost == Decimal("0.000284")

    snapshot_cost = PricingCatalog().estimate(
        "openai",
        "gpt-5.6-luna-2026-07-01",
        input_units=1000,
        output_units=100,
        cached_input_units=200,
    )
    assert snapshot_cost == cost
