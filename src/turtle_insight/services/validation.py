"""R1 — validate ``theses/`` against ``schema/thesis.schema.yaml``.

Scaffold only (P0): the real schema validation, required-field checks
(``falsifiers``, ``evidence.url``/``date``) and orphan-link detection land in
P1. The ``main`` entry point below keeps ``make validate`` / CI wired and
green until then.
"""

from __future__ import annotations


def main() -> int:
    """Placeholder R1 entry point. Returns 0 (real checks arrive in P1)."""
    print("validate: thesis schema validation (R1) is implemented in P1 — scaffold only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
