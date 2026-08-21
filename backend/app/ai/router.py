from app.ai.fake_provider import FakeAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.provider import AIProvider
from app.core.config import get_settings


class AIRouter:
    def __init__(
        self,
        fake_provider: AIProvider | None = None,
        openai_provider: AIProvider | None = None,
    ) -> None:
        self._fake_provider = fake_provider or FakeAIProvider()
        self._openai_provider = openai_provider

    def for_task(self, task: str) -> AIProvider:
        settings = get_settings()
        if task != "creative_analysis":
            raise RuntimeError(f"No AI provider configured for task: {task}")
        if settings.ai_provider == "fake":
            return self._fake_provider
        if self._openai_provider is not None:
            return self._openai_provider
        if settings.openai_api_key is None:
            raise RuntimeError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
        return OpenAIProvider(
            api_key=settings.openai_api_key.get_secret_value(),
            model=settings.openai_model,
            timeout_seconds=settings.openai_timeout_seconds,
        )
