"""P7 integration tests: calibration persistence + Curator score_and_record."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from turtle_insight.agents.curator import Curator
from turtle_insight.domain.calibration import CalibrationScore, Outcome
from turtle_insight.domain.thesis import Evidence, Horizon, Layer, Status, Thesis
from turtle_insight.services.advisory import calibration_scorecard
from turtle_insight.storage.sqlite_repo import SqliteRepository

_NOW = datetime(2026, 6, 5)


def _repo(tmp_path: Path) -> SqliteRepository:
    return SqliteRepository.from_url(f"sqlite:///{tmp_path / 'ti.db'}")


def test_calibration_round_trip(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    score = CalibrationScore(
        thesis_id="T-2026-0001",
        conviction=80,
        realized=True,
        correct=True,
        brier=0.04,
        scored_at=datetime(2026, 6, 1),
    )
    repo.add_score(score)
    assert repo.list_scores() == [score]
    assert repo.list_scores(thesis_id="T-9999-9999") == []


def test_prediction_round_trip_is_upsert(tmp_path: Path) -> None:
    from turtle_insight.domain.calibration import Prediction

    repo = _repo(tmp_path)
    pred = Prediction(
        thesis_id="T-2026-0001",
        statement="demand rises",
        by_date=date(2030, 1, 1),
        conviction=60,
        created=_NOW,
    )
    repo.add_prediction(pred)
    repo.add_prediction(pred.model_copy(update={"conviction": 75}))
    rows = repo.list_predictions()
    assert len(rows) == 1  # keyed by thesis_id
    assert rows[0].conviction == 75


def test_curator_record_outcome_scores_stored_prediction(tmp_path: Path) -> None:
    from turtle_insight.domain.calibration import Prediction

    repo = _repo(tmp_path)
    prediction = Prediction(
        thesis_id="T-2026-0001",
        statement="demand rises",
        by_date=date(2030, 1, 1),
        conviction=80,
        created=_NOW,
    )
    result = Curator().record_outcome(repo, prediction, realized=True, now=datetime(2027, 1, 1))
    assert result.correct is True  # conviction 80 (>=50) and realized
    assert [s.thesis_id for s in repo.list_scores()] == ["T-2026-0001"]


def test_curator_score_and_record_persists(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    thesis = Thesis(
        id="T-2026-0001",
        layer=Layer.macro,
        horizon=Horizon.long,
        title="seed",
        claim="a sufficiently long claim about demand",
        conviction=80,
        status=Status.active,
        evidence=[Evidence(date=date(2026, 5, 1), source="x", url="https://e/x", summary="s")],
        falsifiers=["demand growth stalls"],
        created=_NOW,
    )
    outcome = Outcome(thesis_id="T-2026-0001", realized=True, observed_at=datetime(2027, 1, 1))
    Curator().score_and_record(repo, thesis, outcome, now=datetime(2027, 1, 1))

    card = calibration_scorecard(repo, now=_NOW)
    assert card.total == 1
    assert card.correct == 1
