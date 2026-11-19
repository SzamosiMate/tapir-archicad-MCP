"""Measure overlap and warm lookup time for identical batched search refinements."""

import argparse
import json
import os
from pathlib import Path
from statistics import median
from time import perf_counter

import tapir_archicad_mcp.model_configuration  # noqa: F401
from tapir_archicad_mcp.tools.custom.discovery_chain import chain_tool
from tapir_archicad_mcp.tools.custom.discovery_vectors import CACHE_ENV

QUERY_PAIRS = (
    (["navigator", "project"], ["placed drawings", "publisher set"], ["refresh linked drawings", "publish layouts"]),
    (["elements"], ["wall openings", "window geometry"], ["opening geometry", "window opening"]),
    (
        ["design_options", "navigator"],
        ["view settings", "design option combination"],
        ["saved view settings", "active variant"],
    ),
)


def probe(hybrid: bool) -> dict:
    started = perf_counter()
    discover = chain_tool(hybrid)
    startup_seconds = perf_counter() - started
    samples = []
    overlaps = []
    for groups, first_query, second_query in QUERY_PAIRS:
        first = discover(groups=groups, keywords=first_query)
        seen = {command.name for command in first.matches}
        fresh = discover(groups=groups, keywords=second_query)
        continued = discover(groups=groups, keywords=second_query, query_id=first.query_id)
        repeated_without_token = seen & {command.name for command in fresh.matches}
        repeated_with_token = seen & {command.name for command in continued.matches}
        assert not repeated_with_token
        overlaps.append(
            {
                "first": first_query,
                "refinement": second_query,
                "repeats_without_token": len(repeated_without_token),
                "repeats_with_token": len(repeated_with_token),
                "fresh_slots_without_token": len(fresh.matches) - len(repeated_without_token),
                "fresh_slots_with_token": len(continued.matches),
            }
        )
        for _ in range(7):
            started = perf_counter()
            discover(groups=groups, keywords=second_query, query_id=first.query_id)
            samples.append((perf_counter() - started) * 1000)

    compact = discover(groups=["navigator"])
    target = "navigator_publish_publisher_set"
    assert target in compact.names.splitlines()
    enlarged = discover(keywords=[target], query_id=compact.query_id)
    assert [command.name for command in enlarged.matches] == [target]
    assert discover(keywords=[target], query_id=enlarged.query_id).matches == []
    return {"startup_seconds": startup_seconds, "median_warm_batch_ms": median(samples), "overlap": overlaps}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vector-cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    os.environ[CACHE_ENV] = str(args.vector_cache.resolve())
    data = {name: probe(hybrid) for name, hybrid in (("chain-lexical", False), ("chain-hybrid", True))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2))
