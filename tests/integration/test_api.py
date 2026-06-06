"""P5 integration tests: FastAPI read-only endpoints (no trading surface)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from turtle_insight.api.app import create_app, get_repo
from turtle_insight.connectors.dart import DartConnector
from turtle_insight.connectors.edgar import EdgarConnector
from turtle_insight.connectors.fred import FredConnector
from turtle_insight.connectors.market_api import MarketApiConnector
from turtle_insight.connectors.news import NewsConnector
from turtle_insight.services.orchestrator import Orchestrator
from turtle_insight.storage.repository import ThesisRepository
from turtle_insight.storage.sqlite_repo import SqliteRepository


def _client(tmp_path: Path) -> TestClient:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    Orchestrator(
        signal_repo=repo,
        thesis_repo=repo,
        connectors=[
            EdgarConnector(),
            DartConnector(),
            FredConnector(),
            MarketApiConnector(),
            NewsConnector(),
        ],
        now=datetime(2026, 6, 5),
    ).run_cycle()

    app = create_app()

    def _override() -> ThesisRepository:
        return repo

    app.dependency_overrides[get_repo] = _override
    return TestClient(app)


def test_health(tmp_path: Path) -> None:
    assert _client(tmp_path).get("/health").json() == {"status": "ok"}


def test_list_and_get_active_thesis(tmp_path: Path) -> None:
    client = _client(tmp_path)
    listing = client.get("/theses", params={"status": "active"}).json()
    assert [t["id"] for t in listing] == ["T-2026-0100"]
    detail = client.get("/theses/T-2026-0100").json()
    assert detail["status"] == "active"
    assert detail["falsifiers"]
    assert client.get("/theses/T-9999-9999").status_code == 404


def test_graph_endpoint(tmp_path: Path) -> None:
    body = _client(tmp_path).get("/theses/T-2026-0100/graph").json()
    assert body["node"]["id"] == "T-2026-0100"
    assert "parents" in body and "children" in body


def test_proposal_and_brief_endpoints(tmp_path: Path) -> None:
    client = _client(tmp_path)
    proposal = client.get("/proposals/latest").json()
    assert proposal["items"], "expected at least one proposal item from the active seed"
    for item in proposal["items"]:
        assert item["scenarios"]["bull"] and item["scenarios"]["bear"]
    brief = client.get("/briefs/weekly").json()
    assert brief["kind"] == "weekly"
    assert "Weekly Brief" in brief["body_md"]


def test_daily_and_monthly_brief_endpoints(tmp_path: Path) -> None:
    client = _client(tmp_path)
    daily = client.get("/briefs/daily").json()
    assert daily["kind"] == "daily"
    assert "Daily Pulse" in daily["body_md"]
    monthly = client.get("/briefs/monthly").json()
    assert monthly["kind"] == "monthly"
    assert "Calibration scorecard" in monthly["body_md"]


def test_market_regime_endpoint(tmp_path: Path) -> None:
    body = _client(tmp_path).get("/market/regime").json()
    assert body["regime"] in {"risk_on", "risk_off", "neutral"}
    assert body["leader"] in {"KR", "US", "balanced"}


def test_calibration_endpoint_empty_by_default(tmp_path: Path) -> None:
    card = _client(tmp_path).get("/calibration").json()
    assert card["total"] == 0
    assert card["accuracy"] == 0.0


def test_no_trading_endpoints(tmp_path: Path) -> None:
    app = _client(tmp_path).app
    paths = app.openapi()["paths"]
    forbidden = ("order", "trade", "buy", "sell", "execute")
    assert not any(word in path.lower() for path in paths for word in forbidden)
    for methods in paths.values():
        assert set(methods).issubset({"get"})  # read-only surface only
