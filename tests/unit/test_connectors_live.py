"""Live connectors (ADR-0010): request/normalization contracts without live IO.

All HTTP is served by ``httpx.MockTransport`` (engineering.md: no live external
calls in tests). Covers: EDGAR/FRED normalization, the SEC User-Agent and FRED
key prerequisites, the offline cache fallback, the summary cap, and the
``TI_CONNECTOR_MODE`` switch.
"""

from __future__ import annotations

from pathlib import Path

import httpx

from turtle_insight.config.settings import Settings
from turtle_insight.connectors.dart import DartConnector
from turtle_insight.connectors.edgar import EdgarConnector, EdgarLiveConnector
from turtle_insight.connectors.fred import FredConnector, FredLiveConnector
from turtle_insight.connectors.market_api import MarketApiConnector
from turtle_insight.connectors.news import NewsConnector
from turtle_insight.services.pipeline import build_connectors

_UA = "turtle-insight test@example.com"

_TICKER_MAP = {"0": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"}}
_SUBMISSIONS = {
    "filings": {
        "recent": {
            "form": ["10-Q", "4", "8-K"],
            "filingDate": ["2026-05-21", "2026-05-20", "2026-05-01"],
            "accessionNumber": [
                "0001045810-26-000123",
                "0001045810-26-000122",
                "0001045810-26-000100",
            ],
            "primaryDocument": ["nvda-20260430.htm", "form4.xml", "nvda-8k.htm"],
            "primaryDocDescription": ["10-Q", "FORM 4", "x" * 600],
        }
    }
}


def _edgar_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("User-Agent") != _UA:
            return httpx.Response(403)
        if request.url.host == "www.sec.gov" and request.url.path == "/files/company_tickers.json":
            return httpx.Response(200, json=_TICKER_MAP)
        if request.url.host == "data.sec.gov" and "CIK0001045810" in request.url.path:
            return httpx.Response(200, json=_SUBMISSIONS)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def _edgar(
    tmp_path: Path, transport: httpx.MockTransport, user_agent: str | None = _UA
) -> EdgarLiveConnector:
    return EdgarLiveConnector(
        user_agent=user_agent,
        tickers=["NVDA"],
        cache_dir=tmp_path / "cache",
        client=httpx.Client(transport=transport),
        retries=0,
    )


def test_edgar_live_normalizes_filings(tmp_path: Path) -> None:
    signals = _edgar(tmp_path, _edgar_transport()).fetch()

    assert [s.id for s in signals] == [
        "edgar-0001045810-26-000123",
        "edgar-0001045810-26-000100",
    ]  # Form 4 filtered out
    ten_q = signals[0]
    assert ten_q.source == "edgar"
    assert ten_q.url == (
        "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000123/nvda-20260430.htm"
    )
    assert ten_q.published_at.date().isoformat() == "2026-05-21"
    assert "10-Q filed by NVIDIA CORP (NVDA)" in ten_q.summary
    assert ten_q.tickers == ["NVDA"]
    assert ten_q.tags == ["filing", "10-q"]
    assert all(len(s.summary) <= 500 for s in signals)  # cap holds for the long 8-K description


def test_edgar_live_requires_user_agent(tmp_path: Path) -> None:
    connector = _edgar(tmp_path, _edgar_transport(), user_agent=None)
    assert connector.fetch() == []  # degrades (empty cache), never raises


def test_live_fetch_failure_replays_cache(tmp_path: Path) -> None:
    first = _edgar(tmp_path, _edgar_transport()).fetch()
    assert first

    down = httpx.MockTransport(lambda request: httpx.Response(503))
    replayed = _edgar(tmp_path, down).fetch()
    assert replayed == first  # same cache_dir -> last good signals replayed


_FRED_OBSERVATIONS = {
    "observations": [
        {"date": "2026-06-01", "value": "."},
        {"date": "2026-05-01", "value": "123.4"},
        {"date": "2026-04-01", "value": "120.1"},
    ]
}
_FRED_SERIES = {"seriess": [{"title": "Electric Power Generation Employees"}]}


def _fred_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("api_key") != "k":
            return httpx.Response(400)
        if request.url.path == "/fred/series/observations":
            assert request.url.params.get("sort_order") == "desc"
            return httpx.Response(200, json=_FRED_OBSERVATIONS)
        if request.url.path == "/fred/series":
            return httpx.Response(200, json=_FRED_SERIES)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def _fred(tmp_path: Path, api_key: str | None = "k") -> FredLiveConnector:
    return FredLiveConnector(
        api_key=api_key,
        series=["ces4422000001"],
        cache_dir=tmp_path / "cache",
        client=httpx.Client(transport=_fred_transport()),
        retries=0,
    )


def test_fred_live_builds_macro_signal(tmp_path: Path) -> None:
    signals = _fred(tmp_path).fetch()

    assert len(signals) == 1
    signal = signals[0]
    assert signal.id == "fred-CES4422000001-2026-05-01"  # "." observation skipped
    assert signal.url == "https://fred.stlouisfed.org/series/CES4422000001"
    assert signal.tags == ["macro"]
    # Title + latest/prev values -> routable, factual summary.
    assert "Electric Power Generation Employees" in signal.summary
    assert "123.4 on 2026-05-01" in signal.summary
    assert "(prev 120.1 on 2026-04-01)" in signal.summary


def test_fred_live_without_key_falls_back(tmp_path: Path) -> None:
    assert _fred(tmp_path, api_key=None).fetch() == []


def test_build_connectors_mode_switch(tmp_path: Path) -> None:
    fixture = build_connectors(Settings(_env_file=None))
    assert [type(c) for c in fixture] == [
        EdgarConnector,
        DartConnector,
        FredConnector,
        MarketApiConnector,
        NewsConnector,
    ]

    live = build_connectors(
        Settings(_env_file=None, ti_connector_mode="live", ti_cache_dir=str(tmp_path))
    )
    assert [type(c) for c in live] == [EdgarLiveConnector, FredLiveConnector]
