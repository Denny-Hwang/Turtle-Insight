"""R1 — validate ``theses/`` against ``schema/thesis.schema.yaml`` (+ graph integrity).

Checks every ``theses/**/*.yaml`` against the JSON Schema (the wire-format
single source of truth), enforces the promotion-gate invariant that an
``active`` thesis carries at least one evidence item, and verifies that
parent/child links resolve (orphan-link check).

``theses/examples/`` are standalone illustrations: they are schema-validated
but excluded from the cross-link integrity check (they may reference theses
that are not part of the canonical store).
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schema" / "thesis.schema.yaml"
THESES_DIR = REPO_ROOT / "theses"
_EXAMPLES_DIR = "examples"


@dataclass
class ValidationResult:
    checked: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"schema at {path} is not a YAML mapping")
    return raw


def iter_thesis_files(theses_dir: Path = THESES_DIR) -> list[Path]:
    return sorted(theses_dir.rglob("*.yaml"))


def _load_mapping(path: Path) -> dict[str, Any] | str:
    """Parse ``path`` as a YAML mapping, or return an error string."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return f"{path}: YAML parse error: {exc}"
    if not isinstance(raw, dict):
        return f"{path}: top-level YAML must be a mapping"
    return raw


def _schema_errors(path: Path, data: dict[str, Any], validator: Draft202012Validator) -> list[str]:
    errors: list[str] = []
    for err in sorted(validator.iter_errors(data), key=str):
        loc = "/".join(str(part) for part in err.path)
        errors.append(f"{path}: {loc or '<root>'}: {err.message}")
    # Promotion-gate invariant beyond the schema: active requires >=1 evidence.
    if data.get("status") == "active" and not data.get("evidence"):
        errors.append(f"{path}: status=active requires at least one evidence item (promotion gate)")
    return errors


def check_orphan_links(files: Iterable[Path]) -> list[str]:
    """Verify parent/child ids resolve. Files under ``examples/`` are skipped as sources."""
    docs: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in files:
        raw = _load_mapping(path)
        if isinstance(raw, dict) and isinstance(raw.get("id"), str):
            docs[raw["id"]] = (path, raw)
    known = set(docs)
    errors: list[str] = []
    for _tid, (path, data) in sorted(docs.items()):
        if _EXAMPLES_DIR in path.parts:
            continue
        for relation in ("parents", "children"):
            refs = data.get(relation) or []
            if not isinstance(refs, list):
                continue
            for ref in refs:
                if ref not in known:
                    errors.append(f"{path}: {relation} references missing thesis '{ref}'")
    return errors


def validate_theses(
    theses_dir: Path = THESES_DIR, schema_path: Path = SCHEMA_PATH
) -> ValidationResult:
    validator = Draft202012Validator(load_schema(schema_path), format_checker=FormatChecker())
    files = iter_thesis_files(theses_dir)
    result = ValidationResult()
    for path in files:
        result.checked += 1
        raw = _load_mapping(path)
        if isinstance(raw, str):
            result.errors.append(raw)
            continue
        result.errors.extend(_schema_errors(path, raw, validator))
    result.errors.extend(check_orphan_links(files))
    return result


def main() -> int:
    result = validate_theses()
    if result.ok:
        print(f"validate: OK — {result.checked} thesis file(s) valid.")
        return 0
    print(
        f"validate: FAILED — {len(result.errors)} error(s) across {result.checked} file(s):",
        file=sys.stderr,
    )
    for err in result.errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
