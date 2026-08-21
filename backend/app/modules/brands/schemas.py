from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl, StringConstraints, model_validator

BrandName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class BrandCreate(BaseModel):
    name: BrandName
    website: HttpUrl | None = None
    industry: ShortText | None = None
    description: str | None = None
    target_customer: str | None = None
    brand_tone: str | None = None


class BrandUpdate(BaseModel):
    name: BrandName | None = None
    website: HttpUrl | None = None
    industry: ShortText | None = None
    description: str | None = None
    target_customer: str | None = None
    brand_tone: str | None = None

    @model_validator(mode="after")
    def name_cannot_be_null(self) -> "BrandUpdate":
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self

    def persistence_values(self) -> dict[str, Any]:
        values = self.model_dump(exclude_unset=True)
        if "website" in values and values["website"] is not None:
            values["website"] = str(values["website"])
        return values


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    website: str | None
    industry: str | None
    description: str | None
    target_customer: str | None
    brand_tone: str | None
    created_at: datetime
    updated_at: datetime
