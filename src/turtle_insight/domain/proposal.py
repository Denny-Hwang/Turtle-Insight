"""Domain models: Review, Proposal, Brief (agent outputs).

See the I/O contracts in ``AGENTS.md``. Proposals are *suggestions* with
bull/base/bear scenarios and sizing rationale — never imperative buy/sell
calls (GOLDEN RULE 2).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .thesis import AssetLink, Horizon, ThesisId


class Verdict(StrEnum):
    pass_ = "pass"
    revise = "revise"
    reject = "reject"


class Review(BaseModel):
    """RedTeam output for a thesis change."""

    model_config = ConfigDict(extra="forbid")

    thesis_id: ThesisId
    verdict: Verdict
    bear_case: str
    falsifier_check: str
    bias_flags: list[str] = Field(default_factory=list)
    created: datetime


class Scenarios(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bull: str
    base: str
    bear: str


class Constraints(BaseModel):
    """User constraints snapshot used to generate a proposal."""

    model_config = ConfigDict(extra="forbid")

    risk_tolerance: str  # e.g. "conservative" | "moderate" | "aggressive"
    horizon: Horizon
    excluded_sectors: list[str] = Field(default_factory=list)


class ProposalItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thesis_id: ThesisId
    asset: AssetLink
    stance: str  # non-imperative, e.g. "watch" | "accumulate-on-weakness"
    scenarios: Scenarios
    sizing_rationale: str
    risks: list[str] = Field(default_factory=list)


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    items: list[ProposalItem] = Field(default_factory=list)
    constraints_snapshot: Constraints


class BriefKind(StrEnum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    deepdive = "deepdive"


class Brief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: BriefKind
    created: datetime
    body_md: str
    sources: list[str] = Field(default_factory=list)
