"""P7 unit tests: calibration scorecard aggregation."""

from __future__ import annotations

from datetime import datetime

import pytest

from turtle_insight.agents.curator import Curator
from turtle_insight.domain.calibration import CalibrationScore, history, summarize

_NOW = datetime(2026, 6, 5)


def _score(*, correct: bool, brier: float, scored_at: datetime = _NOW) -> CalibrationScore:
    return CalibrationScore(
        thesis_id="T-2026-0001",
        conviction=80,
        realized=correct,
        correct=correct,
        brier=brier,
        scored_at=scored_at,
    )


def test_history_groups_by_month_ascending() -> None:
    periods = history(
        [
            _score(correct=True, brier=0.04, scored_at=datetime(2026, 5, 10)),
            _score(correct=False, brier=0.64, scored_at=datetime(2026, 6, 1)),
            _score(correct=True, brier=0.04, scored_at=datetime(2026, 6, 20)),
        ]
    )
    assert [p.period for p in periods] == ["2026-05", "2026-06"]
    assert periods[1].total == 2
    assert periods[1].correct == 1
    assert periods[1].accuracy == 0.5


def test_summarize_empty_is_zeroed() -> None:
    card = summarize([], now=_NOW)
    assert card.total == 0
    assert card.correct == 0
    assert card.accuracy == 0.0
    assert card.mean_brier == 0.0


def test_summarize_counts_accuracy_and_mean_brier() -> None:
    card = summarize(
        [_score(correct=True, brier=0.04), _score(correct=False, brier=0.64)], now=_NOW
    )
    assert card.total == 2
    assert card.correct == 1
    assert card.accuracy == pytest.approx(0.5)
    assert card.mean_brier == pytest.approx(0.34)


def test_curator_scorecard_delegates_to_summarize() -> None:
    card = Curator().scorecard([_score(correct=True, brier=0.04)], now=_NOW)
    assert card.total == 1
    assert card.accuracy == 1.0
