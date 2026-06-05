"""Market data API connector (yfinance for MVP; fixtures, read-only)."""

from __future__ import annotations

from typing import ClassVar

from .base import FixtureConnector


class MarketApiConnector(FixtureConnector):
    source: ClassVar[str] = "market_api"
