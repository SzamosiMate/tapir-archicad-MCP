"""Optional CPU semantic ranking for the chained discovery experiment."""

import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
from fastembed import TextEmbedding

from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSIONS = 384
MIN_COSINE = 0.30
CACHE_ENV = "TAPIR_DISCOVERY_VECTOR_CACHE"


def _normalized(embeddings):
    rows = np.asarray(list(embeddings), dtype=np.float32)
    return rows / np.maximum(np.linalg.norm(rows, axis=1, keepdims=True), np.finfo(np.float32).tiny)


class VectorIndex:
    def __init__(self, model: TextEmbedding, catalog_names: list[str], embeddings: np.ndarray):
        self.model = model
        self.indices = {name: index for index, name in enumerate(catalog_names)}
        self.embeddings = embeddings

    def ranks(self, queries: list[str], scope: list[str]) -> list[list[str]]:
        queries_vector = _normalized(self.model.query_embed(queries))
        scores = queries_vector @ self.embeddings[[self.indices[name] for name in scope]].T
        return [
            [
                name
                for _, name in sorted(
                    (-float(score), name) for name, score in zip(scope, row, strict=True) if score >= MIN_COSINE
                )
            ]
            for row in scores
        ]


def prepare_index(*, download: bool = False) -> VectorIndex:
    cache = Path(os.environ.get(CACHE_ENV, Path.home() / ".tapir_mcp" / "discovery_vectors"))
    cache.mkdir(parents=True, exist_ok=True)
    try:
        model = TextEmbedding(MODEL, cache_dir=str(cache / "models"), threads=2, local_files_only=not download)
    except (OSError, ValueError) as error:
        raise RuntimeError(
            "Prepare the hybrid model with the command-discovery benchmark's prepare_vectors.py."
        ) from error

    items = list(TOOL_DISCOVERY_CATALOG.values())
    corpus = [f"{item['name'].replace('_', ' ')}. {item['title']}. {item['description']}" for item in items]
    key = hashlib.sha256(json.dumps([MODEL, version("fastembed"), corpus], ensure_ascii=False).encode()).hexdigest()
    path = cache / f"{key}.npy"
    try:
        vectors = np.load(path, allow_pickle=False)
        if vectors.shape != (len(items), DIMENSIONS) or vectors.dtype != np.float32:
            raise ValueError("Cached vector index has unexpected dimensions or dtype")
    except (OSError, ValueError):
        vectors = _normalized(model.passage_embed(corpus, batch_size=32))
        with NamedTemporaryFile(dir=cache, suffix=".npy", delete=False) as temporary:
            scratch = Path(temporary.name)
        try:
            np.save(scratch, vectors, allow_pickle=False)
            scratch.replace(path)
        finally:
            scratch.unlink(missing_ok=True)
    return VectorIndex(model, [item["name"] for item in items], vectors)
