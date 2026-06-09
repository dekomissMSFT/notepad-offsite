"""Sentence-transformers wrapper. Lazy-loaded to keep startup fast."""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .config import settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.model_name)


def embed(text: str) -> np.ndarray:
    vec = _model().encode([text], normalize_embeddings=True)[0]
    return np.asarray(vec, dtype=np.float32)


def embed_many(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)
    return np.asarray(
        _model().encode(texts, normalize_embeddings=True),
        dtype=np.float32,
    )
