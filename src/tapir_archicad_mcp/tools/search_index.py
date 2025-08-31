import logging
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG
from tapir_archicad_mcp.tools.custom.models import ToolInfo

log = logging.getLogger()

# --- Configuration ---
INDEX_DIR = Path.home() / ".tapir_mcp"
INDEX_FILE = INDEX_DIR / "tool_index.faiss"
MODEL_NAME = "all-MiniLM-L6-v2"

# --- NEW: Configuration for Search Results ---
# The maximum number of candidates to pull from the index.
SEARCH_CANDIDATE_LIMIT = 10
# The minimum similarity score (0.0 to 1.0) required to include a result.
# This is our "adjacency" filter. A higher value means a stricter search.
SIMILARITY_THRESHOLD = 0.55

# --- In-Memory Globals ---
FAISS_INDEX: faiss.Index | None = None
SENTENCE_MODEL: SentenceTransformer | None = None


# ... (create_or_load_index function remains exactly the same) ...
def create_or_load_index():
    """
    Initializes the sentence transformer model and FAISS index.
    If a pre-built index exists, it's loaded. Otherwise, a new one is
    created from the tool catalog and saved for future use.
    This function is called once at server startup.
    """
    global FAISS_INDEX, SENTENCE_MODEL

    log.info("Initializing semantic search index...")

    # Ensure the storage directory exists
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Load the sentence transformer model
    try:
        SENTENCE_MODEL = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        log.error(
            f"Failed to load sentence-transformer model '{MODEL_NAME}'. Semantic search will be disabled. Error: {e}")
        return

    if INDEX_FILE.exists():
        log.info(f"Loading existing FAISS index from {INDEX_FILE}")
        try:
            FAISS_INDEX = faiss.read_index(str(INDEX_FILE))
            log.info("Semantic search index loaded successfully.")
        except Exception as e:
            log.error(f"Failed to load FAISS index from {INDEX_FILE}. Error: {e}")
            # Invalidate to trigger recreation if needed
            FAISS_INDEX = None

    else:
        log.warning("FAISS index not found. Building a new one. This may take a moment on first run...")
        try:
            # 1. Prepare the text data for embedding
            # We embed a combination of the name and description for better context
            corpus = [f"{tool['title']}: {tool['description']}" for tool in TOOL_DISCOVERY_CATALOG]

            if not corpus:
                log.error("Tool discovery catalog is empty. Cannot build search index.")
                return

            # 2. Generate embeddings
            log.info(f"Generating embeddings for {len(corpus)} tools...")
            embeddings = SENTENCE_MODEL.encode(corpus, convert_to_tensor=False, show_progress_bar=True)

            # 3. Create and populate the FAISS index
            embedding_dim = embeddings.shape[1]
            FAISS_INDEX = faiss.IndexFlatL2(embedding_dim)  # Using L2 distance for similarity
            FAISS_INDEX.add(np.array(embeddings, dtype=np.float32))

            # 4. Save the index to disk for future runs
            log.info(f"Saving new index to {INDEX_FILE}...")
            faiss.write_index(FAISS_INDEX, str(INDEX_FILE))
            log.info("Semantic search index built and saved successfully.")

        except Exception as e:
            log.critical(
                f"CRITICAL: Failed to build and save the FAISS index. Semantic search will be unavailable. Error: {e}")
            FAISS_INDEX = None


def search_tools(query: str) -> list[ToolInfo]:
    """
    Performs a semantic search for tools based on the user's query.
    Returns a list of the most relevant tools that meet the similarity threshold.
    """
    if not FAISS_INDEX or not SENTENCE_MODEL:
        log.warning("Search is unavailable. Index or model not initialized.")
        # Fallback keyword search remains the same
        query_lower = query.lower()
        results = []
        for tool_data in TOOL_DISCOVERY_CATALOG:
            if query_lower in tool_data["description"].lower() or query_lower in tool_data["name"].lower():
                results.append(ToolInfo(**tool_data))
        return results[:SEARCH_CANDIDATE_LIMIT]

    # 1. Create a vector embedding for the search query
    query_embedding = SENTENCE_MODEL.encode([query])
    query_embedding = np.array(query_embedding, dtype=np.float32)

    # 2. Search the FAISS index for the k nearest neighbors
    # D = distances (L2 distance), I = indices of the matching vectors
    distances, indices = FAISS_INDEX.search(query_embedding, SEARCH_CANDIDATE_LIMIT)

    # 3. Filter results based on the similarity threshold
    results = []
    for dist, i in zip(distances[0], indices[0]):
        if i == -1:  # FAISS returns -1 if there are fewer items than the limit
            continue

        # Convert L2 distance to a more intuitive 0-1 similarity score.
        # This formula is a simple way to invert the distance.
        similarity = 1 / (1 + dist)

        if similarity >= SIMILARITY_THRESHOLD:
            tool_data = TOOL_DISCOVERY_CATALOG[i]
            # Optional: log the score for debugging
            log.debug(f"Found tool '{tool_data['name']}' with similarity score: {similarity:.2f}")
            results.append(ToolInfo(**tool_data))

    if not results:
        log.warning(f"No tools found for query '{query}' above similarity threshold of {SIMILARITY_THRESHOLD}")

    return results