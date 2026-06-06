"""P12 integration test: the analyze entry point populates the DB end to end."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from turtle_insight.domain.thesis import Status
from turtle_insight.services.pipeline import analyze
from turtle_insight.services.validation import validate_theses
from turtle_insight.storage.files import read_thesis
from turtle_insight.storage.sqlite_repo import SqliteRepository

_NOW = datetime(2026, 6, 5)


def test_analyze_full_cycle_populates_graph(tmp_path: Path) -> None:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    result = analyze(repo, full=True, now=_NOW)

    assert result.signals >= 5
    assert set(result.activated) == {"T-2026-0001", "T-2026-0002", "T-2026-0100"}
    assert {t.id for t in repo.list_theses(status=Status.active)} == {
        "T-2026-0001",
        "T-2026-0002",
        "T-2026-0100",
    }
    assert repo.list_signals()  # signals ingested for the viewer/API


def test_analyze_mvp_cycle_populates_seed(tmp_path: Path) -> None:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    result = analyze(repo, full=False, now=_NOW)
    assert set(result.activated) == {"T-2026-0100"}


def test_analyze_write_files_materializes_valid_canonical_yaml(tmp_path: Path) -> None:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    base = tmp_path / "theses"
    analyze(repo, full=True, now=_NOW, write_files=True, base_dir=base)

    active_path = base / "active" / "T-2026-0100.yaml"
    assert active_path.exists()
    assert read_thesis(active_path).id == "T-2026-0100"

    # The exported files are a valid, link-resolving canonical store (R1).
    result = validate_theses(theses_dir=base)
    assert result.ok, result.errors
    assert result.checked == 3
