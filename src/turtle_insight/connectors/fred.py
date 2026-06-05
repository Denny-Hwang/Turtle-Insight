"""FRED connector (US macro; fixtures, read-only)."""

from __future__ import annotations

from typing import ClassVar

from .base import FixtureConnector


class FredConnector(FixtureConnector):
    source: ClassVar[str] = "fred"
