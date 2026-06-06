"""SQLite repository implementation (MVP) over the SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, selectinload

from ..domain.calibration import CalibrationScore, Prediction
from ..domain.signal import Signal
from ..domain.thesis import (
    AssetLink,
    AssetRole,
    Evidence,
    Horizon,
    Layer,
    ReviewCadence,
    Status,
    Thesis,
)
from .repository import Repository
from .sql_models import (
    AssetRow,
    Base,
    CalibrationRow,
    EvidenceRow,
    PredictionRow,
    SignalRow,
    ThesisRow,
)


def _to_thesis_row(thesis: Thesis) -> ThesisRow:
    return ThesisRow(
        id=thesis.id,
        layer=thesis.layer.value,
        horizon=thesis.horizon.value,
        status=thesis.status.value,
        conviction=thesis.conviction,
        title=thesis.title,
        claim=thesis.claim,
        review_cadence=thesis.review_cadence.value,
        created=thesis.created,
        last_reviewed=thesis.last_reviewed,
        parents=list(thesis.parents),
        children=list(thesis.children),
        falsifiers=list(thesis.falsifiers),
        risks=list(thesis.risks),
        assets=[
            AssetRow(market=a.market, ticker=a.ticker, role=a.role.value) for a in thesis.assets
        ],
        evidence=[
            EvidenceRow(
                date=e.date,
                source=e.source,
                url=e.url,
                summary=e.summary,
                weight=e.weight,
                signal_id=e.signal_id,
            )
            for e in thesis.evidence
        ],
    )


def _to_thesis(row: ThesisRow) -> Thesis:
    return Thesis(
        id=row.id,
        layer=Layer(row.layer),
        horizon=Horizon(row.horizon),
        status=Status(row.status),
        conviction=row.conviction,
        title=row.title,
        claim=row.claim,
        review_cadence=ReviewCadence(row.review_cadence),
        created=row.created,
        last_reviewed=row.last_reviewed,
        parents=list(row.parents),
        children=list(row.children),
        falsifiers=list(row.falsifiers),
        risks=list(row.risks),
        assets=[
            AssetLink(market=a.market, ticker=a.ticker, role=AssetRole(a.role)) for a in row.assets
        ],
        evidence=[
            Evidence(
                date=e.date,
                source=e.source,
                url=e.url,
                summary=e.summary,
                weight=e.weight,
                signal_id=e.signal_id,
            )
            for e in row.evidence
        ],
    )


def _to_signal_row(signal: Signal) -> SignalRow:
    return SignalRow(
        id=signal.id,
        source=signal.source,
        url=signal.url,
        published_at=signal.published_at,
        summary=signal.summary,
        raw_ref=signal.raw_ref,
        tickers=list(signal.tickers),
        tags=list(signal.tags),
    )


def _to_signal(row: SignalRow) -> Signal:
    return Signal(
        id=row.id,
        source=row.source,
        url=row.url,
        published_at=row.published_at,
        summary=row.summary,
        raw_ref=row.raw_ref,
        tickers=list(row.tickers),
        tags=list(row.tags),
    )


def _to_calibration_row(score: CalibrationScore) -> CalibrationRow:
    return CalibrationRow(
        thesis_id=score.thesis_id,
        conviction=score.conviction,
        realized=score.realized,
        correct=score.correct,
        brier=score.brier,
        scored_at=score.scored_at,
    )


def _to_calibration_score(row: CalibrationRow) -> CalibrationScore:
    return CalibrationScore(
        thesis_id=row.thesis_id,
        conviction=row.conviction,
        realized=row.realized,
        correct=row.correct,
        brier=row.brier,
        scored_at=row.scored_at,
    )


def _to_prediction_row(prediction: Prediction) -> PredictionRow:
    return PredictionRow(
        thesis_id=prediction.thesis_id,
        statement=prediction.statement,
        by_date=prediction.by_date,
        conviction=prediction.conviction,
        created=prediction.created,
    )


def _to_prediction(row: PredictionRow) -> Prediction:
    return Prediction(
        thesis_id=row.thesis_id,
        statement=row.statement,
        by_date=row.by_date,
        conviction=row.conviction,
        created=row.created,
    )


class SqliteRepository(Repository):
    """Thesis + signal + calibration repository backed by a SQLAlchemy engine."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        Base.metadata.create_all(engine)

    @classmethod
    def from_url(cls, url: str) -> SqliteRepository:
        return cls(create_engine(url))

    # --- ThesisRepository ---
    def upsert_thesis(self, thesis: Thesis) -> None:
        with Session(self._engine) as session:
            existing = session.get(ThesisRow, thesis.id)
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(_to_thesis_row(thesis))
            session.commit()

    def get_thesis(self, thesis_id: str) -> Thesis | None:
        with Session(self._engine) as session:
            row = session.get(
                ThesisRow,
                thesis_id,
                options=[selectinload(ThesisRow.assets), selectinload(ThesisRow.evidence)],
            )
            return _to_thesis(row) if row is not None else None

    def list_theses(
        self,
        *,
        status: Status | None = None,
        layer: str | None = None,
        ticker: str | None = None,
    ) -> list[Thesis]:
        stmt = select(ThesisRow).options(
            selectinload(ThesisRow.assets), selectinload(ThesisRow.evidence)
        )
        if status is not None:
            stmt = stmt.where(ThesisRow.status == status.value)
        if layer is not None:
            stmt = stmt.where(ThesisRow.layer == layer)
        if ticker is not None:
            stmt = stmt.where(ThesisRow.assets.any(AssetRow.ticker == ticker))
        with Session(self._engine) as session:
            return [_to_thesis(row) for row in session.scalars(stmt).all()]

    # --- SignalRepository ---
    def upsert_signal(self, signal: Signal) -> None:
        with Session(self._engine) as session:
            existing = session.get(SignalRow, signal.id)
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(_to_signal_row(signal))
            session.commit()

    def get_signal(self, signal_id: str) -> Signal | None:
        with Session(self._engine) as session:
            row = session.get(SignalRow, signal_id)
            return _to_signal(row) if row is not None else None

    def list_signals(self, *, tag: str | None = None) -> list[Signal]:
        with Session(self._engine) as session:
            signals = [_to_signal(row) for row in session.scalars(select(SignalRow)).all()]
        if tag is not None:
            signals = [s for s in signals if tag in s.tags]
        return signals

    # --- CalibrationRepository ---
    def add_score(self, score: CalibrationScore) -> None:
        with Session(self._engine) as session:
            session.add(_to_calibration_row(score))
            session.commit()

    def list_scores(self, *, thesis_id: str | None = None) -> list[CalibrationScore]:
        stmt = select(CalibrationRow).order_by(CalibrationRow.scored_at, CalibrationRow.id)
        if thesis_id is not None:
            stmt = stmt.where(CalibrationRow.thesis_id == thesis_id)
        with Session(self._engine) as session:
            return [_to_calibration_score(row) for row in session.scalars(stmt).all()]

    def add_prediction(self, prediction: Prediction) -> None:
        with Session(self._engine) as session:
            existing = session.get(PredictionRow, prediction.thesis_id)
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(_to_prediction_row(prediction))
            session.commit()

    def list_predictions(self) -> list[Prediction]:
        stmt = select(PredictionRow).order_by(PredictionRow.thesis_id)
        with Session(self._engine) as session:
            return [_to_prediction(row) for row in session.scalars(stmt).all()]
