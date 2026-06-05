"""P4 eval: the seed thesis passes the gate to ``active`` with discipline intact.

Checks GOLDEN RULES on pipeline output: every active thesis carries falsifiers
and dated evidence (with url), and no evidence stores full text (<=500 chars,
GOLDEN RULE 5).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from turtle_insight.connectors.base import Connector
from turtle_insight.connectors.dart import DartConnector
from turtle_insight.connectors.edgar import EdgarConnector
from turtle_insight.connectors.fred import FredConnector
from turtle_insight.connectors.market_api import MarketApiConnector
from turtle_insight.connectors.news import NewsConnector
from turtle_insight.domain.thesis import Status
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


def _run(tmp_path: Path) -> SqliteRepository:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    Orchestrator(signal_repo=repo, thesis_repo=repo, connectors=_connectors(), now=_NOW).run_cycle()
    return repo


def test_seed_thesis_reaches_active(tmp_path: Path) -> None:
    repo = _run(tmp_path)
    active = repo.list_theses(status=Status.active)
    assert {t.id for t in active} == {"T-2026-0100"}


def test_active_thesis_has_falsifiers_and_dated_evidence(tmp_path: Path) -> None:
    repo = _run(tmp_path)
    for thesis in repo.list_theses(status=Status.active):
        assert thesis.falsifiers, f"{thesis.id} missing falsifiers"
        assert thesis.evidence, f"{thesis.id} missing evidence"
        assert all(e.url and e.date for e in thesis.evidence)


def test_active_thesis_stores_no_full_text(tmp_path: Path) -> None:
    repo = _run(tmp_path)
    for thesis in repo.list_theses(status=Status.active):
        assert all(len(e.summary) <= 500 for e in thesis.evidence)
