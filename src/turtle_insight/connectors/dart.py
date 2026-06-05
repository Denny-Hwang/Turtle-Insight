"""DART connector (KR filings; fixtures, read-only)."""

from __future__ import annotations

from typing import ClassVar

from .base import FixtureConnector


class DartConnector(FixtureConnector):
    source: ClassVar[str] = "dart"
