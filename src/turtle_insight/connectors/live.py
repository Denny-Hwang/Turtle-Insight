"""Live-connector base: HTTP fetch with retry/backoff + cached-replay fallback.

Live connectors are opt-in (``TI_CONNECTOR_MODE=live``) and limited to
public-domain government APIs (SEC EDGAR, FRED) so the link + short-summary
storage stays ToS-safe (GOLDEN RULE 5). A successful fetch persists the
*normalized* signals to a small JSON cache; any network/parse failure replays
the last good cache instead of raising, so a flaky source degrades the cycle
but never breaks it (engineering.md "외부 호출 실패는 재시도+백오프 후 누락
플래그", PRD NFR offline resilience).
"""

from __future__ import annotations

import json
import logging
import time
from abc import abstractmethod
from pathlib import Path
from typing import Any

import httpx

from ..domain.signal import Signal
from .base import Connector

logger = logging.getLogger("turtle_insight.connectors")


class ConnectorError(RuntimeError):
    """Raised inside ``_fetch_live`` when a live source cannot be used."""


class LiveConnector(Connector):
    """Base for live HTTP connectors: retry+backoff GETs, cache write/replay."""

    def __init__(
        self,
        *,
        cache_dir: Path,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
        retries: int = 2,
        backoff: float = 0.5,
    ) -> None:
        self._cache_dir = cache_dir
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)
        self._retries = retries
        self._backoff = backoff

    @abstractmethod
    def _fetch_live(self) -> list[Signal]:
        """Fetch and normalize signals from the live source (may raise)."""

    def fetch(self) -> list[Signal]:
        try:
            signals = self._fetch_live()
        except Exception as exc:  # degrade to the last good cache; never crash the cycle
            logger.warning("%s live fetch failed (%s); replaying cached signals", self.source, exc)
            return self._read_cache()
        self._write_cache(signals)
        return signals

    def _get_json(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                response = self._client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < self._retries:
                    time.sleep(self._backoff * (2**attempt))
        raise ConnectorError(
            f"GET {url} failed after {self._retries + 1} attempt(s)"
        ) from last_error

    # --- offline-resilience cache (normalized signals: link + summary only) ---

    def _cache_path(self) -> Path:
        return self._cache_dir / f"{self.source}.json"

    def _write_cache(self, signals: list[Signal]) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        payload = [signal.model_dump(mode="json") for signal in signals]
        self._cache_path().write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _read_cache(self) -> list[Signal]:
        path = self._cache_path()
        if not path.exists():
            return []
        records = json.loads(path.read_text(encoding="utf-8"))
        return [Signal.model_validate(record) for record in records]
