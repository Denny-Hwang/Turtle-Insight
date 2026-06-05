"""P1 unit tests: state machine transitions and the promotion gate."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from turtle_insight.domain.proposal import Review, Verdict
from turtle_insight.domain.state import (
    TransitionError,
    can_promote_to_active,
    is_allowed_transition,
    promote,
)
from turtle_insight.domain.thesis import (
    Evidence,
    Horizon,
    Layer,
    Status,
    Thesis,
)


def _candidate(*, with_evidence: bool = True) -> Thesis:
    evidence = (
        [Evidence(date=date(2026, 1, 1), source="src", url="https://example.com/x", summary="s")]
        if with_evidence
        else []
    )
    return Thesis(
        id="T-2026-0001",
        layer=Layer.chain,
        horizon=Horizon.long,
        title="title",
        claim="a sufficiently long claim",
        status=Status.candidate,
        evidence=evidence,
        falsifiers=["observable refutation condition"],
        created=datetime(2026, 1, 1),
    )


def _review(thesis_id: str = "T-2026-0001", verdict: Verdict = Verdict.pass_) -> Review:
    return Review(
        thesis_id=thesis_id,
        verdict=verdict,
        bear_case="bear",
        falsifier_check="checked",
        created=datetime(2026, 1, 2),
    )


def test_allowed_transitions() -> None:
    assert is_allowed_transition(Status.draft, Status.candidate)
    assert is_allowed_transition(Status.candidate, Status.active)
    assert is_allowed_transition(Status.active, Status.realized)
    assert is_allowed_transition(Status.active, Status.invalidated)


def test_disallowed_transitions() -> None:
    assert not is_allowed_transition(Status.draft, Status.active)
    assert not is_allowed_transition(Status.realized, Status.active)
    assert not is_allowed_transition(Status.invalidated, Status.draft)


def test_gate_passes_with_falsifiers_evidence_and_pass() -> None:
    t = _candidate()
    assert can_promote_to_active(t, _review())
    promoted = promote(t, Status.active, _review())
    assert promoted.status is Status.active
    assert t.status is Status.candidate  # original is unchanged (copy)


def test_gate_blocks_when_verdict_not_pass() -> None:
    t = _candidate()
    assert not can_promote_to_active(t, _review(verdict=Verdict.revise))
    with pytest.raises(TransitionError):
        promote(t, Status.active, _review(verdict=Verdict.revise))


def test_gate_blocks_without_evidence() -> None:
    t = _candidate(with_evidence=False)
    assert not can_promote_to_active(t, _review())


def test_gate_blocks_on_mismatched_review() -> None:
    t = _candidate()
    assert not can_promote_to_active(t, _review(thesis_id="T-2026-9999"))


def test_gate_blocks_without_falsifiers() -> None:
    # The model forbids empty falsifiers; model_copy(update=...) bypasses validation
    # so we can exercise the gate's falsifier branch directly.
    t = _candidate().model_copy(update={"falsifiers": []})
    assert not can_promote_to_active(t, _review())


def test_promote_rejects_disallowed_edge() -> None:
    draft = _candidate().model_copy(update={"status": Status.draft})
    with pytest.raises(TransitionError):
        promote(draft, Status.active, _review())
