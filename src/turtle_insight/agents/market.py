"""Market agent (lower layer): market regime + KR/US relative strength.

Reads price/market signals and derives a coarse regime label and a KR-vs-US
relative-strength leader, then stores a compact derived market-regime signal
(link + short summary only). Deterministic; no live calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from ..domain.signal import Signal
from .base import Agent, AgentContext, AgentResult


@dataclass(frozen=True)
class MarketRegime:
    regime: str  # "risk_on" | "risk_off" | "neutral"
    leader: str  # "KR" | "US" | "balanced"
    kr_signals: int
    us_signals: int


def _market_for(ticker: str) -> str:
    return "KR" if ticker.isdigit() else "US"


class Market(Agent):
    name: ClassVar[str] = "market"

    def assess(self, signals: list[Signal]) -> MarketRegime:
        price = [s for s in signals if "price" in s.tags]
        kr = sum(1 for s in price if any(_market_for(t) == "KR" for t in s.tickers))
        us = sum(1 for s in price if any(_market_for(t) == "US" for t in s.tickers))
        if any("risk-off" in s.tags or "defensive" in s.tags for s in signals):
            regime = "risk_off"
        elif price:
            regime = "risk_on"
        else:
            regime = "neutral"
        leader = "KR" if kr > us else "US" if us > kr else "balanced"
        return MarketRegime(regime=regime, leader=leader, kr_signals=kr, us_signals=us)

    def run(self, ctx: AgentContext) -> AgentResult:
        if ctx.signal_repo is None:
            raise ValueError("Market requires a signal_repo in the context")
        now = ctx.now or datetime.now()
        regime = self.assess(ctx.signal_repo.list_signals())
        derived = Signal(
            id="market-regime",
            source="market",
            url="https://finance.yahoo.com/",
            published_at=now,
            summary=(
                f"Market regime={regime.regime}, leader={regime.leader} "
                f"(KR {regime.kr_signals} / US {regime.us_signals} price signals)."
            ),
            tags=sorted(
                {"regime", f"regime:{regime.regime}", f"leader:{regime.leader}", "source:market"}
            ),
        )
        ctx.signal_repo.upsert_signal(derived)
        return AgentResult(
            agent=self.name,
            summary=f"regime={regime.regime}, leader={regime.leader}",
            signals=1,
        )
