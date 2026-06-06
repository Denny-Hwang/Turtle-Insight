"""Strategist agent (trend/chain layer): map megatrends to industry value chains.

Produces the trend thesis that bridges the macro thesis (parent) and the chain
thesis (child), completing macro -> trend -> chain linkage.
"""

from __future__ import annotations

from typing import ClassVar

from ..domain.thesis import Horizon, Layer
from .base import Agent, AgentContext, AgentResult
from .templates import ThesisTemplate, synthesize

DEFAULT_TRENDS: tuple[ThesisTemplate, ...] = (
    ThesisTemplate(
        id="T-2026-0002",
        layer=Layer.trend,
        horizon=Horizon.long,
        title="단일 모델 → 에이전트 시스템으로의 전환",
        claim=(
            "AI 사용이 단일 모델 호출에서 다단계 에이전트 시스템으로 이동하며, 추론 연산·도구 호출·"
            "메모리 수요가 비선형적으로 증가한다."
        ),
        falsifiers=[
            "에이전트 아키텍처가 비용/신뢰성 문제로 단일 모델 대비 확산에 실패",
            "추론 단가 급락으로 에이전트화의 연산 증분 효과가 대부분 상쇄",
        ],
        evidence_tags=["compute", "memory"],
        risks=["과대광고 사이클", "신뢰성·안전 제약"],
        parents=["T-2026-0001"],
        children=["T-2026-0100"],
    ),
)


class Strategist(Agent):
    name: ClassVar[str] = "strategist"

    def __init__(self, templates: tuple[ThesisTemplate, ...] = DEFAULT_TRENDS) -> None:
        self._templates = templates

    def run(self, ctx: AgentContext) -> AgentResult:
        return synthesize(ctx, self._templates, agent_name=self.name, noun="trend thesis(es)")
