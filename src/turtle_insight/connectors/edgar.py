"""SEC EDGAR connector (US filings; fixtures, read-only)."""

from __future__ import annotations

from typing import ClassVar

from .base import FixtureConnector


class EdgarConnector(FixtureConnector):
    source: ClassVar[str] = "edgar"
