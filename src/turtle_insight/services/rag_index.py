"""RAG: index thesis evidence into the pgvector store and search it.

Evidence summaries (link + short text only) are embedded and stored; a text
query is embedded the same way and matched by nearest-neighbour. Postgres only
(VectorStore). The embedder is injected (deterministic lexical default).
"""

from __future__ import annotations

from ..storage.rag import Neighbor, VectorStore
from ..storage.repository import ThesisRepository
from .embedding import Embedder

EVIDENCE_TABLE = "evidence_embeddings"


def index_evidence(repo: ThesisRepository, store: VectorStore, embedder: Embedder) -> int:
    """Embed and upsert every thesis evidence item; returns the count indexed."""
    store.ensure_schema()
    count = 0
    for thesis in repo.list_theses():
        for index, evidence in enumerate(thesis.evidence):
            entry_id = evidence.signal_id or f"{thesis.id}#{index}"
            store.add(entry_id, thesis.id, embedder.embed(evidence.summary))
            count += 1
    return count


def search(store: VectorStore, embedder: Embedder, query: str, *, k: int = 5) -> list[Neighbor]:
    return store.search(embedder.embed(query), k=k)
