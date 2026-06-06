"""P5 unit tests: Synthesizer weekly brief (links + summaries only)."""

from __future__ import annotations

from datetime import date, datetime

from turtle_insight.agents.synthesizer import Synthesizer
from turtle_insight.domain.calibration import Scorecard
from turtle_insight.domain.proposal import Constraints, Proposal
from turtle_insight.domain.thesis import Evidence, Horizon, Layer, Status, Thesis

_NOW = datetime(2026, 6, 5)


def _active() -> Thesis:
    return Thesis(
        id="T-2026-0100",
        layer=Layer.chain,
        horizon=Horizon.long,
        title="seed thesis",
        claim="a sufficiently long claim about demand",
        status=Status.active,
        evidence=[
            Evidence(date=date(2026, 5, 20), source="keynote", url="https://e/x", summary="short")
        ],
        falsifiers=["demand growth stalls"],
        created=_NOW,
    )


def test_weekly_brief_uses_links_and_records_sources() -> None:
    brief = Synthesizer().weekly([_active()], None, now=_NOW)
    assert brief.kind.value == "weekly"
    assert "https://e/x" in brief.body_md
    assert brief.sources == ["https://e/x"]
    assert "not investment advice" in brief.body_md.lower()


def test_daily_brief_is_concise_with_regime() -> None:
    brief = Synthesizer().daily([_active()], now=_NOW, regime="regime=risk_on, leader=KR")
    assert brief.kind.value == "daily"
    assert "Daily Pulse" in brief.body_md
    assert "risk_on" in brief.body_md
    assert "T-2026-0100" in brief.body_md
    assert brief.sources == []  # headlines only


def test_monthly_brief_includes_scorecard() -> None:
    scorecard = Scorecard(total=4, correct=3, accuracy=0.75, mean_brier=0.12, generated_at=_NOW)
    brief = Synthesizer().monthly([_active()], None, scorecard, now=_NOW)
    assert brief.kind.value == "monthly"
    assert "Calibration scorecard" in brief.body_md
    assert "3/4 correct" in brief.body_md
    assert "not investment advice" in brief.body_md.lower()


def test_weekly_brief_handles_no_theses() -> None:
    empty = Proposal(
        generated_at=_NOW,
        items=[],
        constraints_snapshot=Constraints(risk_tolerance="moderate", horizon=Horizon.long),
    )
    brief = Synthesizer().weekly([], empty, now=_NOW)
    assert "No active theses" in brief.body_md
    assert brief.sources == []
