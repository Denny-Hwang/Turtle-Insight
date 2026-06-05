"""Analyst agent: turn signals into candidate Asset/Chain theses.

MVP synthesis is deterministic and rule-based: each configured
:class:`ThesisTemplate` is grown into a candidate thesis whose evidence links
to the matching ingested signals (``signal_id`` set, dated, with url) and whose
falsifiers are explicit. LLM-assisted synthesis via ``services.inference`` is a
v1.x enhancement; keeping this pure makes the promotion gate reproducible.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

from ..domain.signal import Signal
from ..domain.thesis import AssetLink, AssetRole, Evidence, Horizon, Layer, Status, Thesis
from .base import Agent, AgentContext, AgentResult


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


# Seed: agentic-inference demand -> accelerated-compute full-stack bottleneck (memory/power).
DEFAULT_SEEDS: tuple[ThesisTemplate, ...] = (
    ThesisTemplate(
        id="T-2026-0100",
        layer=Layer.chain,
        horizon=Horizon.long,
        title="에이전트 추론 수요 → 가속컴퓨팅 풀스택 병목(메모리·전력)",
        claim=(
            "AI가 단일 모델에서 에이전트 시스템으로 이동하면 추론 연산량이 구조적으로 증가하고, "
            "병목이 연산에서 메모리(HBM)·전력으로 옮겨가 해당 가치사슬의 수요가 장기 증가한다."
        ),
        falsifiers=[
            "에이전트 추론 효율이 급개선되어 메모리·전력 증분 수요 증가율이 2개 분기 연속 둔화",
            "HBM 공급 과잉으로 가격이 추세적으로 하락하고 가동률이 떨어짐",
            "에이전트 도입이 기대보다 느려 추론 트래픽 성장세가 꺾임",
        ],
        evidence_tags=["memory", "power", "compute"],
        risks=["사이클·재고 변동성", "정책·전력 인프라 제약"],
    ),
)


def _market_for(ticker: str) -> str:
    return "KR" if ticker.isdigit() else "US"


def _assets_from_signals(signals: Iterable[Signal]) -> list[AssetLink]:
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


class Analyst(Agent):
    name: ClassVar[str] = "analyst"

    def __init__(self, seeds: tuple[ThesisTemplate, ...] = DEFAULT_SEEDS) -> None:
        self._seeds = seeds

    def _build(self, template: ThesisTemplate, signals: list[Signal], now: datetime) -> Thesis:
        matched = [s for s in signals if set(s.tags) & set(template.evidence_tags)]
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
            assets=_assets_from_signals(matched),
            evidence=evidence,
            falsifiers=list(template.falsifiers),
            risks=list(template.risks),
            created=now,
        )

    def run(self, ctx: AgentContext) -> AgentResult:
        if ctx.signal_repo is None or ctx.thesis_repo is None:
            raise ValueError("Analyst requires signal_repo and thesis_repo in the context")
        now = ctx.now or datetime.now()
        signals = ctx.signal_repo.list_signals()
        count = 0
        for template in self._seeds:
            thesis = self._build(template, signals, now)
            if not thesis.evidence:
                continue  # no supporting signals yet — do not fabricate evidence
            ctx.thesis_repo.upsert_thesis(thesis)
            count += 1
        return AgentResult(
            agent=self.name, summary=f"created {count} candidate thesis(es)", theses=count
        )
