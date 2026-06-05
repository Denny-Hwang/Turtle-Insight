"""Agent contract: ``Agent.run(ctx) -> AgentResult`` with injected dependencies.

Agents hold business logic only; all side effects go through the injected
``connectors``/repositories/``inference`` on the context (engineering.md).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

from ..connectors.base import Connector
from ..services.inference import Inference
from ..storage.repository import SignalRepository, ThesisRepository


@dataclass
class AgentContext:
    thesis_repo: ThesisRepository | None = None
    signal_repo: SignalRepository | None = None
    connectors: list[Connector] = field(default_factory=list)
    inference: Inference | None = None
    now: datetime | None = None


@dataclass
class AgentResult:
    agent: str
    summary: str
    signals: int = 0
    theses: int = 0
    reviews: int = 0
    proposals: int = 0
    briefs: int = 0


class Agent(ABC):
    name: ClassVar[str]

    @abstractmethod
    def run(self, ctx: AgentContext) -> AgentResult: ...
