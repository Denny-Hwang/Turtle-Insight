"""P6 eval: the full cycle builds a connected macro -> trend -> chain graph, all active."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from turtle_insight.connectors.base import Connector
from turtle_insight.connectors.dart import DartConnector
from turtle_insight.connectors.edgar import EdgarConnector
from turtle_insight.connectors.fred import FredConnector
from turtle_insight.connectors.market_api import MarketApiConnector
from turtle_insight.connectors.news import NewsConnector
from turtle_insight.domain.thesis import Layer, Status
from turtle_insight.services.orchestrator import Orchestrator
from turtle_insight.storage.sqlite_repo import SqliteRepository

_NOW = datetime(2026, 6, 5)


def _connectors() -> list[Connector]:
    return [
        EdgarConnector(),
        DartConnector(),
        FredConnector(),
        MarketApiConnector(),
        NewsConnector(),
    ]


def _full(tmp_path: Path) -> SqliteRepository:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    Orchestrator(
        signal_repo=repo, thesis_repo=repo, connectors=_connectors(), now=_NOW
    ).run_full_cycle()
    return repo


def test_all_three_layers_reach_active(tmp_path: Path) -> None:
    repo = _full(tmp_path)
    active = {t.id: t for t in repo.list_theses(status=Status.active)}
    assert set(active) == {"T-2026-0001", "T-2026-0002", "T-2026-0100"}
    assert {active[i].layer for i in active} == {Layer.macro, Layer.trend, Layer.chain}


def test_graph_is_connected(tmp_path: Path) -> None:
    repo = _full(tmp_path)
    macro = repo.get_thesis("T-2026-0001")
    trend = repo.get_thesis("T-2026-0002")
    chain = repo.get_thesis("T-2026-0100")
    assert macro is not None and trend is not None and chain is not None
    assert macro.children == ["T-2026-0002"]
    assert trend.parents == ["T-2026-0001"]
    assert trend.children == ["T-2026-0100"]
    assert chain.parents == ["T-2026-0002"]


def test_every_active_layer_keeps_discipline(tmp_path: Path) -> None:
    repo = _full(tmp_path)
    for thesis in repo.list_theses(status=Status.active):
        assert thesis.falsifiers, f"{thesis.id} missing falsifiers"
        assert thesis.evidence, f"{thesis.id} missing evidence"
        assert all(e.url and e.date for e in thesis.evidence)
        assert all(len(e.summary) <= 500 for e in thesis.evidence)


def test_market_regime_signal_recorded(tmp_path: Path) -> None:
    repo = _full(tmp_path)
    regime = repo.get_signal("market-regime")
    assert regime is not None
    assert any(t.startswith("regime:") for t in regime.tags)
