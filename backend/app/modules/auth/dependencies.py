from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.db.session import get_db_session
from app.modules.auth.adapter import AuthAdapter, DevAuthAdapter, SupabaseAuthAdapter
from app.modules.auth.domain import AuthenticatedIdentity
from app.modules.users.model import User

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_auth_adapter() -> AuthAdapter:
    settings = get_settings()
    if settings.auth_mode == "dev":
        if settings.app_env == "production":
            raise RuntimeError("AUTH_MODE=dev is not allowed when APP_ENV=production")
        return DevAuthAdapter()
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is required when AUTH_MODE=supabase")
    return SupabaseAuthAdapter(settings.supabase_url, settings.supabase_jwt_audience)


async def get_authenticated_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    adapter: Annotated[AuthAdapter, Depends(get_auth_adapter)],
) -> AuthenticatedIdentity:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise AuthenticationError()
    return await adapter.authenticate(credentials.credentials)


def get_current_user(
    identity: Annotated[AuthenticatedIdentity, Depends(get_authenticated_identity)],
    session: Annotated[Session, Depends(get_db_session)],
) -> User:
    user = session.scalar(select(User).where(User.auth_user_id == identity.auth_user_id))
    if user is not None:
        return user

    user = User(
        auth_user_id=identity.auth_user_id,
        email=identity.email.casefold(),
        name=identity.name,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing_user = session.scalar(
            select(User).where(User.auth_user_id == identity.auth_user_id)
        )
        if existing_user is None:
            raise
        return existing_user
    return user


DatabaseSession = Annotated[Session, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
