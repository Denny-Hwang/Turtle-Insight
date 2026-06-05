"""P5 unit tests: Curator predictions, calibration, freshness, archive."""

from __future__ import annotations

from datetime import date, datetime

from turtle_insight.agents.curator import (
    Curator,
    register_prediction,
    score_thesis,
    stale_evidence,
)
from turtle_insight.domain.calibration import Outcome
from turtle_insight.domain.thesis import Evidence, Horizon, Layer, Status, Thesis


def _thesis(*, status: Status = Status.active, conviction: int = 70) -> Thesis:
    return Thesis(
        id="T-2026-0100",
        layer=Layer.chain,
        horizon=Horizon.long,
        title="seed",
        claim="a sufficiently long claim about demand",
        conviction=conviction,
        status=status,
        evidence=[Evidence(date=date(2026, 5, 20), source="x", url="https://e/x", summary="s")],
        falsifiers=["demand growth stalls"],
        created=datetime(2026, 6, 5),
    )


def test_register_prediction_carries_conviction_and_future_date() -> None:
    pred = register_prediction(_thesis(conviction=65), now=datetime(2026, 6, 5))
    assert pred.thesis_id == "T-2026-0100"
    assert pred.conviction == 65
    assert pred.by_date > date(2026, 6, 5)


def test_score_thesis_marks_high_conviction_realized_correct() -> None:
    outcome = Outcome(thesis_id="T-2026-0100", realized=True, observed_at=datetime(2027, 1, 1))
    result = score_thesis(_thesis(conviction=80), outcome)
    assert result.correct is True


def test_stale_evidence_flag() -> None:
    thesis = _thesis()
    assert stale_evidence(thesis, now=datetime(2026, 6, 1)) is False
    assert stale_evidence(thesis, now=datetime(2026, 12, 1)) is True


def test_flag_stale_and_archivable() -> None:
    curator = Curator()
    fresh = _thesis()
    assert curator.flag_stale([fresh], now=datetime(2026, 6, 1)) == []
    realized = _thesis(status=Status.realized)
    assert curator.archivable([fresh, realized]) == ["T-2026-0100"]
