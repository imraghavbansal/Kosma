"""Deterministic mock embedding - a hash-based pseudo-vector, not a real
semantic embedding model (see PRODUCT-SPEC.md: "AI calls: Mock provider
only"). Computed synchronously on ingestion since it's a pure function with no
real latency, unlike a real embedding API call would have - there's nothing
here for a background job to usefully defer. Exists so pgvector's storage and
similarity-search path is real and exercised end to end, even though V1's
actual cohort matching uses structured filters, not this vector (see
change_engine/cohort.py's docstring for why)."""

import hashlib

from kosma_api.config import get_settings

settings = get_settings()


def mock_embed(text: str) -> list[float]:
    dim = settings.embedding_dim
    values: list[float] = []
    counter = 0
    while len(values) < dim:
        digest = hashlib.sha256(f"{text}:{counter}".encode("utf-8")).digest()
        for i in range(0, len(digest), 4):
            if len(values) >= dim:
                break
            chunk = digest[i : i + 4]
            as_int = int.from_bytes(chunk, "big", signed=False)
            values.append((as_int / 0xFFFFFFFF) * 2 - 1)  # normalize to [-1, 1]
        counter += 1
    return values
