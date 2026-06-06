"""Deterministic lexical embedder (placeholder for a real embedding model).

Hashes tokens into a fixed-dimension bag-of-words vector (L2-normalized), so
identical text yields identical vectors and lexical overlap drives cosine
similarity. This is a deterministic substrate for the pgvector RAG path
(ADR-0005/0008); a real semantic embedder (same ``Embedder`` protocol) is
injected later without changing callers.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

_TOKEN = re.compile(r"[0-9a-z]+")


class Embedder(Protocol):
    @property
    def dim(self) -> int: ...

    def embed(self, text: str) -> list[float]: ...


class HashingEmbedder:
    """Token-hashing bag-of-words embedder (deterministic, lexical)."""

    def __init__(self, dim: int = 64) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dim
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            vector[int.from_bytes(digest, "big") % self._dim] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm > 0.0:
            vector = [value / norm for value in vector]
        return vector
