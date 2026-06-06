"""P6 unit tests: Macro/Strategist build linked candidate theses; Market regime."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from turtle_insight.agents.base import AgentContext
from turtle_insight.agents.macro import Macro
from turtle_insight.agents.market import Market
from turtle_insight.agents.strategist import Strategist
from turtle_insight.domain.signal import Signal
from turtle_insight.domain.thesis import Layer, Status
from turtle_insight.storage.sqlite_repo import SqliteRepository

_NOW = datetime(2026, 6, 5)


def _repo(tmp_path: Path) -> SqliteRepository:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    repo.upsert_signal(
        Signal(
            id="m1",
            source="fred",
            url="https://example.com/m",
            published_at=datetime(2026, 5, 15),
            summary="macro: compute and power demand rising",
            tags=["macro", "compute", "power"],
        )
    )
    repo.upsert_signal(
        Signal(
            id="m2",
            source="market_api",
            url="https://example.com/p",
            published_at=datetime(2026, 5, 29),
            summary="000660 weekly close up on memory demand",
            tickers=["000660"],
            tags=["price", "memory"],
        )
    )
    return repo


def test_macro_builds_macro_layer_thesis_with_child_link(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = Macro().run(AgentContext(signal_repo=repo, thesis_repo=repo, now=_NOW))
    assert result.theses == 1
    macro = repo.get_thesis("T-2026-0001")
    assert macro is not None
    assert macro.layer is Layer.macro
    assert macro.status is Status.candidate
    assert macro.children == ["T-2026-0002"]
    assert macro.evidence and all(e.signal_id for e in macro.evidence)


def test_strategist_builds_trend_linking_macro_and_chain(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    Strategist().run(AgentContext(signal_repo=repo, thesis_repo=repo, now=_NOW))
    trend = repo.get_thesis("T-2026-0002")
    assert trend is not None
    assert trend.layer is Layer.trend
    assert trend.parents == ["T-2026-0001"]
    assert trend.children == ["T-2026-0100"]


def test_market_assess_regime_and_leader(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    market = Market()
    regime = market.assess(repo.list_signals())
    assert regime.regime == "risk_on"
    assert regime.leader == "KR"
    assert regime.kr_signals == 1

    market.run(AgentContext(signal_repo=repo, now=_NOW))
    derived = repo.get_signal("market-regime")
    assert derived is not None
    assert "regime:risk_on" in derived.tags
