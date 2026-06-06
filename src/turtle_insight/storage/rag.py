"""pgvector-backed similarity search over evidence/signal embeddings (Postgres only).

The DB image provides the ``vector`` extension (pgvector). Vectors are passed as
text and cast with ``::vector`` in SQL, so no extra Python driver dependency is
needed beyond psycopg. Embeddings are supplied by the caller (an external
embedding model); this store only persists and searches them — it is the
``v1+`` RAG substrate referenced in ADR-0005.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Engine, text


@dataclass(frozen=True)
class Neighbor:
    id: str
    ref: str
    distance: float


def _to_vector_literal(embedding: Sequence[float]) -> str:
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


class VectorStore:
    """Stores ``(id, ref, embedding)`` rows and does nearest-neighbour search."""

    def __init__(self, engine: Engine, *, dim: int) -> None:
        self._engine = engine
        self._dim = dim

    def ensure_schema(self) -> None:
        with self._engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS embeddings ("
                    "id text PRIMARY KEY, ref text NOT NULL, "
                    f"embedding vector({self._dim}) NOT NULL)"
                )
            )

    def add(self, id: str, ref: str, embedding: Sequence[float]) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO embeddings (id, ref, embedding) "
                    "VALUES (:id, :ref, (:emb)::vector) "
                    "ON CONFLICT (id) DO UPDATE SET ref = excluded.ref, "
                    "embedding = excluded.embedding"
                ),
                {"id": id, "ref": ref, "emb": _to_vector_literal(embedding)},
            )

    def search(self, embedding: Sequence[float], *, k: int = 5) -> list[Neighbor]:
        with self._engine.begin() as conn:
            rows = conn.execute(
                text(
                    "SELECT id, ref, embedding <-> (:emb)::vector AS distance "
                    "FROM embeddings ORDER BY distance LIMIT :k"
                ),
                {"emb": _to_vector_literal(embedding), "k": k},
            ).all()
        return [Neighbor(id=row.id, ref=row.ref, distance=float(row.distance)) for row in rows]
