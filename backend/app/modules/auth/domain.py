from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    auth_user_id: str
    email: str
    name: str | None = None
