"""P4 unit tests: Analyst builds candidate theses from signals."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from turtle_insight.agents.analyst import Analyst
from turtle_insight.agents.base import AgentContext
from turtle_insight.domain.signal import Signal
from turtle_insight.domain.thesis import Status
from turtle_insight.storage.sqlite_repo import SqliteRepository

_NOW = datetime(2026, 6, 5)


def _repo(tmp_path: Path) -> SqliteRepository:
    return SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")


def test_analyst_creates_candidate_linked_to_signals(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.upsert_signal(
        Signal(
            id="s1",
            source="dart",
            url="https://example.com/1",
            published_at=datetime(2026, 5, 20),
            summary="HBM memory demand strong",
            tickers=["000660"],
            tags=["memory"],
        )
    )
    repo.upsert_signal(
        Signal(
            id="s2",
            source="fred",
            url="https://example.com/2",
            published_at=datetime(2026, 5, 15),
            summary="electric power grid investment",
            tags=["power"],
        )
    )

    result = Analyst().run(AgentContext(signal_repo=repo, thesis_repo=repo, now=_NOW))
    assert result.theses == 1

    candidates = repo.list_theses(status=Status.candidate)
    assert len(candidates) == 1
    thesis = candidates[0]
    assert thesis.status is Status.candidate
    assert thesis.falsifiers  # explicit falsifiers attached
    assert {e.signal_id for e in thesis.evidence} == {"s1", "s2"}
    assert all(e.url and e.date for e in thesis.evidence)
    assert any(a.ticker == "000660" and a.market == "KR" for a in thesis.assets)


def test_analyst_skips_template_without_supporting_signals(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.upsert_signal(
        Signal(
            id="s3",
            source="news",
            url="https://example.com/3",
            published_at=datetime(2026, 5, 1),
            summary="unrelated regulatory note",
            tags=["policy"],  # not in the seed's evidence_tags
        )
    )
    result = Analyst().run(AgentContext(signal_repo=repo, thesis_repo=repo, now=_NOW))
    assert result.theses == 0
    assert repo.list_theses(status=Status.candidate) == []
