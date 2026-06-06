"""Shared rule-based thesis synthesis: a template grown from matching signals.

Used by the layer agents (Macro/Strategist/Analyst) to build candidate theses
deterministically — evidence links to the supporting signals (``signal_id``,
dated, with url) and falsifiers are explicit — so the promotion gate is
reproducible. LLM-assisted synthesis (services.inference) is a later upgrade.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from ..domain.signal import Signal
from ..domain.thesis import AssetLink, AssetRole, Evidence, Horizon, Layer, Status, Thesis
from .base import AgentContext, AgentResult


@dataclass(frozen=True)
class ThesisTemplate:
    id: str
    layer: Layer
    horizon: Horizon
    title: str
    claim: str
    falsifiers: list[str]
    evidence_tags: list[str]
    risks: list[str] = field(default_factory=list)
    parents: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)


def _market_for(ticker: str) -> str:
    return "KR" if ticker.isdigit() else "US"


def assets_from_signals(signals: Iterable[Signal]) -> list[AssetLink]:
    ordered: list[str] = []
    for signal in signals:
        for ticker in signal.tickers:
            if ticker not in ordered:
                ordered.append(ticker)
    return [
        AssetLink(
            market=_market_for(ticker),
            ticker=ticker,
            role=AssetRole.primary if index == 0 else AssetRole.secondary,
        )
        for index, ticker in enumerate(ordered)
    ]


def build_candidate(
    template: ThesisTemplate, signals: list[Signal], now: datetime
) -> Thesis | None:
    """Build a candidate thesis from signals matching the template's tags.

    Returns ``None`` when no signals support it (evidence is never fabricated).
    """
    matched = [s for s in signals if set(s.tags) & set(template.evidence_tags)]
    if not matched:
        return None
    evidence = [
        Evidence(
            date=s.published_at.date(),
            source=s.source,
            url=s.url,
            summary=s.summary,
            weight=0.5,
            signal_id=s.id,
        )
        for s in matched
    ]
    return Thesis(
        id=template.id,
        layer=template.layer,
        horizon=template.horizon,
        title=template.title,
        claim=template.claim,
        status=Status.candidate,
        parents=list(template.parents),
        children=list(template.children),
        assets=assets_from_signals(matched),
        evidence=evidence,
        falsifiers=list(template.falsifiers),
        risks=list(template.risks),
        created=now,
    )


def synthesize(
    ctx: AgentContext,
    templates: Iterable[ThesisTemplate],
    *,
    agent_name: str,
    noun: str,
) -> AgentResult:
    """Run a layer agent: build candidate theses from templates and upsert them."""
    if ctx.signal_repo is None or ctx.thesis_repo is None:
        raise ValueError(f"{agent_name} requires signal_repo and thesis_repo in the context")
    now = ctx.now or datetime.now()
    signals = ctx.signal_repo.list_signals()
    count = 0
    for template in templates:
        thesis = build_candidate(template, signals, now)
        if thesis is None:
            continue
        ctx.thesis_repo.upsert_thesis(thesis)
        count += 1
    return AgentResult(agent=agent_name, summary=f"created {count} {noun}", theses=count)
