"""Curator agent: register predictions, score calibration, flag stale evidence, archive.

Keeps ``conviction`` honest by tying each active thesis to a dated prediction
that is later scored against the realized outcome (thesis-and-epistemics §3).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import ClassVar

from ..domain.calibration import CalibrationScore, Outcome, Prediction, Scorecard, score, summarize
from ..domain.thesis import Status, Thesis
from ..storage.repository import CalibrationRepository
from .base import Agent, AgentContext, AgentResult

# Rough target horizons for predictions (days), by thesis horizon.
_HORIZON_DAYS: dict[str, int] = {"short": 365 * 2, "long": 365 * 7}


def register_prediction(thesis: Thesis, *, now: datetime) -> Prediction:
    days = _HORIZON_DAYS.get(thesis.horizon.value, 365 * 3)
    return Prediction(
        thesis_id=thesis.id,
        statement=thesis.claim,
        by_date=(now + timedelta(days=days)).date(),
        conviction=thesis.conviction,
        created=now,
    )


def score_thesis(
    thesis: Thesis, outcome: Outcome, *, now: datetime | None = None
) -> CalibrationScore:
    prediction = register_prediction(thesis, now=now or outcome.observed_at)
    return score(prediction, outcome, scored_at=now)


def stale_evidence(thesis: Thesis, *, now: datetime, max_age_days: int = 120) -> bool:
    if not thesis.evidence:
        return True
    newest = max(ev.date for ev in thesis.evidence)
    return (now.date() - newest).days > max_age_days


class Curator(Agent):
    name: ClassVar[str] = "curator"

    def flag_stale(
        self, theses: list[Thesis], *, now: datetime, max_age_days: int = 120
    ) -> list[str]:
        return [t.id for t in theses if stale_evidence(t, now=now, max_age_days=max_age_days)]

    def archivable(self, theses: list[Thesis]) -> list[str]:
        return [t.id for t in theses if t.status in (Status.invalidated, Status.realized)]

    def score_and_record(
        self,
        repo: CalibrationRepository,
        thesis: Thesis,
        outcome: Outcome,
        *,
        now: datetime | None = None,
    ) -> CalibrationScore:
        result = score_thesis(thesis, outcome, now=now)
        repo.add_score(result)
        return result

    def scorecard(self, scores: list[CalibrationScore], *, now: datetime) -> Scorecard:
        return summarize(scores, now=now)

    def register_active(
        self, repo: CalibrationRepository, theses: list[Thesis], *, now: datetime
    ) -> int:
        """Register (upsert) a dated prediction for each active thesis."""
        count = 0
        for thesis in theses:
            repo.add_prediction(register_prediction(thesis, now=now))
            count += 1
        return count

    def record_outcome(
        self,
        repo: CalibrationRepository,
        prediction: Prediction,
        *,
        realized: bool,
        now: datetime,
        note: str | None = None,
    ) -> CalibrationScore:
        """Score a registered prediction against its realized outcome and persist it."""
        outcome = Outcome(
            thesis_id=prediction.thesis_id, realized=realized, observed_at=now, note=note
        )
        result = score(prediction, outcome, scored_at=now)
        repo.add_score(result)
        return result

    def run(self, ctx: AgentContext) -> AgentResult:
        if ctx.thesis_repo is None:
            raise ValueError("Curator requires a thesis_repo in the context")
        now = ctx.now or datetime.now()
        active = ctx.thesis_repo.list_theses(status=Status.active)
        stale = self.flag_stale(active, now=now)
        return AgentResult(
            agent=self.name,
            summary=f"{len(active)} active reviewed, {len(stale)} flagged stale",
        )
