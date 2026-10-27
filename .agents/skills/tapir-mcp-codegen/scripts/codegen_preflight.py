"""Compare exact multiconn releases and validate MCP codegen without modifying generated files."""

import argparse
import ast
import hashlib
import importlib
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import distribution
from pathlib import Path
from urllib.request import urlopen

# This repository-local skill uses the production generator's naming and configuration.
PROJECT_SCRIPTS = Path(__file__).resolve().parents[4] / "scripts"
sys.path.insert(0, str(PROJECT_SCRIPTS))

RELEASE_URL = "https://raw.githubusercontent.com/SzamosiMate/multiconn_archicad/refs/tags/v{version}"
ORGANIZED = "code_generation/unified/temp_files/01_organized_commands.json"
CONSTANTS = "src/multiconn_archicad/constants.py"
SCHEMAS = {
    "tapir": "code_generation/tapir/schema/tapir_master_schema.json",
    "official": "code_generation/official/schema/official_api_master_schema.json",
}
MODEL_NAMES = {source: f"code_generation/{source}/schema/_command_model_names.json" for source in SCHEMAS}
RELEASE_FILES = [
    ORGANIZED,
    CONSTANTS,
    *SCHEMAS.values(),
    *MODEL_NAMES.values(),
    "code_generation/tapir/schema/tapir_unpatched_schema.json",
]
ANNOTATIONS = {"title", "description", "$comment", "examples", "default", "$schema", "$id", "$defs", "definitions"}
SCHEMA_MAPS = {"properties", "patternProperties", "dependentSchemas"}
SCHEMA_VALUES = {
    "items",
    "additionalItems",
    "additionalProperties",
    "unevaluatedProperties",
    "unevaluatedItems",
    "contains",
    "propertyNames",
    "not",
    "if",
    "then",
    "else",
    "contentSchema",
}
SCHEMA_LISTS = {"anyOf", "oneOf", "allOf", "prefixItems"}


class PreflightError(ValueError):
    """Invalid release metadata, configuration or generated output."""


def require(condition, message):
    if not condition:
        raise PreflightError(message)


def read_release(version, cache_dir, *, offline=False, refresh=False):
    """Only reuse cache entries with matching exact-tag provenance and content hashes."""
    require(re.fullmatch(r"[0-9][A-Za-z0-9.!+_-]*", version), f"Invalid release version: {version}")
    directory = cache_dir / version
    base_url = RELEASE_URL.format(version=version)
    manifest_path = directory / "manifest.json"
    files = None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        cached = {path: (directory / path).read_bytes() for path in RELEASE_FILES}
        if manifest == {"url": base_url, "sha256": {p: hashlib.sha256(b).hexdigest() for p, b in cached.items()}}:
            files = cached
    except (OSError, ValueError):
        pass
    if files is None or refresh:
        require(not offline, f"No intact exact-tag cache for multiconn {version}: {directory}")

        def fetch(path):
            with urlopen(f"{base_url}/{path}", timeout=30) as response:
                return path, response.read()

        with ThreadPoolExecutor(max_workers=6) as pool:
            files = dict(pool.map(fetch, RELEASE_FILES))
        # Validate the complete download before marking the cache reusable.
        release = parse_release(version, files)
        for path, content in files.items():
            destination = directory / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        manifest_path.write_text(
            json.dumps(
                {"url": base_url, "sha256": {p: hashlib.sha256(b).hexdigest() for p, b in files.items()}}, indent=2
            ),
            encoding="utf-8",
        )
        return release
    return parse_release(version, files)


def json_pointer(document, reference):
    require(reference.startswith("#/"), f"Unsupported non-local reference: {reference}")
    value = document
    try:
        for part in reference[2:].split("/"):
            value = value[part.replace("~1", "/").replace("~0", "~")]
    except (KeyError, TypeError) as error:
        raise PreflightError(f"Unresolved reference: {reference}") from error
    return value


def references(value):
    if isinstance(value, dict):
        if "$ref" in value:
            yield value["$ref"]
        for key, item in value.items():
            if key in SCHEMA_MAPS | {"$defs", "definitions", "dependencies"}:
                for child in item.values():
                    if isinstance(child, (dict, bool)):
                        yield from references(child)
            elif key in SCHEMA_VALUES | SCHEMA_LISTS:
                for child in item if isinstance(item, list) else [item]:
                    yield from references(child)


def parse_release(version, files):
    data = {path: json.loads(content) for path, content in files.items() if path.endswith(".json")}
    for path, document in data.items():
        if path.endswith("_schema.json"):
            require(isinstance(document, dict) and document.get("$defs"), f"Empty schema in {version}: {path}")
    tree = ast.parse(files[CONSTANTS].decode("utf-8"))
    tapir_version = next(
        (
            ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "SUPPORTED_TAPIR_VERSION" for t in node.targets)
        ),
        None,
    )
    require(isinstance(tapir_version, str) and tapir_version, f"Missing supported Tapir version in {version}")
    organized = data[ORGANIZED]
    require(isinstance(organized, dict), f"Invalid organized metadata in {version}")
    commands = {}
    for source in SCHEMAS:
        groups = organized.get(source)
        require(isinstance(groups, dict) and groups, f"Missing/empty {source} metadata in {version}")
        names = data[MODEL_NAMES[source]]
        require(
            isinstance(names, list) and names and all(isinstance(n, str) and n.isidentifier() for n in names),
            f"Invalid {source} model-name list in {version}",
        )
        require(len(names) == len(set(names)), f"Duplicate {source} model names in {version}")
        schema = data[SCHEMAS[source]]
        require(isinstance(schema, dict) and schema.get("$defs"), f"Empty {source} schema in {version}")
        for ref in references(schema):
            json_pointer(schema, ref)
        found = {}
        for group, items in groups.items():
            require(isinstance(items, list), f"Invalid command group: {source}/{group}")
            for item in items:
                name = item["name"].removeprefix("API.") if source == "official" else item["name"]
                require(name not in found, f"Duplicate upstream command: {source}/{name}")
                require(item.get("group") == group, f"Inconsistent category: {source}/{name}")
                found[name] = {**item, "group": group}
                for suffix in ("Parameters", "Result"):
                    model = name + suffix
                    require(
                        (model in schema["$defs"]) == (model in names),
                        f"Model-name/schema disagreement: {source}/{model}",
                    )
        require(found, f"Empty command inventory: {source}")
        commands[source] = found
    return {
        "version": version,
        "tapir_version": tapir_version,
        "commands": commands,
        "schemas": {s: data[p] for s, p in SCHEMAS.items()},
        "models": {s: set(data[p]) for s, p in MODEL_NAMES.items()},
    }


def resolve_schema(schema, document):
    """Expand alias chains; retain constraint siblings as an intersection, not an overwrite."""
    seen = set()
    while isinstance(schema, dict) and "$ref" in schema:
        reference = schema["$ref"]
        require(reference not in seen, f"Reference-only cycle: {reference}")
        seen.add(reference)
        target = json_pointer(document, reference)
        siblings = {k: v for k, v in schema.items() if k != "$ref" and k not in ANNOTATIONS}
        if siblings:
            return {"allOf": [target, siblings]}
        schema = target
    return schema


def schemas_equal(left, right, left_document, right_document, seen=None):
    """Compare schema graphs, preserving ordered tuple schemas and literal enum/const data."""
    left = resolve_schema(left, left_document)
    right = resolve_schema(right, right_document)
    if not isinstance(left, dict) or not isinstance(right, dict):
        return type(left) is type(right) and left == right
    seen = set() if seen is None else seen
    pair = (id(left), id(right))
    if pair in seen:
        return True  # The same pair of recursive schema nodes is already being compared.
    seen = seen | {pair}
    keys = left.keys() - ANNOTATIONS
    if keys != right.keys() - ANNOTATIONS:
        return False
    for key in keys:
        a, b = left[key], right[key]
        if key in SCHEMA_MAPS:
            if a.keys() != b.keys() or not all(
                schemas_equal(a[n], b[n], left_document, right_document, seen) for n in a
            ):
                return False
        elif key in SCHEMA_LISTS or (key == "items" and isinstance(a, list)):
            if not isinstance(b, list) or len(a) != len(b):
                return False
            if key in {"prefixItems", "items"}:
                if not all(schemas_equal(x, y, left_document, right_document, seen) for x, y in zip(a, b)):
                    return False
            else:
                remaining = list(b)
                for branch in a:
                    index = next(
                        (
                            i
                            for i, candidate in enumerate(remaining)
                            if schemas_equal(branch, candidate, left_document, right_document, seen)
                        ),
                        None,
                    )
                    if index is None:
                        return False
                    remaining.pop(index)
        elif key in SCHEMA_VALUES:
            if not schemas_equal(a, b, left_document, right_document, seen):
                return False
        elif key in {"required", "enum", "type"} and isinstance(a, list):
            if not isinstance(b, list) or sorted(map(json_key, a)) != sorted(map(json_key, b)):
                return False
        elif json_key(a) != json_key(b):
            return False
    return True


def json_key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def compare_releases(previous, target):
    result = {}
    for source in SCHEMAS:
        old, new = previous["commands"][source], target["commands"][source]
        a, b = previous["schemas"][source], target["schemas"][source]
        changed = {}
        for name in sorted(old.keys() & new.keys()):
            contracts = [
                suffix
                for suffix in ("Parameters", "Result")
                if not schemas_equal(a["$defs"].get(name + suffix), b["$defs"].get(name + suffix), a, b)
            ]
            if contracts:
                changed[name] = contracts
        result[source] = {
            "previous_count": len(old),
            "target_count": len(new),
            "added": sorted(new.keys() - old.keys()),
            "removed": sorted(old.keys() - new.keys()),
            "changed": changed,
            "description_changed": sorted(
                n for n in old.keys() & new.keys() if old[n]["description"] != new[n]["description"]
            ),
            "category_changed": {
                n: [old[n]["group"], new[n]["group"]]
                for n in sorted(old.keys() & new.keys())
                if old[n]["group"] != new[n]["group"]
            },
        }
    return result


def variants(schema, document, seen=()):
    schema = resolve_schema(schema, document)
    require(isinstance(schema, dict), "Expected an object schema for a configured result path")
    require(id(schema) not in seen, "Recursive result wrapper at a configured path")
    seen = (*seen, id(schema))
    yield schema
    for key in ("oneOf", "anyOf", "allOf"):
        for branch in schema.get(key, []):
            yield from variants(branch, document, seen)


def field_schemas(schema, field, document):
    return [
        branch["properties"][field] for branch in variants(schema, document) if field in branch.get("properties", {})
    ]


def has_type(schema, required_type, document):
    types = [branch["type"] for branch in variants(schema, document) if "type" in branch]
    return bool(types) and all(value == required_type for value in types)


def validate_config(release, configs):
    from generate_tools import camel_to_snake

    expected = {}
    for config in configs:
        commands = release["commands"][config.name]
        schema = release["schemas"][config.name]
        active = commands.keys() - config.commands_to_exclude
        for name, command in commands.items():
            group = command["group"]
            require(group in config.group_mapping, f"Unmapped category: {config.name}/{group}")
            if name not in active:
                continue
            public_name = f"{config.group_mapping[group]}_{camel_to_snake(name)}"
            require(re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", public_name), f"Invalid public name: {public_name}")
            require(public_name not in expected, f"Tool-name collision: {public_name}")
            expected[public_name] = {"source": config.name, "title": name, "module": group.replace(" ", "_").lower()}
        require(not (config.image_fields.keys() & config.image_lists.keys()), f"Conflicting {config.name} image config")
        for setting, mapping in (
            ("pagination", config.paginated_commands),
            ("image", config.image_fields),
            ("image_list", config.image_lists),
        ):
            require(
                mapping.keys() <= active,
                f"Inactive/unknown {config.name} {setting} entries: {sorted(mapping.keys() - active)}",
            )
            for title, field in mapping.items():
                fields = field_schemas(schema["$defs"][title + "Result"], field, schema)
                required_type = "string" if setting == "image" else "array"
                require(
                    fields and all(has_type(f, required_type, schema) for f in fields),
                    f"Invalid {setting} top-level field: {config.name}/{title}/{field}",
                )
                if setting == "image_list":
                    contents = []
                    for item in fields:
                        for array in variants(item, schema):
                            if "items" not in array:
                                continue
                            for branch in variants(array["items"], schema):
                                for image in field_schemas(branch, "image", schema):
                                    contents.extend(field_schemas(image, "content", schema))
                    require(
                        contents and all(has_type(f, "string", schema) for f in contents),
                        f"Unsupported image-list shape: {config.name}/{title}/{field}",
                    )
    return expected


def validate_generated(release, configs, expected):
    """Check static registrations before imports can hide duplicate or stale definitions."""
    declarations = []
    for config in configs:
        modules = {v["module"] for v in expected.values() if v["source"] == config.name}
        paths = {p.stem for p in config.output_dir.glob("*.py")}
        require(paths == modules | {"__init__"}, f"Missing/stale generated modules: {config.name}")
        init = ast.parse((config.output_dir / "__init__.py").read_text(encoding="utf-8"))
        imports = [node.module for node in init.body if isinstance(node, ast.ImportFrom)]
        wanted = {f"tapir_archicad_mcp.tools.generated.{config.name}.{m}" for m in modules}
        require(set(imports) == wanted and len(imports) == len(wanted), f"Stale/missing imports: {config.name}")
        for path in config.output_dir.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "register_tool_for_dispatch"
                ):
                    names = [ast.literal_eval(k.value) for k in node.keywords if k.arg == "name"]
                    require(len(names) == 1, f"Invalid registration: {path}")
                    declarations.extend(names)
    duplicates = sorted(n for n, count in Counter(declarations).items() if count > 1)
    require(not duplicates, f"Duplicate generated registrations: {duplicates}")
    require(set(declarations) == expected.keys(), "Generated declarations differ from target metadata")

    importlib.import_module("tapir_archicad_mcp.model_configuration")
    registry = importlib.import_module("tapir_archicad_mcp.tools.tool_registry")
    require(registry.TOOL_CALLABLE_REGISTRY.keys() == expected.keys(), "Runtime registry differs from target metadata")
    for name, info in expected.items():
        source, title = info["source"], info["title"]
        entry = registry.TOOL_CALLABLE_REGISTRY[name]
        models = importlib.import_module(f"multiconn_archicad.models.{source}.commands")
        model_name = title + "Parameters"
        model = getattr(models, model_name) if model_name in release["models"][source] else None
        require(entry.params_model is model, f"Wrong parameter contract: {name}")
        require(
            entry.callable.__module__ == f"tapir_archicad_mcp.tools.generated.{source}.{info['module']}",
            f"Wrong dispatch source: {name}",
        )
        require(registry.TOOL_DISCOVERY_CATALOG[name]["title"] == title, f"Wrong discovery title: {name}")
        config = next(c for c in configs if c.name == source)
        for attribute, setting in (
            ("pagination_field", "paginated_commands"),
            ("image_field", "image_fields"),
            ("image_list_field", "image_lists"),
        ):
            require(getattr(entry, attribute) == getattr(config, setting).get(title), f"Wrong {attribute}: {name}")
        registry.get_tool_input_schema(name)
    return len(expected)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", help="Exact previous multiconn release; omit for regeneration")
    parser.add_argument("--tapir-version", help="Assert the requested Tapir target")
    parser.add_argument("--cache-dir", type=Path, required=True, help="Untracked directory for exact-tag downloads")
    parser.add_argument("--output", type=Path, help="Write the machine-readable comparison/check results")
    parser.add_argument("--offline", action="store_true", help="Use an intact provenance-checked cache only")
    parser.add_argument("--refresh", action="store_true", help="Refetch exact-tag metadata")
    parser.add_argument(
        "--check-generated", action="store_true", help="Also validate generated modules and runtime schemas"
    )
    args = parser.parse_args(argv)
    try:
        from generator_config import MULTICONN_VERSION, OFFICIAL_CONFIG, TAPIR_CONFIG
        from multiconn_archicad.constants import SUPPORTED_TAPIR_VERSION

        require(not (args.offline and args.refresh), "--offline and --refresh cannot be combined")
        direct_url = json.loads(distribution("multiconn-archicad").read_text("direct_url.json") or "{}")
        require(
            not direct_url.get("dir_info", {}).get("editable"),
            "Use the pinned release, not an editable multiconn install",
        )
        target = read_release(MULTICONN_VERSION, args.cache_dir, offline=args.offline, refresh=args.refresh)
        require(target["tapir_version"] == SUPPORTED_TAPIR_VERSION, "Installed Tapir constant differs from release tag")
        require(
            not args.tapir_version or target["tapir_version"] == args.tapir_version, "Requested Tapir target mismatch"
        )
        configs = [TAPIR_CONFIG, OFFICIAL_CONFIG]
        expected = validate_config(target, configs)
        result = {
            "multiconn": MULTICONN_VERSION,
            "tapir": target["tapir_version"],
            "registered_counts": dict(Counter(v["source"] for v in expected.values())),
            "expected_tools": expected,
            "generated_schema_count": None,
            "unmatched_exclusions": {
                c.name: sorted(c.commands_to_exclude - target["commands"][c.name].keys()) for c in configs
            },
        }
        if args.previous:
            previous = read_release(args.previous, args.cache_dir, offline=args.offline, refresh=args.refresh)
            result["previous_multiconn"] = args.previous
            result["previous_tapir"] = previous["tapir_version"]
            result["comparison"] = compare_releases(previous, target)
        if args.check_generated:
            result["generated_schema_count"] = validate_generated(target, configs, expected)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(
            f"multiconn {MULTICONN_VERSION} / Tapir {target['tapir_version']}: {len(expected)} intended tools; config valid"
        )
        for source, change in result.get("comparison", {}).items():
            print(
                f"{source}: +{len(change['added'])} -{len(change['removed'])}, {len(change['changed'])} structurally changed commands"
            )
        if args.check_generated:
            print(f"All {result['generated_schema_count']} generated registrations and input schemas valid")
        return 0
    except (PreflightError, OSError, ValueError, RuntimeError, ImportError, KeyError, TypeError) as error:
        print(f"Codegen preflight failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
