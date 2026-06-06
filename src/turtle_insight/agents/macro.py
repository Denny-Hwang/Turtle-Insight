"""Macro agent (top layer): synthesize Macro theses from macro-scale signals.

Completes the top of the graph: the macro thesis is the parent of the trend
thesis (Strategist). Deterministic, evidence-linked synthesis (templates).
"""

from __future__ import annotations

from typing import ClassVar

from ..domain.thesis import Horizon, Layer
from .base import Agent, AgentContext, AgentResult
from .templates import ThesisTemplate, synthesize

DEFAULT_MACRO: tuple[ThesisTemplate, ...] = (
    ThesisTemplate(
        id="T-2026-0001",
        layer=Layer.macro,
        horizon=Horizon.long,
        title="지능의 유틸리티화 — AI 능력의 범용 인프라화",
        claim=(
            "AI 능력이 전기·인터넷처럼 범용 유틸리티로 확산되며, 장기적으로 연산·데이터·전력 "
            "수요의 구조적 증가를 견인한다."
        ),
        falsifiers=[
            "범용 AI 도입이 정체되어 연산·전력 수요 증가율이 4개 분기 연속 둔화",
            "핵심 응용에서 ROI 부진으로 설비·연구 투자가 추세적으로 축소",
        ],
        evidence_tags=["macro", "compute", "power", "memory"],
        risks=["기술 과열·자본 과잉", "규제·지정학 충격"],
        children=["T-2026-0002"],
    ),
)


class Macro(Agent):
    name: ClassVar[str] = "macro"

    def __init__(self, templates: tuple[ThesisTemplate, ...] = DEFAULT_MACRO) -> None:
        self._templates = templates

    def run(self, ctx: AgentContext) -> AgentResult:
        return synthesize(ctx, self._templates, agent_name=self.name, noun="macro thesis(es)")
