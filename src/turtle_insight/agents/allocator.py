"""Allocator agent: active theses + constraints -> Proposal (suggestions only).

Each item carries bull/base/bear scenarios, a sizing *rationale*, and risks —
never an imperative buy/sell call (GOLDEN RULE 2 / ADR-0002). Sizing is
explained, not commanded; execution is always left to the human.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from ..domain.proposal import Constraints, Proposal, ProposalItem, Scenarios
from ..domain.thesis import AssetLink, Status, Thesis
from .base import Agent, AgentContext, AgentResult
from .market import MarketRegime

# Non-imperative stances (never "buy"/"sell").
_STANCE_PRIMARY = "accumulate-on-weakness"
_STANCE_SECONDARY = "watch"


def _stance_for(asset: AssetLink, regime: MarketRegime | None) -> str:
    # Risk-off regime: stay defensive (watch) regardless of role.
    if regime is not None and regime.regime == "risk_off":
        return _STANCE_SECONDARY
    return _STANCE_PRIMARY if asset.role.value == "primary" else _STANCE_SECONDARY


def _excluded(thesis: Thesis, constraints: Constraints) -> bool:
    text = f"{thesis.title} {thesis.claim}".lower()
    return any(sector.lower() in text for sector in constraints.excluded_sectors)


def _scenarios(thesis: Thesis) -> Scenarios:
    bear_lead = thesis.falsifiers[0] if thesis.falsifiers else "key assumptions fail"
    return Scenarios(
        bull=f"Thesis compounds: {thesis.title} — demand inflects faster than priced in.",
        base="Thesis holds gradually; returns track fundamentals with normal volatility.",
        bear=f"Thesis breaks if a falsifier holds — e.g. {bear_lead}.",
    )


def _sizing_rationale(
    constraints: Constraints, asset: AssetLink, conviction: int, regime: MarketRegime | None
) -> str:
    weight = "starter" if asset.role.value == "secondary" else "core-candidate"
    text = (
        f"{constraints.risk_tolerance} risk tolerance, {asset.role.value} role -> {weight} sizing; "
        f"scale to conviction ({conviction}/100) and risk with staged entries. "
        "This is a sizing rationale, not a buy/sell instruction."
    )
    if regime is not None:
        rel = "tailwind" if regime.leader == asset.market else "neutral/headwind"
        text += (
            f" Market regime={regime.regime}, KR/US leader={regime.leader} "
            f"({asset.market} relative strength: {rel})."
        )
    return text


class Allocator(Agent):
    name: ClassVar[str] = "allocator"

    def __init__(self, constraints: Constraints) -> None:
        self._constraints = constraints

    def propose(
        self, theses: list[Thesis], *, now: datetime, regime: MarketRegime | None = None
    ) -> Proposal:
        items: list[ProposalItem] = []
        for thesis in theses:
            if thesis.horizon != self._constraints.horizon:
                continue
            if _excluded(thesis, self._constraints):
                continue
            scenarios = _scenarios(thesis)
            for asset in thesis.assets:
                items.append(
                    ProposalItem(
                        thesis_id=thesis.id,
                        asset=asset,
                        stance=_stance_for(asset, regime),
                        scenarios=scenarios,
                        sizing_rationale=_sizing_rationale(
                            self._constraints, asset, thesis.conviction, regime
                        ),
                        risks=list(thesis.risks),
                    )
                )
        return Proposal(generated_at=now, items=items, constraints_snapshot=self._constraints)

    def run(self, ctx: AgentContext) -> AgentResult:
        if ctx.thesis_repo is None:
            raise ValueError("Allocator requires a thesis_repo in the context")
        now = ctx.now or datetime.now()
        active = ctx.thesis_repo.list_theses(status=Status.active)
        proposal = self.propose(active, now=now)
        return AgentResult(
            agent=self.name,
            summary=f"proposed {len(proposal.items)} item(s)",
            proposals=len(proposal.items),
        )
