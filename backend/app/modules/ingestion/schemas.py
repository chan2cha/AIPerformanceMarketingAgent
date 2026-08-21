from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Keyword = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class CollectionSourceCreate(BaseModel):
    platform: Literal["meta_ad_library", "tiktok_creative_center"]
    scope: Literal["competitor", "industry"]
    competitor_id: UUID | None = None
    external_identifier: Identifier | None = None
    country_code: Annotated[str, StringConstraints(to_upper=True, pattern=r"^[A-Z]{2}$")] = "VN"
    language_code: Annotated[
        str, StringConstraints(to_lower=True, pattern=r"^[a-z]{2}(-[a-z]{2})?$")
    ] | None = "vi"
    keywords: list[Keyword] = Field(default_factory=list, max_length=20)
    sync_interval_hours: int = Field(default=24, ge=1, le=168)

    @model_validator(mode="after")
    def validate_scope(self) -> "CollectionSourceCreate":
        if self.scope == "competitor" and self.competitor_id is None:
            raise ValueError("competitor scope requires competitor_id")
        if self.scope == "industry" and self.competitor_id is not None:
            raise ValueError("competitor_id is only valid for competitor scope")
        if self.scope == "industry" and not self.keywords:
            raise ValueError("industry scope requires at least one keyword")
        return self


class CollectionSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    brand_id: UUID
    competitor_id: UUID | None
    created_by_user_id: UUID | None
    platform: str
    scope: str
    external_identifier: str | None
    country_code: str
    language_code: str | None
    keywords: list[str]
    status: str
    sync_interval_hours: int
    next_sync_at: datetime | None
    last_attempt_at: datetime | None
    last_sync_at: datetime | None
    last_error_code: str | None
    created_at: datetime
    updated_at: datetime


class CollectionSyncCreate(BaseModel):
    analyze_new_creatives: bool = True


class CollectionSourceUpdate(BaseModel):
    status: Literal["active", "paused"] | None = None
    sync_interval_hours: int | None = Field(default=None, ge=1, le=168)

    @model_validator(mode="after")
    def validate_non_empty(self) -> "CollectionSourceUpdate":
        if self.status is None and self.sync_interval_hours is None:
            raise ValueError("at least one field is required")
        return self
