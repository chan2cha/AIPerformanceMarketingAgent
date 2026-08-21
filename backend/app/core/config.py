from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://app:local-development-only@localhost:5432/performance_marketing"
    )
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    app_env: Literal["local", "test", "production"] = "local"
    auth_mode: Literal["dev", "supabase"] = "dev"
    supabase_url: str | None = None
    supabase_jwt_audience: str = "authenticated"
    ai_provider: Literal["fake", "openai"] = "fake"
    ad_library_provider: Literal["fake", "disabled"] = "fake"
    ai_job_max_retries: int = 2
    ai_job_retry_delay_seconds: int = 1
    collection_job_max_retries: int = 2
    collection_job_retry_delay_seconds: int = 5
    openai_api_key: SecretStr | None = None
    openai_model: Literal["gpt-5.6-luna"] = "gpt-5.6-luna"
    openai_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
