"""R4 — calibration scorecard report (eval-report).

Prints the track-record scorecard aggregated from persisted calibration scores
in the configured DB. Wired to ``make scorecard``; a weekly schedule can call
the same entry point.
"""

from __future__ import annotations

import json
from datetime import datetime

from ..config.settings import get_settings
from ..services.advisory import calibration_scorecard
from ..storage.sqlite_repo import SqliteRepository


def main() -> int:
    repo = SqliteRepository.from_url(get_settings().ti_db_url)
    scorecard = calibration_scorecard(repo, now=datetime.now())
    print(json.dumps(scorecard.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
