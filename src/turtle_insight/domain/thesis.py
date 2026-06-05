"""Domain models for the thesis graph (pydantic v2).

Mirrors ``schema/thesis.schema.yaml`` (the wire-format single source of truth);
the schema is enforced on YAML files by ``services.validation`` (R1), while
these models are the in-code representation used by agents and storage.
See ``docs/TDD.md`` §2 and ``docs/guidelines/thesis-and-epistemics.md``.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Stable thesis identifier, e.g. "T-2026-0001".
ThesisId = Annotated[str, StringConstraints(pattern=r"^T-\d{4}-\d{4}$")]
# A falsifier is a concrete, observable refutation condition (>=5 chars).
Falsifier = Annotated[str, StringConstraints(min_length=5)]


class Layer(StrEnum):
    macro = "macro"
    trend = "trend"
    chain = "chain"
    asset = "asset"


class Horizon(StrEnum):
    short = "short"  # 1-5y
    long = "long"  # 5-20y


class Status(StrEnum):
    draft = "draft"
    candidate = "candidate"
    active = "active"
    invalidated = "invalidated"
    realized = "realized"


class AssetRole(StrEnum):
    primary = "primary"
    secondary = "secondary"


class ReviewCadence(StrEnum):
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"


class Evidence(BaseModel):
    """A dated, sourced fact backing a thesis. Link + short summary only (no full text)."""

    model_config = ConfigDict(extra="forbid")

    date: date
    source: str
    url: str
    summary: Annotated[str, StringConstraints(max_length=500)]
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    signal_id: str | None = None


class AssetLink(BaseModel):
    """Link from a thesis to a tradable asset (read-only reference; no execution)."""

    model_config = ConfigDict(extra="forbid")

    market: str  # "KR" | "US" | ...
    ticker: str
    role: AssetRole


class Thesis(BaseModel):
    """A falsifiable investment claim — a node in the 4-layer thesis graph."""

    model_config = ConfigDict(extra="forbid")

    id: ThesisId
    layer: Layer
    horizon: Horizon
    title: Annotated[str, StringConstraints(min_length=3)]
    claim: Annotated[str, StringConstraints(min_length=10)]
    conviction: int = Field(default=0, ge=0, le=100)
    status: Status = Status.draft
    parents: list[ThesisId] = Field(default_factory=list)
    children: list[ThesisId] = Field(default_factory=list)
    assets: list[AssetLink] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    falsifiers: list[Falsifier] = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)
    review_cadence: ReviewCadence = ReviewCadence.monthly
    last_reviewed: date | None = None
    created: datetime
