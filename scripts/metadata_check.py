"""Validate reviewed command metadata against the exact release schemas."""

import ast
import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

from tapir_archicad_mcp.metadata_types import CommandMetadata, Presentation


def check_duplicate_identities() -> None:
    source = Path(__file__).resolve().parents[1] / "src" / "tapir_archicad_mcp" / "command_metadata.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    mapping = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "COMMAND_METADATA"
    )
    keys = [ast.literal_eval(key) for key in mapping.keys]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate command identities in COMMAND_METADATA.")


def _references(node) -> Iterator[str]:
    if isinstance(node, dict):
        if "$ref" in node:
            yield node["$ref"]
        for key, child in node.items():
            if key != "$defs":
                yield from _references(child)
    elif isinstance(node, list):
        for child in node:
            yield from _references(child)


def _resolve(document: dict, pointer: str) -> dict:
    node = document
    for key in pointer.removeprefix("#/").split("/"):
        node = node[key.replace("~1", "/").replace("~0", "~")]
    return node


def review_fingerprint(name: str, command: dict, document: dict) -> str:
    """Include the command description, both models and every referenced definition."""
    roots = [document["$defs"].get(name + suffix) for suffix in ("Parameters", "Result")]
    closure = {}
    pending = list(_references(roots))
    while pending:
        pointer = pending.pop()
        if pointer not in closure:
            closure[pointer] = _resolve(document, pointer)
            pending.extend(_references(closure[pointer]))
    reviewed = [command["description"], command["group"], roots, closure]
    serialized = json.dumps(reviewed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:20]


def _variants(node: dict, document: dict) -> Iterator[dict]:
    if "$ref" in node:
        yield from _variants(_resolve(document, node["$ref"]), document)
    elif "anyOf" in node or "oneOf" in node:
        for branch in node.get("anyOf", node.get("oneOf")):
            yield from _variants(branch, document)
    elif node.get("type") != "null":
        yield node


def _fields(model: dict, field: str, document: dict) -> list[dict]:
    return [
        variant["properties"][field] for variant in _variants(model, document) if field in variant.get("properties", {})
    ]


def _array_items(model: dict, field: str, document: dict) -> list[dict]:
    fields = _fields(model, field, document)
    variants = [variant for field_schema in fields for variant in _variants(field_schema, document)]
    if not variants or any(item.get("type") != "array" for item in variants):
        raise ValueError(f"Expected a list at {field!r}.")
    return [item["items"] for item in variants]


def _items(node: dict, document: dict) -> list[dict]:
    resolved = _resolve(document, node["$ref"]) if "$ref" in node else node
    branches = resolved.get("anyOf", resolved.get("oneOf"))
    if branches is not None:
        return [option for branch in branches for option in _items(branch, document)]
    return [node]


def _name(node: dict) -> str:
    return node.get("$ref", "").rsplit("/", 1)[-1]


def _validate_errors(items: list[dict], errors: tuple[str, ...], document: dict):
    alternatives = [branch for item in items for branch in _items(item, document)]
    declared = set(errors)
    if not declared <= {_name(branch) for branch in alternatives}:
        raise ValueError(f"Stale item error models {errors!r}.")
    actual = {_name(branch) for branch in alternatives if _fields(branch, "error", document) and _name(branch)}
    if actual != declared:
        raise ValueError(f"Expected declared item error models {sorted(actual)!r}, got {errors!r}.")


def validate_command(name: str, command: dict, document: dict, metadata: CommandMetadata) -> None:
    if not isinstance(metadata, CommandMetadata) or not isinstance(metadata.presentation, Presentation):
        raise ValueError("Expected typed command metadata and presentation.")
    if metadata.adapter is not None:
        raise ValueError("Matrix adapters belong to handwritten commands.")
    definitions = document["$defs"]
    parameters = definitions.get(name + "Parameters", {})
    output = definitions.get(name + "Result", {})
    if contract := metadata.positional:
        if contract.input_field in contract.shared_inputs or len(set(contract.shared_inputs)) != len(
            contract.shared_inputs
        ):
            raise ValueError("Duplicate input fields in positional contract.")
        input_items = _array_items(parameters, contract.input_field, document)
        output_items = _array_items(output, contract.output_field, document)
        _validate_errors(output_items, contract.error_types, document)
        for field in contract.shared_inputs:
            _array_items(parameters, field, document)
        for field in contract.empty_outputs:
            _array_items(output, field, document)
        for items, identity_fields in (
            (input_items, contract.input_identity_fields),
            (output_items, contract.output_identity_fields),
        ):
            for item in items:
                for option in _items(item, document):
                    if _name(option) not in contract.error_types:
                        for field in identity_fields:
                            if not _fields(option, field, document):
                                raise ValueError(f"Stale item identity field {field!r}.")
        for model in contract.partial_output_types:
            if model not in {_name(branch) for item in output_items for branch in _items(item, document)}:
                raise ValueError(f"Stale partial result model {model!r}.")
    for outcome in metadata.outcome_lists:
        _validate_errors(_array_items(output, outcome.field, document), outcome.error_types, document)
    if metadata.count_field:
        _array_items(output, metadata.count_field, document)
    if metadata.handle_if_list:
        _array_items(output, metadata.handle_if_list, document)
    for field in metadata.summary_fields:
        if not _fields(output, field, document):
            raise ValueError(f"Stale result summary field {field!r}.")
    if metadata.inline_if_true:
        field = metadata.inline_if_true
        candidates = [variant for schema in _fields(output, field, document) for variant in _variants(schema, document)]
        if not candidates or any(item.get("type") != "boolean" for item in candidates):
            raise ValueError(f"Invalid result variant flag {field!r}.")
    expected = review_fingerprint(name, command, document)
    if metadata.reviewed != expected:
        raise ValueError(f"Command description or referenced models need review (fingerprint {expected}).")


def validate_source(source: str, commands: dict, document: dict, metadata: dict) -> None:
    actual = {name for owner, name in metadata if owner == source}
    if actual != commands.keys():
        raise ValueError(
            f"{source} command metadata mismatch. Missing: {sorted(commands.keys() - actual)}. "
            f"Stale: {sorted(actual - commands.keys())}."
        )
    issues = []
    for name, command in commands.items():
        try:
            validate_command(name, command, document, metadata[source, name])
        except ValueError as exc:
            issues.append(f"{source}/{name}: {exc}")
    if issues:
        raise ValueError("\n".join(issues))
