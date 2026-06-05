"""P1 unit tests: calibration scoring."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from turtle_insight.domain.calibration import Outcome, Prediction, brier_score, score


def test_brier_score_extremes_and_midpoint() -> None:
    assert brier_score(100, realized=True) == 0.0
    assert brier_score(0, realized=True) == 1.0
    assert brier_score(50, realized=True) == pytest.approx(0.25)


def _prediction(conviction: int) -> Prediction:
    return Prediction(
        thesis_id="T-2026-0001",
        statement="x will happen",
        by_date=date(2026, 12, 31),
        conviction=conviction,
        created=datetime(2026, 1, 1),
    )


def _outcome(realized: bool) -> Outcome:
    return Outcome(thesis_id="T-2026-0001", realized=realized, observed_at=datetime(2026, 6, 1))


def test_score_correct_when_high_conviction_realized() -> None:
    s = score(_prediction(80), _outcome(realized=True))
    assert s.correct is True
    assert s.brier == brier_score(80, realized=True)
    assert s.scored_at == datetime(2026, 6, 1)


def test_score_incorrect_when_high_conviction_not_realized() -> None:
    s = score(_prediction(80), _outcome(realized=False))
    assert s.correct is False


def test_score_rejects_mismatched_thesis() -> None:
    bad = Outcome(thesis_id="T-2026-9999", realized=True, observed_at=datetime(2026, 6, 1))
    with pytest.raises(ValueError, match="different theses"):
        score(_prediction(80), bad)
