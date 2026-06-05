"""SQLAlchemy ORM models (MVP SQLite; shared with Postgres in v1+).

The DB is a query/index over the canonical YAML store (content-as-code,
ADR-0004). For MVP a thesis row holds the full thesis (lossless round-trip):
``parents``/``children``/``falsifiers``/``risks`` as JSON, ``assets`` and
``evidence`` as child tables. See ADR-0006.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ThesisRow(Base):
    __tablename__ = "theses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    layer: Mapped[str] = mapped_column(String)
    horizon: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    conviction: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column(String)
    claim: Mapped[str] = mapped_column(String)
    review_cadence: Mapped[str] = mapped_column(String)
    created: Mapped[datetime] = mapped_column()
    last_reviewed: Mapped[date | None] = mapped_column(default=None)
    parents: Mapped[list[str]] = mapped_column(JSON, default=list)
    children: Mapped[list[str]] = mapped_column(JSON, default=list)
    falsifiers: Mapped[list[str]] = mapped_column(JSON, default=list)
    risks: Mapped[list[str]] = mapped_column(JSON, default=list)

    assets: Mapped[list[AssetRow]] = relationship(
        back_populates="thesis", cascade="all, delete-orphan", order_by="AssetRow.id"
    )
    evidence: Mapped[list[EvidenceRow]] = relationship(
        back_populates="thesis", cascade="all, delete-orphan", order_by="EvidenceRow.id"
    )


class AssetRow(Base):
    __tablename__ = "thesis_assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thesis_id: Mapped[str] = mapped_column(ForeignKey("theses.id", ondelete="CASCADE"))
    market: Mapped[str] = mapped_column(String)
    ticker: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)

    thesis: Mapped[ThesisRow] = relationship(back_populates="assets")


class EvidenceRow(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thesis_id: Mapped[str] = mapped_column(ForeignKey("theses.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column()
    source: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    weight: Mapped[float] = mapped_column()
    signal_id: Mapped[str | None] = mapped_column(default=None)

    thesis: Mapped[ThesisRow] = relationship(back_populates="evidence")


class SignalRow(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    published_at: Mapped[datetime] = mapped_column()
    summary: Mapped[str] = mapped_column(String)
    raw_ref: Mapped[str | None] = mapped_column(default=None)
    tickers: Mapped[list[str]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
