import asyncio

import pytest

from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.modules.auth.adapter import DevAuthAdapter, SupabaseAuthAdapter
from app.modules.auth.dependencies import get_auth_adapter


def test_dev_auth_adapter_is_deterministic() -> None:
    identity = asyncio.run(DevAuthAdapter().authenticate("dev:user-a"))

    assert identity.auth_user_id == "user-a"
    assert identity.email == "user-a@local.invalid"


def test_dev_auth_adapter_rejects_invalid_token() -> None:
    with pytest.raises(AuthenticationError):
        asyncio.run(DevAuthAdapter().authenticate("user-a"))


def test_supabase_auth_adapter_requires_https_project_url() -> None:
    with pytest.raises(ValueError):
        SupabaseAuthAdapter("http://localhost:54321")


def test_supabase_auth_adapter_uses_official_issuer() -> None:
    adapter = SupabaseAuthAdapter("https://project-ref.supabase.co/")

    assert adapter.issuer == "https://project-ref.supabase.co/auth/v1"
    assert adapter.audience == "authenticated"


def test_dev_auth_is_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_MODE", "dev")
    get_settings.cache_clear()
    get_auth_adapter.cache_clear()

    try:
        with pytest.raises(RuntimeError, match="not allowed"):
            get_auth_adapter()
    finally:
        get_settings.cache_clear()
        get_auth_adapter.cache_clear()
