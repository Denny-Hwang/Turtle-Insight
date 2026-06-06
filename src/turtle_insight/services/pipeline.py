"""``make analyze`` — run one analysis cycle against the configured DB.

Populates ``TI_DB_URL`` (default ``sqlite:///ti.db``) so the API and viewer have
data: by default the full macro -> trend -> chain cycle, persisting the active
seed graph and ingested signals. Uses the MVP fixture connectors (no live IO).
"""

from __future__ import annotations

import argparse
from datetime import datetime

from ..config.settings import get_settings
from ..connectors.base import Connector
from ..connectors.dart import DartConnector
from ..connectors.edgar import EdgarConnector
from ..connectors.fred import FredConnector
from ..connectors.market_api import MarketApiConnector
from ..connectors.news import NewsConnector
from ..services.orchestrator import CycleResult, Orchestrator
from ..storage.sqlite_repo import SqliteRepository


def default_connectors() -> list[Connector]:
    return [
        EdgarConnector(),
        DartConnector(),
        FredConnector(),
        MarketApiConnector(),
        NewsConnector(),
    ]


def analyze(
    repo: SqliteRepository, *, full: bool = True, now: datetime | None = None
) -> CycleResult:
    orchestrator = Orchestrator(
        signal_repo=repo,
        thesis_repo=repo,
        connectors=default_connectors(),
        now=now or datetime.now(),
    )
    return orchestrator.run_full_cycle() if full else orchestrator.run_cycle()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an analysis cycle into the configured DB.")
    parser.add_argument(
        "--mvp",
        action="store_true",
        help="run the MVP cycle (Scout->Analyst->RedTeam) instead of the full 3-layer cycle",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    repo = SqliteRepository.from_url(settings.ti_db_url)
    result = analyze(repo, full=not args.mvp)
    print(
        f"analyze: signals={result.signals} candidates={result.candidates} "
        f"reviews={result.reviews} activated={result.activated} -> {settings.ti_db_url}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
