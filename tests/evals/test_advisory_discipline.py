"""P5 eval: advisory outputs obey the GOLDEN RULES (scenarios/risks, links, no imperatives)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from turtle_insight.connectors.base import Connector
from turtle_insight.connectors.dart import DartConnector
from turtle_insight.connectors.edgar import EdgarConnector
from turtle_insight.connectors.fred import FredConnector
from turtle_insight.connectors.market_api import MarketApiConnector
from turtle_insight.connectors.news import NewsConnector
from turtle_insight.services.advisory import latest_proposal, weekly_brief
from turtle_insight.services.orchestrator import Orchestrator
from turtle_insight.storage.sqlite_repo import SqliteRepository

_NOW = datetime(2026, 6, 5)
_IMPERATIVES = ("buy now", "sell now", "매수", "매도", "you should buy", "guaranteed")


def _connectors() -> list[Connector]:
    return [
        EdgarConnector(),
        DartConnector(),
        FredConnector(),
        MarketApiConnector(),
        NewsConnector(),
    ]


def _populated(tmp_path: Path) -> SqliteRepository:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    Orchestrator(signal_repo=repo, thesis_repo=repo, connectors=_connectors(), now=_NOW).run_cycle()
    return repo


def test_proposal_items_have_scenarios_and_risks(tmp_path: Path) -> None:
    proposal = latest_proposal(_populated(tmp_path), now=_NOW)
    assert proposal.items, "seed should yield proposal items"
    for item in proposal.items:
        assert item.scenarios.bull and item.scenarios.base and item.scenarios.bear
        assert item.risks  # GOLDEN RULE 2: risks always surfaced


def test_proposal_uses_no_imperative_stance(tmp_path: Path) -> None:
    proposal = latest_proposal(_populated(tmp_path), now=_NOW)
    for item in proposal.items:
        assert item.stance not in {"buy", "sell"}
        assert "instruction" in item.sizing_rationale.lower()  # explicitly non-directive


def test_weekly_brief_links_only_with_disclaimer(tmp_path: Path) -> None:
    brief = weekly_brief(_populated(tmp_path), now=_NOW)
    assert brief.sources, "brief should cite source links"
    assert all(src.startswith("http") for src in brief.sources)
    assert "not investment advice" in brief.body_md.lower()
    assert not any(token in brief.body_md.lower() for token in _IMPERATIVES)
