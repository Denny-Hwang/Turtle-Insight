"""Agent orchestration — analysis cycles over injected repos and connectors.

``run_cycle`` is the MVP loop (Scout -> Analyst -> RedTeam -> promote).
``run_full_cycle`` adds the upper/lower layers (Macro -> Strategist -> Analyst
-> Market) to build the full macro -> trend -> chain graph. A candidate is
promoted to ``active`` only when RedTeam passes *and* the promotion gate
(:func:`domain.state.can_promote_to_active`) holds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..agents.analyst import Analyst
from ..agents.base import AgentContext
from ..agents.macro import Macro
from ..agents.market import Market
from ..agents.redteam import RedTeam
from ..agents.scout import Scout
from ..agents.strategist import Strategist
from ..connectors.base import Connector
from ..domain.state import can_promote_to_active, promote
from ..domain.thesis import Status
from ..storage.repository import SignalRepository, ThesisRepository


@dataclass
class CycleResult:
    signals: int = 0
    candidates: int = 0
    reviews: int = 0
    activated: list[str] = field(default_factory=list)


class Orchestrator:
    def __init__(
        self,
        *,
        signal_repo: SignalRepository,
        thesis_repo: ThesisRepository,
        connectors: list[Connector],
        scout: Scout | None = None,
        analyst: Analyst | None = None,
        redteam: RedTeam | None = None,
        macro: Macro | None = None,
        strategist: Strategist | None = None,
        market: Market | None = None,
        now: datetime | None = None,
    ) -> None:
        self._signal_repo = signal_repo
        self._thesis_repo = thesis_repo
        self._connectors = connectors
        self._scout = scout or Scout()
        self._analyst = analyst or Analyst()
        self._redteam = redteam or RedTeam()
        self._macro = macro or Macro()
        self._strategist = strategist or Strategist()
        self._market = market or Market()
        self._now = now

    def _context(self) -> AgentContext:
        return AgentContext(
            signal_repo=self._signal_repo,
            thesis_repo=self._thesis_repo,
            connectors=self._connectors,
            now=self._now,
        )

    def _review_and_promote(self, result: CycleResult) -> None:
        for thesis in self._thesis_repo.list_theses(status=Status.candidate):
            review = self._redteam.review(thesis, now=self._now)
            result.reviews += 1
            if can_promote_to_active(thesis, review):
                self._thesis_repo.upsert_thesis(promote(thesis, Status.active, review))
                result.activated.append(thesis.id)

    def run_cycle(self) -> CycleResult:
        ctx = self._context()
        scout_result = self._scout.run(ctx)
        analyst_result = self._analyst.run(ctx)
        result = CycleResult(signals=scout_result.signals, candidates=analyst_result.theses)
        self._review_and_promote(result)
        return result

    def run_full_cycle(self) -> CycleResult:
        ctx = self._context()
        scout_result = self._scout.run(ctx)
        macro_result = self._macro.run(ctx)
        strategist_result = self._strategist.run(ctx)
        analyst_result = self._analyst.run(ctx)
        self._market.run(ctx)
        result = CycleResult(
            signals=scout_result.signals,
            candidates=macro_result.theses + strategist_result.theses + analyst_result.theses,
        )
        self._review_and_promote(result)
        return result
