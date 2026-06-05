"""P1 unit tests: domain model construction and constraints."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from turtle_insight.domain.thesis import (
    Evidence,
    Horizon,
    Layer,
    Status,
    Thesis,
)


def test_valid_thesis_defaults() -> None:
    t = Thesis(
        id="T-2026-0001",
        layer=Layer.chain,
        horizon=Horizon.long,
        title="title",
        claim="a sufficiently long claim",
        falsifiers=["something observable that would refute this"],
        created=datetime(2026, 1, 1),
    )
    assert t.status is Status.draft
    assert t.conviction == 0
    assert t.evidence == []


def test_thesis_requires_at_least_one_falsifier() -> None:
    with pytest.raises(ValidationError):
        Thesis(
            id="T-2026-0001",
            layer=Layer.asset,
            horizon=Horizon.long,
            title="title",
            claim="a sufficiently long claim",
            falsifiers=[],
            created=datetime(2026, 1, 1),
        )


def test_thesis_id_pattern_enforced() -> None:
    with pytest.raises(ValidationError):
        Thesis(
            id="not-a-valid-id",
            layer=Layer.asset,
            horizon=Horizon.long,
            title="title",
            claim="a sufficiently long claim",
            falsifiers=["observable refutation condition"],
            created=datetime(2026, 1, 1),
        )


def test_evidence_summary_capped_at_500() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            date=date(2026, 1, 1),
            source="src",
            url="https://example.com/x",
            summary="x" * 501,
        )


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Thesis(
            id="T-2026-0001",
            layer=Layer.asset,
            horizon=Horizon.long,
            title="title",
            claim="a sufficiently long claim",
            falsifiers=["observable refutation condition"],
            created=datetime(2026, 1, 1),
            surprise="nope",
        )
