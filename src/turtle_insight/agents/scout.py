"""Scout agent: ingest signals from connectors, normalize + tag, upsert.

Stores link + short summary + metadata only (no full text). Tagging derives
lightweight routing hints (memory/power/compute/policy) plus a ``source:*``
tag. Upsert by stable id keeps re-runs idempotent.
"""

from __future__ import annotations

from typing import ClassVar

from ..domain.signal import Signal
from .base import Agent, AgentContext, AgentResult

_KEYWORD_TAGS: dict[str, tuple[str, ...]] = {
    "memory": ("hbm", "memory", "dram", "메모리"),
    "power": ("power", "electric", "grid", "전력"),
    "compute": ("gpu", "accelerator", "inference", "추론"),
    "policy": ("regulation", "policy", "tariff", "규제"),
}


def normalize(signal: Signal) -> Signal:
    """Return a copy with derived routing tags and a ``source:*`` tag added."""
    text = f"{signal.summary} {signal.url}".lower()
    derived = {tag for tag, keywords in _KEYWORD_TAGS.items() if any(k in text for k in keywords)}
    tags = sorted(set(signal.tags) | derived | {f"source:{signal.source}"})
    return signal.model_copy(update={"tags": tags})


class Scout(Agent):
    name: ClassVar[str] = "scout"

    def run(self, ctx: AgentContext) -> AgentResult:
        if ctx.signal_repo is None:
            raise ValueError("Scout requires a signal_repo in the context")
        count = 0
        for connector in ctx.connectors:
            for signal in connector.fetch():
                ctx.signal_repo.upsert_signal(normalize(signal))
                count += 1
        return AgentResult(agent=self.name, summary=f"ingested {count} signals", signals=count)
