"""Calibration track-record scoring (pure).

Skeleton for registering predictions and scoring realized outcomes so that
``conviction`` is an *earned*, calibrated value (thesis-and-epistemics.md §3).
The Curator agent (P5) drives this; here we provide the pure data + scoring.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .thesis import ThesisId

Period = Literal["month", "year"]


class Prediction(BaseModel):
    """A registered, dated prediction tied to a thesis."""

    model_config = ConfigDict(extra="forbid")

    thesis_id: ThesisId
    statement: str
    by_date: date
    conviction: int = Field(ge=0, le=100)
    created: datetime


class Outcome(BaseModel):
    """The realized result for a prediction."""

    model_config = ConfigDict(extra="forbid")

    thesis_id: ThesisId
    realized: bool
    observed_at: datetime
    note: str | None = None


class CalibrationScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thesis_id: ThesisId
    conviction: int
    realized: bool
    correct: bool
    brier: float
    scored_at: datetime


def brier_score(conviction: int, realized: bool) -> float:
    """Squared error between conviction-as-probability and the realized outcome."""
    probability = conviction / 100.0
    outcome = 1.0 if realized else 0.0
    return (probability - outcome) ** 2


def score(
    prediction: Prediction, outcome: Outcome, *, scored_at: datetime | None = None
) -> CalibrationScore:
    """Score a prediction against its realized outcome."""
    if prediction.thesis_id != outcome.thesis_id:
        raise ValueError("prediction and outcome refer to different theses")
    correct = outcome.realized == (prediction.conviction >= 50)
    return CalibrationScore(
        thesis_id=prediction.thesis_id,
        conviction=prediction.conviction,
        realized=outcome.realized,
        correct=correct,
        brier=brier_score(prediction.conviction, outcome.realized),
        scored_at=scored_at or outcome.observed_at,
    )


class Scorecard(BaseModel):
    """Aggregate calibration over a set of scores (track record)."""

    model_config = ConfigDict(extra="forbid")

    total: int
    correct: int
    accuracy: float
    mean_brier: float
    generated_at: datetime


def summarize(scores: list[CalibrationScore], *, now: datetime) -> Scorecard:
    """Aggregate scores into a scorecard (accuracy + mean Brier)."""
    total = len(scores)
    correct = sum(1 for s in scores if s.correct)
    accuracy = correct / total if total else 0.0
    mean_brier = sum(s.brier for s in scores) / total if total else 0.0
    return Scorecard(
        total=total,
        correct=correct,
        accuracy=accuracy,
        mean_brier=mean_brier,
        generated_at=now,
    )


class PeriodScorecard(BaseModel):
    """Calibration aggregate for one time bucket (track-record trend point)."""

    model_config = ConfigDict(extra="forbid")

    period: str  # "2026-06" (month) or "2026" (year)
    total: int
    correct: int
    accuracy: float
    mean_brier: float


def _period_key(moment: datetime, by: Period) -> str:
    return moment.strftime("%Y-%m") if by == "month" else moment.strftime("%Y")


def history(scores: list[CalibrationScore], *, by: Period = "month") -> list[PeriodScorecard]:
    """Group scores into per-period scorecards (ascending by period)."""
    buckets: dict[str, list[CalibrationScore]] = {}
    for score_item in scores:
        buckets.setdefault(_period_key(score_item.scored_at, by), []).append(score_item)
    result: list[PeriodScorecard] = []
    for period in sorted(buckets):
        bucket = buckets[period]
        total = len(bucket)
        correct = sum(1 for s in bucket if s.correct)
        result.append(
            PeriodScorecard(
                period=period,
                total=total,
                correct=correct,
                accuracy=correct / total if total else 0.0,
                mean_brier=sum(s.brier for s in bucket) / total if total else 0.0,
            )
        )
    return result
