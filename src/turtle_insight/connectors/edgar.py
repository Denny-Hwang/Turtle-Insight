"""SEC EDGAR connectors (US filings; read-only).

``EdgarConnector`` replays recorded fixtures (default/demo mode).
``EdgarLiveConnector`` queries the public SEC submissions API (public-domain
data) for a small ticker watchlist and stores filing *metadata* only — link +
short factual summary, never the document text (GOLDEN RULE 5). SEC fair-access
policy requires a declared User-Agent; we send a handful of requests per cycle,
far below the published rate limits.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

import httpx

from ..domain.signal import Signal
from .base import FixtureConnector
from .live import ConnectorError, LiveConnector

logger = logging.getLogger("turtle_insight.connectors")

_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
_FILING_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
_MAX_SUMMARY = 500
# Substantive periodic/current reports only (skip Form 4s and other admin noise).
_DEFAULT_FORMS = ("10-K", "10-Q", "8-K")


class EdgarConnector(FixtureConnector):
    source: ClassVar[str] = "edgar"


class EdgarLiveConnector(LiveConnector):
    """Recent filings for a ticker watchlist via the SEC submissions API."""

    source: ClassVar[str] = "edgar"

    def __init__(
        self,
        *,
        user_agent: str | None,
        tickers: list[str],
        cache_dir: Path,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
        retries: int = 2,
        backoff: float = 0.5,
        forms: tuple[str, ...] = _DEFAULT_FORMS,
        per_ticker: int = 5,
    ) -> None:
        super().__init__(
            cache_dir=cache_dir, client=client, timeout=timeout, retries=retries, backoff=backoff
        )
        self._user_agent = user_agent
        self._tickers = [t.strip().upper() for t in tickers if t.strip()]
        self._forms = forms
        self._per_ticker = per_ticker

    def _headers(self) -> dict[str, str]:
        if not self._user_agent:
            raise ConnectorError(
                "TI_EDGAR_USER_AGENT is required for live EDGAR (SEC fair-access policy)"
            )
        return {"User-Agent": self._user_agent}

    def _cik_by_ticker(self) -> dict[str, tuple[int, str]]:
        data = self._get_json(_TICKER_MAP_URL, headers=self._headers())
        mapping: dict[str, tuple[int, str]] = {}
        for record in data.values():
            mapping[str(record["ticker"]).upper()] = (int(record["cik_str"]), str(record["title"]))
        return mapping

    def _fetch_live(self) -> list[Signal]:
        if not self._tickers:
            return []
        mapping = self._cik_by_ticker()
        signals: list[Signal] = []
        for ticker in self._tickers:
            if ticker not in mapping:
                logger.warning("edgar: unknown ticker %s (not in SEC company map)", ticker)
                continue
            cik, company = mapping[ticker]
            payload = self._get_json(_SUBMISSIONS_URL.format(cik=cik), headers=self._headers())
            signals.extend(self._signals_for(ticker, cik, company, payload))
        return signals

    def _signals_for(self, ticker: str, cik: int, company: str, payload: Any) -> list[Signal]:
        recent = payload["filings"]["recent"]
        forms = list(recent["form"])
        dates = list(recent["filingDate"])
        accessions = list(recent["accessionNumber"])
        documents = list(recent.get("primaryDocument", []))
        descriptions = list(recent.get("primaryDocDescription", []))

        out: list[Signal] = []
        for idx, form in enumerate(forms):
            if form not in self._forms:
                continue
            if len(out) >= self._per_ticker:
                break
            accession = str(accessions[idx])
            filing_date = str(dates[idx])
            document = str(documents[idx]) if idx < len(documents) and documents[idx] else ""
            description = (
                str(descriptions[idx]) if idx < len(descriptions) and descriptions[idx] else form
            )
            summary = (
                f"{form} filed by {company} ({ticker}) on {filing_date}: {description} "
                "(metadata only; full text at the filing link)."
            )[:_MAX_SUMMARY]
            out.append(
                Signal(
                    id=f"edgar-{accession}",
                    source=self.source,
                    url=_FILING_URL.format(
                        cik=cik, accession=accession.replace("-", ""), document=document
                    ),
                    published_at=datetime.fromisoformat(filing_date).replace(tzinfo=UTC),
                    summary=summary,
                    tickers=[ticker],
                    tags=["filing", form.lower()],
                    raw_ref=accession,
                )
            )
        return out
