"""P2 integration tests: file store, SQLite repository, and file<->DB round-trip."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from turtle_insight.domain.signal import Signal
from turtle_insight.domain.thesis import (
    AssetLink,
    AssetRole,
    Evidence,
    Horizon,
    Layer,
    Status,
    Thesis,
)
from turtle_insight.storage.files import iter_theses, read_thesis, save_thesis, thesis_path
from turtle_insight.storage.sqlite_repo import SqliteRepository
from turtle_insight.storage.sync import check_round_trip, sync_to_db


def _thesis(status: Status = Status.candidate, tid: str = "T-2026-0001") -> Thesis:
    return Thesis(
        id=tid,
        layer=Layer.chain,
        horizon=Horizon.long,
        title="seed thesis",
        claim="a sufficiently long claim about the world",
        conviction=40,
        status=status,
        parents=["T-2026-0000"],
        assets=[AssetLink(market="KR", ticker="000660", role=AssetRole.primary)],
        evidence=[
            Evidence(
                date=date(2026, 5, 20),
                source="keynote",
                url="https://example.com/x",
                summary="short factual summary",
                weight=0.6,
            )
        ],
        falsifiers=["demand growth stalls for two consecutive quarters"],
        risks=["cycle volatility"],
        created=datetime(2026, 6, 5),
    )


def test_file_round_trip(tmp_path: Path) -> None:
    thesis = _thesis()
    path = save_thesis(thesis, base_dir=tmp_path)
    assert path == thesis_path(thesis, tmp_path)
    assert path.parent.name == "candidate"
    assert read_thesis(path) == thesis


def test_status_change_moves_file(tmp_path: Path) -> None:
    thesis = _thesis(status=Status.candidate)
    candidate_path = save_thesis(thesis, base_dir=tmp_path)
    assert candidate_path.exists()

    promoted = thesis.model_copy(update={"status": Status.active})
    active_path = save_thesis(promoted, base_dir=tmp_path)

    assert active_path.parent.name == "active"
    assert active_path.exists()
    assert not candidate_path.exists()  # moved, not duplicated
    assert [t.id for t in iter_theses(tmp_path)] == ["T-2026-0001"]


def test_db_round_trip(tmp_path: Path) -> None:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    thesis = _thesis()
    repo.upsert_thesis(thesis)
    assert repo.get_thesis(thesis.id) == thesis


def test_upsert_is_idempotent(tmp_path: Path) -> None:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    thesis = _thesis()
    repo.upsert_thesis(thesis)
    repo.upsert_thesis(thesis.model_copy(update={"conviction": 55}))
    rows = repo.list_theses()
    assert len(rows) == 1
    assert rows[0].conviction == 55


def test_list_theses_filters(tmp_path: Path) -> None:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    repo.upsert_thesis(_thesis(status=Status.candidate, tid="T-2026-0001"))
    repo.upsert_thesis(_thesis(status=Status.active, tid="T-2026-0002"))
    assert {t.id for t in repo.list_theses(status=Status.active)} == {"T-2026-0002"}
    assert {t.id for t in repo.list_theses(ticker="000660")} == {"T-2026-0001", "T-2026-0002"}
    assert repo.list_theses(ticker="ZZZ") == []


def test_signal_round_trip(tmp_path: Path) -> None:
    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    signal = Signal(
        id="S-1",
        source="news",
        url="https://example.com/a",
        published_at=datetime(2026, 6, 1, 9, 0),
        summary="link + short summary only",
        tickers=["000660"],
        tags=["memory", "hbm"],
    )
    repo.upsert_signal(signal)
    assert repo.get_signal("S-1") == signal
    assert {s.id for s in repo.list_signals(tag="hbm")} == {"S-1"}
    assert repo.list_signals(tag="absent") == []


def test_sync_and_check_round_trip(tmp_path: Path) -> None:
    base = tmp_path / "theses"
    save_thesis(_thesis(tid="T-2026-0001"), base_dir=base)
    save_thesis(_thesis(status=Status.draft, tid="T-2026-0002"), base_dir=base)

    repo = SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")
    assert sync_to_db(repo, base_dir=base) == 2
    assert {t.id for t in repo.list_theses()} == {"T-2026-0001", "T-2026-0002"}
    assert check_round_trip(base_dir=base) == []
