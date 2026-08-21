from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl, StringConstraints, model_validator

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class CreativeCreate(BaseModel):
    ownership_type: Literal["own", "competitor", "market"]
    competitor_id: UUID | None = None
    source: Literal["manual"] = "manual"
    source_external_id: str | None = None
    source_url: HttpUrl | None = None
    media_type: Literal["image", "video", "carousel", "text"]
    title: Title | None = None
    body: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    raw_payload: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_manual_creative(self) -> "CreativeCreate":
        if self.ownership_type == "competitor" and self.competitor_id is None:
            raise ValueError("competitor ownership requires competitor_id")
        if self.ownership_type != "competitor" and self.competitor_id is not None:
            raise ValueError("competitor_id is only valid for competitor ownership")
        if not any((self.title, self.body, self.source_url)):
            raise ValueError("at least one of title, body, or source_url is required")
        if self.first_seen_at and self.last_seen_at and self.first_seen_at > self.last_seen_at:
            raise ValueError("first_seen_at cannot be later than last_seen_at")
        return self


class CreativeAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    creative_id: UUID
    job_id: UUID
    status: str
    summary: str
    hook: str | None
    offer: str | None
    cta: str | None
    angle: str | None
    emotional_triggers: list[str]
    visual_elements: list[str]
    strengths: list[str]
    weaknesses: list[str]
    tags: list[str]
    confidence: float
    provider: str
    model: str
    prompt_version: str
    schema_version: str
    created_at: datetime


class CreativeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    brand_id: UUID
    competitor_id: UUID | None
    ownership_type: str
    source: str
    source_external_id: str | None
    source_url: str | None
    media_type: str
    title: str | None
    body: str | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CreativeDetailResponse(CreativeResponse):
    analyses: list[CreativeAnalysisResponse]


class AnalysisJobCreate(BaseModel):
    force: bool = False
