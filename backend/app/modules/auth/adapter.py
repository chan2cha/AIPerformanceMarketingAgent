import asyncio
import re
from collections.abc import Mapping
from typing import Any, Protocol

import jwt
from jwt import InvalidTokenError, PyJWKClient

from app.core.errors import AuthenticationError
from app.modules.auth.domain import AuthenticatedIdentity

DEV_SUBJECT_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
SUPABASE_ALLOWED_ALGORITHMS = frozenset({"RS256", "ES256", "EdDSA"})


class AuthAdapter(Protocol):
    async def authenticate(self, access_token: str) -> AuthenticatedIdentity: ...


class DevAuthAdapter:
    """Deterministic local-only auth using `Bearer dev:<subject>` tokens."""

    async def authenticate(self, access_token: str) -> AuthenticatedIdentity:
        prefix, separator, subject = access_token.partition(":")
        if prefix != "dev" or not separator or not DEV_SUBJECT_PATTERN.fullmatch(subject):
            raise AuthenticationError("유효하지 않은 개발용 인증 토큰입니다.")

        return AuthenticatedIdentity(
            auth_user_id=subject,
            email=f"{subject}@local.invalid",
        )


class SupabaseAuthAdapter:
    def __init__(self, supabase_url: str, audience: str = "authenticated") -> None:
        normalized_url = supabase_url.strip().rstrip("/")
        if not normalized_url.startswith("https://"):
            raise ValueError("SUPABASE_URL must be an https URL")

        self.issuer = f"{normalized_url}/auth/v1"
        self.audience = audience
        self.jwks_client = PyJWKClient(f"{self.issuer}/.well-known/jwks.json", cache_keys=True)

    async def authenticate(self, access_token: str) -> AuthenticatedIdentity:
        try:
            claims = await asyncio.to_thread(self._decode, access_token)
        except (InvalidTokenError, ValueError) as error:
            raise AuthenticationError("유효하지 않은 인증 토큰입니다.") from error

        subject = claims.get("sub")
        email = claims.get("email")
        if not isinstance(subject, str) or not subject or not isinstance(email, str) or not email:
            raise AuthenticationError("인증 토큰에 사용자 정보가 없습니다.")

        user_metadata = claims.get("user_metadata")
        name = user_metadata.get("name") if isinstance(user_metadata, Mapping) else None

        return AuthenticatedIdentity(
            auth_user_id=subject,
            email=email.casefold(),
            name=name if isinstance(name, str) else None,
        )

    def _decode(self, access_token: str) -> dict[str, Any]:
        header = jwt.get_unverified_header(access_token)
        algorithm = header.get("alg")
        if algorithm not in SUPABASE_ALLOWED_ALGORITHMS:
            raise InvalidTokenError("Unsupported signing algorithm")

        signing_key = self.jwks_client.get_signing_key_from_jwt(access_token)
        return jwt.decode(
            access_token,
            signing_key.key,
            algorithms=[algorithm],
            audience=self.audience,
            issuer=self.issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
