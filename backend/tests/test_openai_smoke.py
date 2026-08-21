import os
from uuid import uuid4

import pytest

from app.ai.openai_provider import OpenAIProvider
from app.ai.provider import CreativeAnalysisRequest


@pytest.mark.openai_smoke
def test_openai_creative_analysis_smoke() -> None:
    if os.getenv("RUN_OPENAI_SMOKE") != "1":
        pytest.skip("Set RUN_OPENAI_SMOKE=1 to allow a billable OpenAI request")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.fail("OPENAI_API_KEY is required when RUN_OPENAI_SMOKE=1")

    provider = OpenAIProvider(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        timeout_seconds=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30")),
    )
    result = provider.analyze_creative(
        CreativeAnalysisRequest(
            creative_id=uuid4(),
            title="가벼운 여름 수분 크림",
            body="건조함 없이 산뜻한 수분 케어. 자세히 보기.",
            source_url=None,
            media_type="text",
        )
    )
    assert result.provider == "openai"
    assert result.usage.input_units > 0
    assert result.usage.output_units > 0
    assert result.output["summary"]
