"""P3 integration tests: Scout ingests fixture signals (link + summary only)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from turtle_insight.agents.base import AgentContext
from turtle_insight.agents.scout import Scout, normalize
from turtle_insight.connectors.base import Connector
from turtle_insight.connectors.dart import DartConnector
from turtle_insight.connectors.edgar import EdgarConnector
from turtle_insight.connectors.fred import FredConnector
from turtle_insight.connectors.market_api import MarketApiConnector
from turtle_insight.connectors.news import NewsConnector
from turtle_insight.domain.signal import Signal
from turtle_insight.storage.sqlite_repo import SqliteRepository


def _repo(tmp_path: Path) -> SqliteRepository:
    return SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")


def _connectors() -> list[Connector]:
    return [
        EdgarConnector(),
        DartConnector(),
        FredConnector(),
        MarketApiConnector(),
        NewsConnector(),
    ]


def test_connectors_are_offline_fixtures() -> None:
    for connector in _connectors():
        signals = connector.fetch()
        assert signals, f"{connector.source} fixture should yield at least one signal"
        assert all(s.source == connector.source for s in signals)
        assert all(len(s.summary) <= 500 for s in signals)  # link + summary only


def test_scout_ingests_and_tags_signals(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    result = Scout().run(AgentContext(signal_repo=repo, connectors=_connectors()))
    stored = repo.list_signals()
    assert result.signals >= 5
    assert len(stored) == result.signals
    # no full text retained; every signal carries a source tag
    assert all(len(s.summary) <= 500 for s in stored)
    assert all(any(t.startswith("source:") for t in s.tags) for s in stored)


def test_scout_is_idempotent(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    ctx = AgentContext(signal_repo=repo, connectors=_connectors())
    first = Scout().run(ctx)
    Scout().run(ctx)
    assert len(repo.list_signals()) == first.signals  # upsert: no duplicates


def test_normalize_adds_routing_tags() -> None:
    signal = Signal(
        id="x",
        source="news",
        url="https://example.com/x",
        published_at=datetime(2026, 1, 1),
        summary="HBM memory demand surges as 전력 grid constraints tighten",
    )
    tagged = normalize(signal)
    assert {"memory", "power", "source:news"} <= set(tagged.tags)
