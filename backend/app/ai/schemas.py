from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CreativeAnalysisOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: NonEmptyText
    hook: str | None
    offer: str | None
    cta: str | None
    angle: str | None
    emotional_triggers: list[str]
    visual_elements: list[str]
    strengths: list[str]
    weaknesses: list[str]
    tags: list[str]
    confidence: float = Field(ge=0, le=1)


PROMPT_VERSION = "creative-analysis-v2"
SCHEMA_VERSION = "creative-analysis-v1"
AI_TASK = "creative_analysis"
