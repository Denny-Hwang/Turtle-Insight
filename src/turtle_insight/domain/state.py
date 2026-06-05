"""Thesis state machine (pure): allowed transitions + the promotion gate.

``candidate -> active`` requires, per GOLDEN RULE 3 and
``thesis-and-epistemics.md`` §2: at least one falsifier, at least one dated
evidence item with a url, and a RedTeam ``Review`` with ``verdict == pass``.
This module is pure (no IO) and is tested as a first-class concern.
"""

from __future__ import annotations

from .proposal import Review, Verdict
from .thesis import Status, Thesis

# Allowed status transitions (the only legal edges of the state machine).
ALLOWED_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.draft: frozenset({Status.candidate}),
    Status.candidate: frozenset({Status.active, Status.draft}),  # draft = RedTeam 'revise'
    Status.active: frozenset({Status.invalidated, Status.realized}),
    Status.invalidated: frozenset(),
    Status.realized: frozenset(),
}


class TransitionError(ValueError):
    """Raised for a disallowed transition or a failed promotion gate."""


def is_allowed_transition(src: Status, dst: Status) -> bool:
    return dst in ALLOWED_TRANSITIONS.get(src, frozenset())


def can_promote_to_active(thesis: Thesis, review: Review) -> bool:
    """The hard gate for ``candidate -> active`` (GOLDEN RULE 3)."""
    return (
        review.thesis_id == thesis.id
        and review.verdict is Verdict.pass_
        and bool(thesis.falsifiers)
        and len(thesis.evidence) >= 1
        and all(bool(e.url) for e in thesis.evidence)
    )


def promote(thesis: Thesis, dst: Status, review: Review | None = None) -> Thesis:
    """Return a copy of ``thesis`` moved to ``dst``, enforcing the rules.

    Raises ``TransitionError`` if the edge is not allowed, or if promoting to
    ``active`` without satisfying :func:`can_promote_to_active`.
    """
    if not is_allowed_transition(thesis.status, dst):
        raise TransitionError(f"transition {thesis.status.value} -> {dst.value} is not allowed")
    if dst is Status.active and (review is None or not can_promote_to_active(thesis, review)):
        raise TransitionError(
            "promotion to 'active' requires falsifiers, >=1 dated evidence, "
            "and RedTeam verdict=pass"
        )
    return thesis.model_copy(update={"status": dst})
