"""Synthesizer agent: weekly briefing in Markdown.

Uses links + short summaries only (GOLDEN RULE 5); never reproduces full text.
Output is a suggestion-shaped brief with an explicit decision-support
disclaimer (GOLDEN RULE 2).
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from ..domain.proposal import Brief, BriefKind, Proposal
from ..domain.thesis import Status, Thesis
from .base import Agent, AgentContext, AgentResult


def _thesis_section(thesis: Thesis) -> tuple[list[str], list[str]]:
    lines = [
        f"### {thesis.id} — {thesis.title}",
        f"- Layer/Horizon: {thesis.layer.value}/{thesis.horizon.value} · "
        f"Conviction: {thesis.conviction}/100 · Status: {thesis.status.value}",
        f"- Claim: {thesis.claim}",
    ]
    if thesis.falsifiers:
        lines.append(f"- Falsifiers ({len(thesis.falsifiers)}): e.g. {thesis.falsifiers[0]}")
    sources: list[str] = []
    if thesis.evidence:
        lines.append("- Evidence (links + summaries):")
        for ev in thesis.evidence:
            lines.append(f"  - [{ev.source}]({ev.url}) — {ev.summary} ({ev.date.isoformat()})")
            sources.append(ev.url)
    return lines, sources


def _proposal_section(proposal: Proposal | None) -> list[str]:
    if proposal is None or not proposal.items:
        return ["_No active proposals this week._"]
    lines = ["### Proposal (suggestions — not buy/sell instructions)"]
    for item in proposal.items:
        lines.append(
            f"- {item.thesis_id} · {item.asset.market}:{item.asset.ticker} · stance: {item.stance}"
        )
        lines.append(f"  - bull: {item.scenarios.bull}")
        lines.append(f"  - base: {item.scenarios.base}")
        lines.append(f"  - bear: {item.scenarios.bear}")
        lines.append(f"  - sizing: {item.sizing_rationale}")
    return lines


class Synthesizer(Agent):
    name: ClassVar[str] = "synthesizer"

    def weekly(
        self, theses: list[Thesis], proposal: Proposal | None = None, *, now: datetime
    ) -> Brief:
        parts = [f"# Turtle Insight — Weekly Brief ({now.date().isoformat()})", ""]
        sources: list[str] = []
        parts.append("## Active theses")
        if theses:
            for thesis in theses:
                section, srcs = _thesis_section(thesis)
                parts.extend(section)
                sources.extend(srcs)
        else:
            parts.append("_No active theses yet._")
        parts.append("")
        parts.append("## Advisory")
        parts.extend(_proposal_section(proposal))
        parts.append("")
        parts.append("---")
        parts.append("_Decision-support only. Not investment advice; no orders are placed._")

        deduped: list[str] = []
        for src in sources:
            if src not in deduped:
                deduped.append(src)
        return Brief(kind=BriefKind.weekly, created=now, body_md="\n".join(parts), sources=deduped)

    def run(self, ctx: AgentContext) -> AgentResult:
        if ctx.thesis_repo is None:
            raise ValueError("Synthesizer requires a thesis_repo in the context")
        now = ctx.now or datetime.now()
        theses = ctx.thesis_repo.list_theses(status=Status.active)
        self.weekly(theses, None, now=now)
        return AgentResult(agent=self.name, summary="weekly brief generated", briefs=1)
