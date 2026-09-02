from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
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
    ad_library_provider: Literal["fake", "apify", "disabled"] = "fake"
    billing_provider: Literal["fake", "stripe", "disabled"] = "fake"
    billing_enforcement_enabled: bool = False
    billing_monthly_price_usd: Decimal = Field(default=Decimal("40.00"), gt=0)
    billing_monthly_credit_usd: Decimal = Field(default=Decimal("15.00"), gt=0)
    billing_analysis_limit: int = Field(default=200, ge=1, le=10000)
    billing_collection_run_limit: int = Field(default=50, ge=1, le=10000)
    billing_brand_limit: int = Field(default=1, ge=1, le=100)
    billing_competitor_limit: int = Field(default=5, ge=1, le=1000)
    billing_analysis_reservation_usd: Decimal = Field(default=Decimal("0.05"), gt=0)
    billing_collection_reservation_usd: Decimal = Field(default=Decimal("0.25"), gt=0)
    billing_success_url: str = "http://localhost:3000/?billing=success"
    billing_cancel_url: str = "http://localhost:3000/?billing=cancelled"
    apify_configured: bool = False
    openai_configured: bool = False
    stripe_secret_key: SecretStr | None = None
    stripe_price_id: str | None = None
    stripe_webhook_secret: SecretStr | None = None
    stripe_api_base_url: str = "https://api.stripe.com/v1"
    apify_api_token: SecretStr | None = None
    apify_base_url: str = "https://api.apify.com/v2"
    apify_meta_actor_id: str = "apify~facebook-ads-scraper"
    apify_tiktok_actor_id: str = "khadinakbar~tiktok-ads-scraper"
    apify_timeout_seconds: float = Field(default=120.0, gt=0, le=300)
    apify_max_items_per_sync: int = Field(default=25, ge=1, le=100)
    apify_max_charge_usd_per_sync: float = Field(default=0.25, gt=0, le=20)
    apify_meta_max_items_per_sync: int = Field(default=25, ge=1, le=100)
    apify_meta_max_charge_usd_per_sync: float = Field(default=0.25, gt=0, le=20)
    apify_tiktok_period_days: Literal["7", "30", "180"] = "30"
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

    @model_validator(mode="after")
    def validate_production_billing(self) -> "Settings":
        if self.app_env != "production" or self.auth_mode == "dev":
            return self
        if self.billing_provider == "fake":
            raise ValueError("BILLING_PROVIDER=fake is not allowed in production")
        if self.billing_provider == "stripe":
            if not self.billing_enforcement_enabled:
                raise ValueError("Stripe production billing requires enforcement")
            if (
                not self.stripe_secret_key
                or not self.stripe_price_id
                or not self.stripe_webhook_secret
            ):
                raise ValueError("Stripe production billing secrets are incomplete")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
