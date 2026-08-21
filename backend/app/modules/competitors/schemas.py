from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints

CompetitorName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
ExternalId = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class CompetitorCreate(BaseModel):
    name: CompetitorName
    website: HttpUrl | None = None
    instagram_url: HttpUrl | None = None
    meta_page_id: ExternalId | None = None
    tiktok_url: HttpUrl | None = None
    metadata: dict[str, Any] | None = None


class CompetitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    brand_id: UUID
    name: str
    website: str | None
    instagram_url: str | None
    meta_page_id: str | None
    tiktok_url: str | None
    metadata: dict[str, Any] | None = Field(validation_alias="extra_metadata")
    created_at: datetime
