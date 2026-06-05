"""P4 unit tests: RedTeam review and verdict."""

from __future__ import annotations

from datetime import date, datetime

from turtle_insight.agents.redteam import RedTeam
from turtle_insight.domain.proposal import Verdict
from turtle_insight.domain.thesis import Evidence, Horizon, Layer, Status, Thesis

_NOW = datetime(2026, 6, 5)


def _candidate(*, with_evidence: bool = True, conviction: int = 0) -> Thesis:
    evidence = (
        [Evidence(date=date(2026, 5, 20), source="dart", url="https://example.com/x", summary="s")]
        if with_evidence
        else []
    )
    return Thesis(
        id="T-2026-0100",
        layer=Layer.chain,
        horizon=Horizon.long,
        title="seed",
        claim="a sufficiently long claim about demand",
        conviction=conviction,
        status=Status.candidate,
        evidence=evidence,
        falsifiers=["demand growth stalls for two consecutive quarters"],
        created=_NOW,
    )


def test_redteam_passes_thesis_with_falsifiers_and_evidence() -> None:
    review = RedTeam().review(_candidate(), now=_NOW)
    assert review.verdict is Verdict.pass_
    assert review.thesis_id == "T-2026-0100"
    assert "1 dated evidence" in review.falsifier_check


def test_redteam_revises_thesis_without_evidence() -> None:
    review = RedTeam().review(_candidate(with_evidence=False), now=_NOW)
    assert review.verdict is Verdict.revise


def test_redteam_flags_high_conviction_on_thin_evidence() -> None:
    review = RedTeam().review(_candidate(conviction=90), now=_NOW)
    assert any("high conviction" in flag for flag in review.bias_flags)
