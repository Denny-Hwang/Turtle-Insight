"""News connector (link + <=500 char factual summary only; no full text)."""

from __future__ import annotations

from typing import ClassVar

from .base import FixtureConnector


class NewsConnector(FixtureConnector):
    source: ClassVar[str] = "news"
