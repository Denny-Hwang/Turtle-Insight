"""P1 unit tests: R1 schema validation + orphan-link checks."""

from __future__ import annotations

import textwrap
from pathlib import Path

from turtle_insight.services.validation import (
    SCHEMA_PATH,
    check_orphan_links,
    validate_theses,
)


def test_repo_examples_pass_validation() -> None:
    """The committed theses/examples must satisfy the schema (exit criterion)."""
    result = validate_theses()
    assert result.ok, result.errors
    assert result.checked >= 1


def _write(path: Path, body: str) -> Path:
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def test_schema_violation_detected(tmp_path: Path) -> None:
    _write(
        tmp_path / "T-2026-9999.yaml",
        """\
        id: T-2026-9999
        layer: asset
        horizon: long
        title: bad
        claim: this claim is long enough
        status: draft
        falsifiers: []
        created: "2026-01-01T00:00:00Z"
        """,
    )
    result = validate_theses(theses_dir=tmp_path, schema_path=SCHEMA_PATH)
    assert not result.ok
    assert any("falsifiers" in e for e in result.errors)


def test_active_requires_evidence(tmp_path: Path) -> None:
    _write(
        tmp_path / "T-2026-0010.yaml",
        """\
        id: T-2026-0010
        layer: asset
        horizon: long
        title: active no evidence
        claim: this claim is long enough
        status: active
        falsifiers: ["observable refutation condition here"]
        created: "2026-01-01T00:00:00Z"
        """,
    )
    result = validate_theses(theses_dir=tmp_path, schema_path=SCHEMA_PATH)
    assert not result.ok
    assert any("evidence" in e for e in result.errors)


def test_orphan_link_detected(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "T-2026-0001.yaml",
        """\
        id: T-2026-0001
        layer: chain
        horizon: long
        title: child
        claim: this claim is long enough to pass
        status: draft
        parents: [T-2026-0002]
        falsifiers: ["observable refutation condition here"]
        created: "2026-01-01T00:00:00Z"
        """,
    )
    errors = check_orphan_links([f])
    assert any("missing thesis" in e and "T-2026-0002" in e for e in errors)
