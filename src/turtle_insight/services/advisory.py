"""Advisory generation shared by the API and viewer: latest proposal + weekly brief.

Pulls active theses from the repository and runs the Allocator/Synthesizer with
a default (overridable) constraints snapshot.
"""

from __future__ import annotations

from datetime import datetime

from ..agents.allocator import Allocator
from ..agents.synthesizer import Synthesizer
from ..domain.calibration import Scorecard, summarize
from ..domain.proposal import Brief, Constraints, Proposal
from ..domain.thesis import Horizon, Status
from ..storage.repository import CalibrationRepository, Repository, ThesisRepository


def default_constraints() -> Constraints:
    return Constraints(risk_tolerance="moderate", horizon=Horizon.long, excluded_sectors=[])


def latest_proposal(
    repo: ThesisRepository,
    constraints: Constraints | None = None,
    *,
    now: datetime | None = None,
) -> Proposal:
    when = now or datetime.now()
    active = repo.list_theses(status=Status.active)
    return Allocator(constraints or default_constraints()).propose(active, now=when)


def weekly_brief(
    repo: ThesisRepository,
    constraints: Constraints | None = None,
    *,
    now: datetime | None = None,
) -> Brief:
    when = now or datetime.now()
    active = repo.list_theses(status=Status.active)
    proposal = Allocator(constraints or default_constraints()).propose(active, now=when)
    return Synthesizer().weekly(active, proposal, now=when)


def calibration_scorecard(repo: CalibrationRepository, *, now: datetime | None = None) -> Scorecard:
    return summarize(repo.list_scores(), now=now or datetime.now())


def daily_brief(repo: Repository, *, now: datetime | None = None) -> Brief:
    when = now or datetime.now()
    active = repo.list_theses(status=Status.active)
    regime_signal = repo.get_signal("market-regime")
    regime = regime_signal.summary if regime_signal is not None else None
    return Synthesizer().daily(active, now=when, regime=regime)


def monthly_brief(
    repo: Repository,
    constraints: Constraints | None = None,
    *,
    now: datetime | None = None,
) -> Brief:
    when = now or datetime.now()
    active = repo.list_theses(status=Status.active)
    proposal = Allocator(constraints or default_constraints()).propose(active, now=when)
    scorecard = summarize(repo.list_scores(), now=when)
    return Synthesizer().monthly(active, proposal, scorecard, now=when)
