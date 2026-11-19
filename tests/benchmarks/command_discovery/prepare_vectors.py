"""Download the optional embedding model and prepare a local catalogue index."""

import argparse
import os
from pathlib import Path
from time import perf_counter

import tapir_archicad_mcp.model_configuration  # noqa: F401
from tapir_archicad_mcp.tools.custom.discovery_vectors import CACHE_ENV, MODEL, prepare_index

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    os.environ[CACHE_ENV] = str(args.cache.resolve())
    started = perf_counter()
    index = prepare_index(download=True)
    print(f"Prepared {len(index.indices)} vectors with {MODEL} in {perf_counter() - started:.2f} s.")
