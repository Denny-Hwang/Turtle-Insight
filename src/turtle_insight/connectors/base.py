"""Connector interface + a fixture-replay base (MVP).

Connectors are the only path to external sources (engineering.md). For MVP
they replay *recorded fixtures* — no live network calls — so tests are
deterministic and ToS-safe. Text sources keep link + a short factual summary
only (GOLDEN RULE 5); the summary is capped to 500 chars defensively.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from ..domain.signal import Signal

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_MAX_SUMMARY = 500


def load_fixture(source: str, fixtures_dir: Path = FIXTURES_DIR) -> list[dict[str, Any]]:
    path = fixtures_dir / f"{source}.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"fixture {path} must be a JSON list")
    return data


class Connector(ABC):
    """A source of signals. Implementations must not make live calls in MVP."""

    source: ClassVar[str]

    @abstractmethod
    def fetch(self) -> list[Signal]: ...


class FixtureConnector(Connector):
    """Base connector that replays ``fixtures/<source>.json`` into Signals."""

    def fetch(self) -> list[Signal]:
        signals: list[Signal] = []
        for rec in load_fixture(self.source):
            signals.append(
                Signal(
                    id=str(rec["id"]),
                    source=self.source,
                    url=str(rec["url"]),
                    published_at=datetime.fromisoformat(str(rec["published_at"])),
                    summary=str(rec["summary"])[:_MAX_SUMMARY],
                    tickers=list(rec.get("tickers", [])),
                    tags=list(rec.get("tags", [])),
                    raw_ref=rec.get("raw_ref"),
                )
            )
        return signals
