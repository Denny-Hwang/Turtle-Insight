"""P5 unit tests: Allocator produces non-imperative proposals with scenarios."""

from __future__ import annotations

from datetime import date, datetime

from turtle_insight.agents.allocator import Allocator
from turtle_insight.domain.proposal import Constraints
from turtle_insight.domain.thesis import (
    AssetLink,
    AssetRole,
    Evidence,
    Horizon,
    Layer,
    Status,
    Thesis,
)

_NOW = datetime(2026, 6, 5)


def _active() -> Thesis:
    return Thesis(
        id="T-2026-0100",
        layer=Layer.chain,
        horizon=Horizon.long,
        title="agentic inference -> memory/power bottleneck",
        claim="a sufficiently long claim about demand",
        conviction=40,
        status=Status.active,
        assets=[
            AssetLink(market="US", ticker="NVDA", role=AssetRole.primary),
            AssetLink(market="KR", ticker="000660", role=AssetRole.secondary),
        ],
        evidence=[Evidence(date=date(2026, 5, 20), source="x", url="https://e/x", summary="s")],
        falsifiers=["demand growth stalls for two consecutive quarters"],
        risks=["cycle volatility"],
        created=_NOW,
    )


def _constraints(**kw: object) -> Constraints:
    base: dict[str, object] = {
        "risk_tolerance": "moderate",
        "horizon": Horizon.long,
        "excluded_sectors": [],
    }
    base.update(kw)
    return Constraints(**base)  # type: ignore[arg-type]


def test_proposal_items_have_scenarios_sizing_and_risks() -> None:
    proposal = Allocator(_constraints()).propose([_active()], now=_NOW)
    assert len(proposal.items) == 2
    for item in proposal.items:
        assert item.scenarios.bull and item.scenarios.base and item.scenarios.bear
        assert item.sizing_rationale
        assert item.risks == ["cycle volatility"]


def test_stance_is_non_imperative() -> None:
    proposal = Allocator(_constraints()).propose([_active()], now=_NOW)
    stances = {item.stance for item in proposal.items}
    assert stances <= {"accumulate-on-weakness", "watch"}
    assert "buy" not in stances and "sell" not in stances


def test_horizon_mismatch_is_filtered_out() -> None:
    proposal = Allocator(_constraints(horizon=Horizon.short)).propose([_active()], now=_NOW)
    assert proposal.items == []


def test_excluded_sector_is_filtered_out() -> None:
    proposal = Allocator(_constraints(excluded_sectors=["memory"])).propose([_active()], now=_NOW)
    assert proposal.items == []
