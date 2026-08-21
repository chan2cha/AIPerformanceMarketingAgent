from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


class OrganizationCreate(BaseModel):
    name: NonEmptyName


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    plan: str
    status: str
    created_at: datetime
    updated_at: datetime


class UserOrganizationResponse(BaseModel):
    id: UUID
    name: str
    role: Literal["owner", "admin", "member"]


class MeResponse(BaseModel):
    id: UUID
    email: str
    name: str | None
    organizations: list[UserOrganizationResponse]
