"""Canonical thesis store: ``theses/<status>/<id>.yaml`` read/write (ADR-0004).

Files are the source of truth; the status determines the folder, so a status
change *moves* the file. The DB (``storage.sqlite_repo``) is a one-way index
rebuilt from these files.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import yaml

from ..domain.thesis import Status, Thesis

REPO_ROOT = Path(__file__).resolve().parents[3]
THESES_DIR = REPO_ROOT / "theses"
_STATUS_DIRS: tuple[str, ...] = tuple(s.value for s in Status)


def thesis_path(thesis: Thesis, base_dir: Path = THESES_DIR) -> Path:
    return base_dir / thesis.status.value / f"{thesis.id}.yaml"


def _dump(thesis: Thesis) -> str:
    return yaml.safe_dump(thesis.model_dump(mode="json"), sort_keys=False, allow_unicode=True)


def existing_files(thesis_id: str, base_dir: Path = THESES_DIR) -> list[Path]:
    """All on-disk copies of a thesis across status folders (normally 0 or 1)."""
    candidates = (base_dir / status / f"{thesis_id}.yaml" for status in _STATUS_DIRS)
    return [path for path in candidates if path.exists()]


def save_thesis(thesis: Thesis, base_dir: Path = THESES_DIR) -> Path:
    """Write the thesis to its status folder, removing any stale copy elsewhere."""
    target = thesis_path(thesis, base_dir)
    for stale in existing_files(thesis.id, base_dir):
        if stale != target:
            stale.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_dump(thesis), encoding="utf-8")
    return target


def read_thesis(path: Path) -> Thesis:
    return Thesis.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def iter_theses(base_dir: Path = THESES_DIR) -> Iterator[Thesis]:
    """Yield every thesis under the canonical status folders (examples/ excluded)."""
    for status in _STATUS_DIRS:
        folder = base_dir / status
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.yaml")):
            yield read_thesis(path)
