"""Advisory generation shared by the API and viewer: proposals + briefs.

Pulls active theses (and the current market regime) from the repository and
runs the Allocator/Synthesizer with a default (overridable) constraints
snapshot. The market regime (Market agent) shapes proposal stance/sizing.
"""

from __future__ import annotations

from datetime import datetime

from ..agents.allocator import Allocator
from ..agents.market import Market, MarketRegime
from ..agents.synthesizer import Synthesizer
from ..domain.calibration import Period, PeriodScorecard, Scorecard, history, summarize
from ..domain.proposal import Brief, Constraints, Proposal
from ..domain.thesis import Horizon, Status, Thesis
from ..storage.repository import CalibrationRepository, Repository


def default_constraints() -> Constraints:
    return Constraints(risk_tolerance="moderate", horizon=Horizon.long, excluded_sectors=[])


def current_regime(repo: Repository) -> MarketRegime:
    """Re-assess the market regime from the stored signals (deterministic)."""
    return Market().assess(repo.list_signals())


def _proposal_for(
    repo: Repository, active: list[Thesis], constraints: Constraints | None, when: datetime
) -> Proposal:
    regime = current_regime(repo)
    return Allocator(constraints or default_constraints()).propose(active, now=when, regime=regime)


def latest_proposal(
    repo: Repository,
    constraints: Constraints | None = None,
    *,
    now: datetime | None = None,
) -> Proposal:
    when = now or datetime.now()
    active = repo.list_theses(status=Status.active)
    return _proposal_for(repo, active, constraints, when)


def weekly_brief(
    repo: Repository,
    constraints: Constraints | None = None,
    *,
    now: datetime | None = None,
) -> Brief:
    when = now or datetime.now()
    active = repo.list_theses(status=Status.active)
    proposal = _proposal_for(repo, active, constraints, when)
    return Synthesizer().weekly(active, proposal, now=when)


def calibration_scorecard(repo: CalibrationRepository, *, now: datetime | None = None) -> Scorecard:
    return summarize(repo.list_scores(), now=now or datetime.now())


def calibration_history(
    repo: CalibrationRepository, *, by: Period = "month"
) -> list[PeriodScorecard]:
    return history(repo.list_scores(), by=by)


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
    proposal = _proposal_for(repo, active, constraints, when)
    scorecard = summarize(repo.list_scores(), now=when)
    return Synthesizer().monthly(active, proposal, scorecard, now=when)
