"""Repository interfaces (ports) for theses and signals.

Concrete implementations live in ``sqlite_repo`` (MVP) and, later, a Postgres
repository. Agents/services depend on these abstractions, not the DB.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.calibration import CalibrationScore
from ..domain.signal import Signal
from ..domain.thesis import Status, Thesis


class ThesisRepository(ABC):
    @abstractmethod
    def upsert_thesis(self, thesis: Thesis) -> None: ...

    @abstractmethod
    def get_thesis(self, thesis_id: str) -> Thesis | None: ...

    @abstractmethod
    def list_theses(
        self,
        *,
        status: Status | None = None,
        layer: str | None = None,
        ticker: str | None = None,
    ) -> list[Thesis]: ...


class SignalRepository(ABC):
    @abstractmethod
    def upsert_signal(self, signal: Signal) -> None: ...

    @abstractmethod
    def get_signal(self, signal_id: str) -> Signal | None: ...

    @abstractmethod
    def list_signals(self, *, tag: str | None = None) -> list[Signal]: ...


class CalibrationRepository(ABC):
    @abstractmethod
    def add_score(self, score: CalibrationScore) -> None: ...

    @abstractmethod
    def list_scores(self, *, thesis_id: str | None = None) -> list[CalibrationScore]: ...


class Repository(ThesisRepository, SignalRepository, CalibrationRepository, ABC):
    """Combined repository surface (theses + signals + calibration)."""
