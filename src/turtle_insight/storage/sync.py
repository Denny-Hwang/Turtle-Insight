"""``make sync`` — one-way file -> DB synchronization (+ a CI consistency check).

Reads the canonical ``theses/<status>/*.yaml`` store and upserts each thesis
into the DB index. With ``--check`` it verifies the files are faithfully
round-trippable through the DB (used by CI) using a throwaway database, so no
state is persisted.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from ..config.settings import get_settings
from .files import THESES_DIR, iter_theses
from .sqlite_repo import SqliteRepository


def sync_to_db(repo: SqliteRepository, base_dir: Path = THESES_DIR) -> int:
    count = 0
    for thesis in iter_theses(base_dir):
        repo.upsert_thesis(thesis)
        count += 1
    return count


def check_round_trip(base_dir: Path = THESES_DIR) -> list[str]:
    """Sync files to a throwaway DB and confirm read-back equals the files."""
    file_theses = {t.id: t for t in iter_theses(base_dir)}
    with tempfile.TemporaryDirectory() as tmp:
        repo = SqliteRepository.from_url(f"sqlite:///{Path(tmp) / 'check.db'}")
        for thesis in file_theses.values():
            repo.upsert_thesis(thesis)
        db_theses = {t.id: t for t in repo.list_theses()}

    errors: list[str] = []
    for tid, thesis in file_theses.items():
        if tid not in db_theses:
            errors.append(f"{tid}: present in files but missing from DB")
        elif db_theses[tid] != thesis:
            errors.append(f"{tid}: file/DB mismatch after round-trip")
    errors.extend(
        f"{tid}: present in DB but missing from files" for tid in db_theses - file_theses.keys()
    )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync theses files into the DB index.")
    parser.add_argument(
        "--check", action="store_true", help="verify file<->DB round-trip consistency only"
    )
    args = parser.parse_args(argv)

    if args.check:
        errors = check_round_trip()
        if errors:
            print("sync --check: FAILED", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1
        print("sync --check: OK — files are DB-round-trippable.")
        return 0

    settings = get_settings()
    repo = SqliteRepository.from_url(settings.ti_db_url)
    count = sync_to_db(repo)
    print(f"sync: upserted {count} thesis file(s) into {settings.ti_db_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
