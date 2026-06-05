"""RedTeam agent: adversarial review of a thesis.

Produces a bear case, a falsifier/evidence check and bias flags, and a verdict.
A thesis can ``pass`` only with at least one falsifier and at least one dated
evidence item carrying a url (GOLDEN RULE 3 / thesis-and-epistemics §2). The
verdict drives ``candidate -> active`` promotion in the orchestrator.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from ..domain.proposal import Review, Verdict
from ..domain.thesis import Status, Thesis
from .base import Agent, AgentContext, AgentResult


def _has_dated_evidence(thesis: Thesis) -> bool:
    return len(thesis.evidence) >= 1 and all(bool(e.url) for e in thesis.evidence)


class RedTeam(Agent):
    name: ClassVar[str] = "redteam"

    def review(self, thesis: Thesis, *, now: datetime | None = None) -> Review:
        has_falsifiers = bool(thesis.falsifiers)
        has_evidence = _has_dated_evidence(thesis)

        bias_flags: list[str] = []
        if not has_falsifiers:
            bias_flags.append("no falsifiers — not a testable thesis")
        if thesis.conviction >= 80 and len(thesis.evidence) < 2:
            bias_flags.append("high conviction on thin evidence")

        verdict = Verdict.pass_ if (has_falsifiers and has_evidence) else Verdict.revise
        lead = thesis.falsifiers[0] if thesis.falsifiers else "(none provided)"
        bear_case = (
            f"Bear case: the thesis breaks if a falsifier holds — e.g. {lead}. "
            "Weigh the most concrete disconfirming signals before sizing."
        )
        falsifier_check = (
            f"{len(thesis.falsifiers)} falsifier(s); "
            f"{len(thesis.evidence)} dated evidence item(s) with url."
        )
        return Review(
            thesis_id=thesis.id,
            verdict=verdict,
            bear_case=bear_case,
            falsifier_check=falsifier_check,
            bias_flags=bias_flags,
            created=now or datetime.now(),
        )

    def run(self, ctx: AgentContext) -> AgentResult:
        if ctx.thesis_repo is None:
            raise ValueError("RedTeam requires a thesis_repo in the context")
        count = 0
        for thesis in ctx.thesis_repo.list_theses(status=Status.candidate):
            self.review(thesis, now=ctx.now)
            count += 1
        return AgentResult(agent=self.name, summary=f"reviewed {count} candidate(s)", reviews=count)
