"""P12 integration test: the analyze entry point populates the DB end to end."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from turtle_insight.domain.thesis import Status
from turtle_insight.services.pipeline import analyze
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
