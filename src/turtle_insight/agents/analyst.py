"""Analyst agent: turn signals into a candidate Chain/Asset thesis.

Deterministic, rule-based synthesis (see :mod:`agents.templates`): evidence
links to the supporting signals and falsifiers are explicit, so the promotion
gate is reproducible. The seed chain thesis links up to the Strategist's trend
thesis (its parent) to complete the macro -> trend -> chain graph.
"""

from __future__ import annotations

from typing import ClassVar

from ..domain.thesis import Horizon, Layer
from .base import Agent, AgentContext, AgentResult
from .templates import ThesisTemplate, synthesize

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
        parents=["T-2026-0002"],
    ),
)


class Analyst(Agent):
    name: ClassVar[str] = "analyst"

    def __init__(self, seeds: tuple[ThesisTemplate, ...] = DEFAULT_SEEDS) -> None:
        self._seeds = seeds

    def run(self, ctx: AgentContext) -> AgentResult:
        return synthesize(ctx, self._seeds, agent_name=self.name, noun="candidate thesis(es)")
