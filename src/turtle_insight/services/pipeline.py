"""``make analyze`` — run one analysis cycle against the configured DB.

Populates ``TI_DB_URL`` (default ``sqlite:///ti.db``) so the API and viewer have
data: by default the full macro -> trend -> chain cycle, persisting the active
seed graph and ingested signals. Uses the MVP fixture connectors (no live IO).

With ``--write-files`` it also exports every thesis to the canonical
``theses/<status>/<id>.yaml`` store (content-as-code, ADR-0004), so ``make
validate``/``sync-check`` and git cover them.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from ..config.settings import get_settings
from ..connectors.base import Connector
from ..connectors.dart import DartConnector
from ..connectors.edgar import EdgarConnector
from ..connectors.fred import FredConnector
from ..connectors.market_api import MarketApiConnector
from ..connectors.news import NewsConnector
from ..services.orchestrator import CycleResult, Orchestrator
from ..storage.files import THESES_DIR, save_thesis
from ..storage.repository import Repository
from ..storage.sqlite_repo import SqliteRepository


def default_connectors() -> list[Connector]:
    return [
        EdgarConnector(),
        DartConnector(),
        FredConnector(),
        MarketApiConnector(),
        NewsConnector(),
    ]


def export_theses(repo: Repository, base_dir: Path = THESES_DIR) -> int:
    """Write every thesis in the DB to the canonical ``theses/<status>/`` store."""
    count = 0
    for thesis in repo.list_theses():
        save_thesis(thesis, base_dir)
        count += 1
    return count


def analyze(
    repo: Repository,
    *,
    full: bool = True,
    now: datetime | None = None,
    write_files: bool = False,
    base_dir: Path = THESES_DIR,
) -> CycleResult:
    orchestrator = Orchestrator(
        signal_repo=repo,
        thesis_repo=repo,
        connectors=default_connectors(),
        now=now or datetime.now(),
    )
    result = orchestrator.run_full_cycle() if full else orchestrator.run_cycle()
    if write_files:
        export_theses(repo, base_dir)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an analysis cycle into the configured DB.")
    parser.add_argument(
        "--mvp",
        action="store_true",
        help="run the MVP cycle (Scout->Analyst->RedTeam) instead of the full 3-layer cycle",
    )
    parser.add_argument(
        "--write-files",
        action="store_true",
        help="also export theses to the canonical theses/<status>/ YAML store",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    repo = SqliteRepository.from_url(settings.ti_db_url)
    result = analyze(repo, full=not args.mvp, write_files=args.write_files)
    suffix = " (+files)" if args.write_files else ""
    print(
        f"analyze: signals={result.signals} candidates={result.candidates} "
        f"reviews={result.reviews} activated={result.activated} -> {settings.ti_db_url}{suffix}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
