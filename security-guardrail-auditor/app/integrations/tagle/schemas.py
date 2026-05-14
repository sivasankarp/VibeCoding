from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

Archetype = Literal["catalyst", "navigator", "architect", "connector", "pioneer"]


class TagleDimensionScore(BaseModel):
    """One of the five research-backed dimensions referenced on tagle.ai."""

    key: str = Field(..., description="Stable machine key, e.g. growth_orientation")
    label: str
    score: float = Field(..., ge=0, le=100)
    summary: str


class TagleMaturityStage(BaseModel):
    """Twelve-stage maturity spectrum described on tagle.ai."""

    stage_number: int = Field(..., ge=1, le=12)
    stage_key: str
    label: str
    mindset_tier: str
    skills_tier: str


class TagleAssessment(BaseModel):
    """Structured assessment payload (file or API-shaped)."""

    assessment_id: str
    source: Literal["bundled_sample", "file", "api"]
    completed_at: datetime
    quiz_url: HttpUrl | None = None
    archetype: Archetype
    archetype_summary: str
    maturity: TagleMaturityStage
    tagle_score: float = Field(..., ge=0, le=100, description="Overall Tagle-style readiness score")
    dimensions: list[TagleDimensionScore]
    action_plan_highlights: list[str] = Field(default_factory=list)
    disclaimer: str = Field(
        default="Illustrative structured record for engineering demos unless source=api.",
    )
