"""FRED connectors (US macro; read-only).

``FredConnector`` replays recorded fixtures (default/demo mode).
``FredLiveConnector`` queries the FRED API (public data, free API key) for the
latest observations of configured series and stores one compact, factual
summary per series — numbers + the series title, link only (GOLDEN RULE 5).
The series title is included so Scout's keyword tagger can route the signal
(e.g. "Electric Power ..." -> ``power``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

import httpx

from ..domain.signal import Signal
from .base import FixtureConnector
from .live import ConnectorError, LiveConnector

_SERIES_URL = "https://api.stlouisfed.org/fred/series"
_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
_SERIES_PAGE_URL = "https://fred.stlouisfed.org/series/{series_id}"
_MAX_SUMMARY = 500
# Fetch a few latest observations so one missing value (".") still leaves a prev.
_OBSERVATIONS_LIMIT = 4


class FredConnector(FixtureConnector):
    source: ClassVar[str] = "fred"


class FredLiveConnector(LiveConnector):
    """Latest observations for configured FRED series ids."""

    source: ClassVar[str] = "fred"

    def __init__(
        self,
        *,
        api_key: str | None,
        series: list[str],
        cache_dir: Path,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
        retries: int = 2,
        backoff: float = 0.5,
    ) -> None:
        super().__init__(
            cache_dir=cache_dir, client=client, timeout=timeout, retries=retries, backoff=backoff
        )
        self._api_key = api_key
        self._series = [s.strip().upper() for s in series if s.strip()]

    def _params(self, series_id: str) -> dict[str, str]:
        if not self._api_key:
            raise ConnectorError("FRED_API_KEY is required for live FRED")
        return {"series_id": series_id, "api_key": self._api_key, "file_type": "json"}

    def _series_title(self, series_id: str) -> str:
        # Nice-to-have metadata: fall back to the bare id if the lookup fails.
        try:
            data = self._get_json(_SERIES_URL, params=self._params(series_id))
            return str(data["seriess"][0]["title"])
        except (ConnectorError, KeyError, IndexError):
            return series_id

    def _observations(self, series_id: str) -> list[dict[str, Any]]:
        params = self._params(series_id) | {
            "sort_order": "desc",
            "limit": str(_OBSERVATIONS_LIMIT),
        }
        data = self._get_json(_OBSERVATIONS_URL, params=params)
        return [obs for obs in data["observations"] if obs.get("value") not in ("", ".")]

    def _fetch_live(self) -> list[Signal]:
        signals: list[Signal] = []
        for series_id in self._series:
            observations = self._observations(series_id)
            if not observations:
                continue
            latest = observations[0]
            title = self._series_title(series_id)
            summary = f"FRED {series_id} ({title}): {latest['value']} on {latest['date']}"
            if len(observations) > 1:
                prev = observations[1]
                summary += f" (prev {prev['value']} on {prev['date']})"
            signals.append(
                Signal(
                    id=f"fred-{series_id}-{latest['date']}",
                    source=self.source,
                    url=_SERIES_PAGE_URL.format(series_id=series_id),
                    published_at=datetime.fromisoformat(str(latest["date"])).replace(tzinfo=UTC),
                    summary=summary[:_MAX_SUMMARY],
                    tags=["macro"],
                )
            )
        return signals
