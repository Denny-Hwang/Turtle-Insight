"""Domain model: Signal — a normalized external observation (Scout output).

Link + short summary + metadata only (no full text); enforces GOLDEN RULE 5
via the ``summary`` length cap. See ``AGENTS.md`` and ``docs/TDD.md`` §4.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class Signal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str
    url: str
    published_at: datetime
    summary: Annotated[str, StringConstraints(max_length=500)]  # short factual summary only
    tickers: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    raw_ref: str | None = None
