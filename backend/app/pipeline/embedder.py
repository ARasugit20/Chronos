# WHY: Text embeddings for theme similarity when regex confidence is low.

from __future__ import annotations

import hashlib

import numpy as np
import structlog

logger = structlog.get_logger(__name__)
_MODEL = None


def _hash_embed(text: str, dim: int = 32) -> np.ndarray:
    digest = hashlib.sha256(text.encode()).digest()
    values = [digest[i % len(digest)] / 255.0 for i in range(dim)]
    return np.array(values, dtype=np.float32)


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("embedder.loaded", model="all-MiniLM-L6-v2")
    except Exception as exc:  # noqa: BLE001
        logger.warning("embedder.fallback_hash", error=str(exc))
        _MODEL = "hash"
    return _MODEL


def embed(text: str) -> np.ndarray:
    model = _load_model()
    if model == "hash":
        return _hash_embed(text)
    return np.array(model.encode(text), dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
