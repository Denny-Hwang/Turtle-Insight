"""PostgreSQL + pgvector integration tests.

Skipped unless ``TI_TEST_PG_URL`` points at a Postgres with the pgvector
extension available (the CI ``pg-compat`` job provides one). Proves the storage
layer is Postgres-compatible and that pgvector nearest-neighbour search works.
"""

from __future__ import annotations

import os
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine

from turtle_insight.domain.thesis import (
    AssetLink,
    AssetRole,
    Evidence,
    Horizon,
    Layer,
    Status,
    Thesis,
)
from turtle_insight.services.embedding import HashingEmbedder
from turtle_insight.services.pipeline import analyze
from turtle_insight.services.rag_index import EVIDENCE_TABLE, index_evidence, search
from turtle_insight.storage.rag import VectorStore
from turtle_insight.storage.sqlite_repo import SqliteRepository

_PG_URL = os.environ.get("TI_TEST_PG_URL")
_NOW = datetime(2026, 6, 5)
pytestmark = pytest.mark.skipif(_PG_URL is None, reason="TI_TEST_PG_URL not set")


def _thesis() -> Thesis:
    return Thesis(
        id="T-2026-0100",
        layer=Layer.chain,
        horizon=Horizon.long,
        title="seed thesis",
        claim="a sufficiently long claim about demand",
        conviction=40,
        status=Status.active,
        assets=[AssetLink(market="KR", ticker="000660", role=AssetRole.primary)],
        evidence=[Evidence(date=date(2026, 5, 20), source="x", url="https://e/x", summary="s")],
        falsifiers=["demand growth stalls for two consecutive quarters"],
        risks=["cycle volatility"],
        created=datetime(2026, 6, 5),
    )


def test_postgres_thesis_round_trip() -> None:
    assert _PG_URL is not None
    repo = SqliteRepository.from_url(_PG_URL)
    thesis = _thesis()
    repo.upsert_thesis(thesis)
    assert repo.get_thesis(thesis.id) == thesis
    assert {t.id for t in repo.list_theses(status=Status.active)} == {"T-2026-0100"}


def test_pgvector_nearest_neighbour() -> None:
    assert _PG_URL is not None
    store = VectorStore(create_engine(_PG_URL), dim=3)
    store.ensure_schema()
    store.add("a", "signal-a", [1.0, 0.0, 0.0])
    store.add("b", "signal-b", [0.0, 1.0, 0.0])
    store.add("c", "signal-c", [0.0, 0.0, 1.0])

    neighbours = store.search([0.9, 0.1, 0.0], k=2)
    assert [n.id for n in neighbours] == ["a", "b"]
    assert neighbours[0].distance <= neighbours[1].distance


def test_rag_evidence_index_and_search() -> None:
    assert _PG_URL is not None
    repo = SqliteRepository.from_url(_PG_URL)
    analyze(repo, full=True, now=_NOW)  # populate theses + evidence

    embedder = HashingEmbedder(dim=64)
    store = VectorStore(create_engine(_PG_URL), dim=embedder.dim, table=EVIDENCE_TABLE)
    indexed = index_evidence(repo, store, embedder)
    assert indexed >= 1

    results = search(store, embedder, "HBM memory demand", k=3)
    assert results
    assert results[0].ref.startswith("T-2026-")
