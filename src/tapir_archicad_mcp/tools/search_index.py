import logging
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG
from tapir_archicad_mcp.tools.custom.models import ToolInfo

log = logging.getLogger()

# --- Configuration ---
INDEX_DIR = Path.home() / ".tapir_mcp"
INDEX_FILE = INDEX_DIR / "tool_index.faiss"
META_FILE = INDEX_DIR / "tool_index.meta.json"
MODEL_NAME = "all-MiniLM-L6-v2"
SEARCH_CANDIDATE_LIMIT = 10

MIN_ABSOLUTE_THRESHOLD = 0.35
RELATIVE_DROP_OFF_FACTOR = 0.90

# --- Module-level Globals ---
FAISS_INDEX: Optional[faiss.Index] = None
SENTENCE_MODEL: Optional[SentenceTransformer] = None


def _get_catalog_hash() -> str:
    """Creates a SHA256 hash of the tool catalog to detect changes."""
    serialized_catalog = json.dumps(TOOL_DISCOVERY_CATALOG, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized_catalog).hexdigest()


def _initialize_sentence_model() -> Optional[SentenceTransformer]:
    """Loads the sentence transformer model from disk."""
    try:
        return SentenceTransformer(MODEL_NAME)
    except Exception as e:
        log.error(f"Failed to load sentence-transformer model '{MODEL_NAME}'. Search is disabled. Error: {e}")
        return None


def _validate_and_load_existing_index(expected_hash: str) -> Optional[faiss.Index]:
    """Checks if a valid, up-to-date index exists on disk and loads it if so."""
    if not (META_FILE.exists() and INDEX_FILE.exists()):
        return None

    try:
        with open(META_FILE, 'r') as f:
            metadata = json.load(f)

        hash_matches = metadata.get("catalog_hash") == expected_hash
        model_matches = metadata.get("model_name") == MODEL_NAME

        if hash_matches and model_matches:
            log.info("Found valid index metadata. Loading existing index.")
            return faiss.read_index(str(INDEX_FILE))
        else:
            log.warning("Index metadata is stale (hash or model mismatch). Rebuilding is required.")
            return None
    except (json.JSONDecodeError, faiss.FaissException) as e:
        log.warning(f"Could not load existing index or metadata: {e}. Rebuilding is required.")
        return None


def _create_embedding_corpus() -> List[str]:
    """Generates the text corpus for embedding from the global tool catalog."""
    return [
        f"{tool['title']}: {tool['description']} Keywords: {tool['schema_keywords']}"
        for tool in TOOL_DISCOVERY_CATALOG
    ]


def _build_and_save_new_index(model: SentenceTransformer, catalog_hash: str) -> Optional[faiss.Index]:
    """Builds a new FAISS index from the tool catalog and saves it to disk."""
    log.warning("Building new FAISS index. This may take a moment on the first run...")
    try:
        corpus = _create_embedding_corpus()
        if not corpus:
            log.error("Tool discovery catalog is empty. Cannot build search index.")
            return None

        embeddings = model.encode(corpus, convert_to_tensor=False, show_progress_bar=True)
        embedding_dim = embeddings.shape[1]

        new_index = faiss.IndexFlatL2(embedding_dim)
        new_index.add(np.array(embeddings, dtype=np.float32))

        faiss.write_index(new_index, str(INDEX_FILE))
        with open(META_FILE, 'w') as f:
            json.dump({"catalog_hash": catalog_hash, "model_name": MODEL_NAME}, f)

        log.info("Semantic search index built and saved successfully.")
        return new_index
    except Exception as e:
        log.critical(f"CRITICAL: Failed to build and save FAISS index. Search is unavailable. Error: {e}")
        if INDEX_FILE.exists(): INDEX_FILE.unlink(missing_ok=True)
        if META_FILE.exists(): META_FILE.unlink(missing_ok=True)
        return None


def _calculate_top_score_relative_threshold(scores: List[float]) -> float:
    """
    Calculates a threshold based on a relative drop-off from the best score.
    """
    if not scores:
        return MIN_ABSOLUTE_THRESHOLD

    best_score = scores[0]
    relative_threshold = best_score * RELATIVE_DROP_OFF_FACTOR

    final_threshold = max(relative_threshold, MIN_ABSOLUTE_THRESHOLD)

    log.debug(f"Search scores: {[f'{s:.2f}' for s in scores]}")
    log.debug(
        f"Best score: {best_score:.2f}, RelativeThreshold: {relative_threshold:.2f}, FinalThreshold: {final_threshold:.2f}")
    return final_threshold


def _perform_keyword_fallback_search(query: str) -> List[ToolInfo]:
    """A simple keyword search for when the semantic index is unavailable."""
    log.warning(f"Performing keyword fallback search for query: '{query}'")
    query_lower = query.lower()
    results = []
    for tool_data in TOOL_DISCOVERY_CATALOG:
        if query_lower in tool_data["description"].lower() or query_lower in tool_data["name"].lower():
            results.append(ToolInfo(**tool_data))
    return results[:SEARCH_CANDIDATE_LIMIT]


def create_or_load_index():
    """
    Orchestrates the index setup process at server startup.
    It validates any existing index and rebuilds it if necessary.
    """
    global FAISS_INDEX, SENTENCE_MODEL
    log.info("Initializing semantic search index...")
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    catalog_hash = _get_catalog_hash()
    FAISS_INDEX = _validate_and_load_existing_index(catalog_hash)

    if FAISS_INDEX is None:
        model = _initialize_sentence_model()
        if model:
            FAISS_INDEX = _build_and_save_new_index(model, catalog_hash)

    if FAISS_INDEX and SENTENCE_MODEL is None:
        SENTENCE_MODEL = _initialize_sentence_model()


def search_tools(query: str) -> List[ToolInfo]:
    """
    Performs a semantic search and uses a top-score relative threshold to
    filter for the most relevant tools.
    """
    if not FAISS_INDEX or not SENTENCE_MODEL:
        return _perform_keyword_fallback_search(query)

    query_embedding = SENTENCE_MODEL.encode([query])
    distances, indices = FAISS_INDEX.search(np.array(query_embedding, dtype=np.float32), SEARCH_CANDIDATE_LIMIT)

    # Ensure scores are sorted descending by zipping with indices and sorting
    candidates = sorted(
        [(1 / (1 + dist), i) for dist, i in zip(distances[0], indices[0]) if dist >= 0],
        key=lambda x: x[0],
        reverse=True
    )

    if not candidates:
        return []

    candidate_scores = [score for score, index in candidates]
    final_threshold = _calculate_top_score_relative_threshold(candidate_scores)

    results = []
    for score, i in candidates:
        if score >= final_threshold:
            tool_data = TOOL_DISCOVERY_CATALOG[i]
            results.append(ToolInfo(**tool_data))

    if not results:
        log.warning(f"No tools found for query '{query}' above final threshold of {final_threshold:.2f}")

    return results