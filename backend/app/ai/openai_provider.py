import json
from time import monotonic
from typing import Any, Protocol

import openai
from openai import OpenAI

from app.ai.prompts import load_creative_analysis_prompt
from app.ai.provider import (
    CreativeAnalysisRequest,
    PermanentProviderError,
    ProviderResult,
    ProviderUsage,
    RetryableProviderError,
)
from app.ai.schemas import CreativeAnalysisOutput


class ResponsesClient(Protocol):
    def parse(self, **kwargs: Any) -> Any: ...


class OpenAIClient(Protocol):
    responses: ResponsesClient


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        client: OpenAIClient | None = None,
        prompt: str | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.model = model
        self._client = client or OpenAI(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=0,
        )
        self._prompt = prompt or load_creative_analysis_prompt()

    def analyze_creative(self, request: CreativeAnalysisRequest) -> ProviderResult:
        started_at = monotonic()
        try:
            response = self._client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": self._prompt},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "creative_id": str(request.creative_id),
                                "title": request.title,
                                "body": request.body,
                                "source_url": request.source_url,
                                "media_type": request.media_type,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                text_format=CreativeAnalysisOutput,
                store=False,
            )
        except (openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError) as error:
            raise RetryableProviderError("OpenAI is temporarily unavailable") from error
        except openai.APIStatusError as error:
            if error.status_code >= 500:
                raise RetryableProviderError("OpenAI server error") from error
            raise PermanentProviderError("OpenAI rejected the request") from error
        except openai.APIError as error:
            raise PermanentProviderError("OpenAI request failed") from error

        output = response.output_parsed
        if output is None:
            raise PermanentProviderError("OpenAI returned no structured output")

        usage = response.usage
        input_tokens = int(usage.input_tokens) if usage is not None else 0
        output_tokens = int(usage.output_tokens) if usage is not None else 0
        cached_tokens = 0
        input_details = getattr(usage, "input_tokens_details", None)
        if input_details is not None:
            cached_tokens = int(input_details.cached_tokens or 0)
        cached_tokens = min(input_tokens, max(0, cached_tokens))

        return ProviderResult(
            output=output.model_dump(mode="json"),
            provider=self.name,
            model=response.model or self.model,
            usage=ProviderUsage(
                input_units=input_tokens,
                output_units=output_tokens,
                unit_type="tokens",
                cached_input_units=cached_tokens,
            ),
            request_id=getattr(response, "_request_id", None),
            latency_ms=max(0, round((monotonic() - started_at) * 1000)),
        )
