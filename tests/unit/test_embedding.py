"""P19 unit tests: deterministic lexical embedder."""

from __future__ import annotations

import math

from turtle_insight.services.embedding import HashingEmbedder


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_embed_is_deterministic_with_fixed_dim() -> None:
    embedder = HashingEmbedder(dim=32)
    assert embedder.dim == 32
    v1 = embedder.embed("HBM memory demand")
    v2 = embedder.embed("HBM memory demand")
    assert v1 == v2
    assert len(v1) == 32


def test_embed_is_l2_normalized() -> None:
    vector = HashingEmbedder(dim=16).embed("memory power compute")
    assert math.isclose(math.sqrt(sum(x * x for x in vector)), 1.0, rel_tol=1e-9)


def test_embed_without_tokens_is_zero_vector() -> None:
    assert HashingEmbedder(dim=8).embed("!!! ...") == [0.0] * 8


def test_lexical_overlap_drives_similarity() -> None:
    embedder = HashingEmbedder(dim=256)
    a = embedder.embed("memory hbm demand rises")
    b = embedder.embed("demand for hbm memory rises")
    c = embedder.embed("electric power grid investment")
    assert _dot(a, b) > _dot(a, c)
