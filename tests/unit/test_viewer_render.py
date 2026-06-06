"""P14 unit tests: pure viewer rendering helpers."""

from __future__ import annotations

from datetime import datetime

from turtle_insight.agents.market import MarketRegime
from turtle_insight.domain.calibration import PeriodScorecard, Scorecard
from turtle_insight.domain.proposal import Constraints, Proposal, ProposalItem, Scenarios
from turtle_insight.domain.thesis import AssetLink, AssetRole, Horizon, Layer, Status, Thesis
from turtle_insight.viewer.render import (
    LAYER_COLORS,
    accuracy_by_period,
    build_graph_dot,
    proposal_rows,
    regime_badge,
    scorecard_metrics,
)

_NOW = datetime(2026, 6, 5)


def _thesis(tid: str, layer: Layer, *, parents: list[str], children: list[str]) -> Thesis:
    return Thesis(
        id=tid,
        layer=layer,
        horizon=Horizon.long,
        title=f"{tid} title",
        claim="a sufficiently long claim about demand",
        status=Status.active,
        parents=parents,
        children=children,
        falsifiers=["demand growth stalls"],
        created=_NOW,
    )


def test_build_graph_dot_has_nodes_edges_and_layer_colors() -> None:
    theses = [
        _thesis("T-2026-0001", Layer.macro, parents=[], children=["T-2026-0002"]),
        _thesis("T-2026-0002", Layer.trend, parents=["T-2026-0001"], children=["T-2026-0100"]),
        _thesis("T-2026-0100", Layer.chain, parents=["T-2026-0002"], children=[]),
    ]
    dot = build_graph_dot(theses)
    assert '"T-2026-0001" -> "T-2026-0002";' in dot
    assert '"T-2026-0002" -> "T-2026-0100";' in dot
    assert LAYER_COLORS["macro"] in dot
    assert dot.count("->") == 2  # deduped parent/child edges, no duplicates


def test_build_graph_dot_skips_dangling_edges() -> None:
    # parent not present in the visible set -> no edge emitted
    dot = build_graph_dot(
        [_thesis("T-2026-0100", Layer.chain, parents=["T-2026-9999"], children=[])],
        include_assets=False,
    )
    assert "->" not in dot
    assert '"T-2026-0100"' in dot


def test_build_graph_dot_includes_asset_nodes_when_enabled() -> None:
    chain = _thesis("T-2026-0100", Layer.chain, parents=[], children=[]).model_copy(
        update={"assets": [AssetLink(market="KR", ticker="000660", role=AssetRole.primary)]}
    )
    with_assets = build_graph_dot([chain], include_assets=True)
    assert '"KR:000660"' in with_assets
    assert '"T-2026-0100" -> "KR:000660"' in with_assets
    assert "KR:000660" not in build_graph_dot([chain], include_assets=False)


def test_regime_badge_contains_icon_and_leader() -> None:
    badge = regime_badge(MarketRegime(regime="risk_on", leader="KR", kr_signals=1, us_signals=0))
    assert "🟢" in badge
    assert "risk_on" in badge and "KR" in badge


def test_scorecard_metrics_formats_values() -> None:
    metrics = scorecard_metrics(
        Scorecard(total=4, correct=3, accuracy=0.75, mean_brier=0.123, generated_at=_NOW)
    )
    assert ("Predictions", "4") in metrics
    assert ("Accuracy", "75%") in metrics
    assert ("Mean Brier", "0.123") in metrics


def test_accuracy_by_period_maps_period_to_accuracy() -> None:
    periods = [
        PeriodScorecard(period="2026-05", total=1, correct=1, accuracy=1.0, mean_brier=0.04),
        PeriodScorecard(period="2026-06", total=2, correct=1, accuracy=0.5, mean_brier=0.34),
    ]
    assert accuracy_by_period(periods) == {"2026-05": 1.0, "2026-06": 0.5}


def test_proposal_rows_shape() -> None:
    proposal = Proposal(
        generated_at=_NOW,
        items=[
            ProposalItem(
                thesis_id="T-2026-0100",
                asset=AssetLink(market="KR", ticker="000660", role=AssetRole.primary),
                stance="accumulate-on-weakness",
                scenarios=Scenarios(bull="b", base="ba", bear="be"),
                sizing_rationale="rationale",
                risks=["cycle"],
            )
        ],
        constraints_snapshot=Constraints(risk_tolerance="moderate", horizon=Horizon.long),
    )
    rows = proposal_rows(proposal)
    assert rows == [
        {
            "thesis": "T-2026-0100",
            "asset": "KR:000660",
            "stance": "accumulate-on-weakness",
            "bull": "b",
            "bear": "be",
        }
    ]
