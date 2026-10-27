---
name: tapir-mcp-codegen
description: Update or regenerate this repository's Archicad MCP tools from a pinned multiconn release and review affected generator configuration. Use for Tapir MCP API/codegen updates, not generating multiconn models or executing commands in Archicad.
---

# Tapir MCP code generation

Update the multiconn dependency, regenerate MCP wrappers, review affected config, and prepare a temporary detailed review, condensed repository record and PR message. Fix generator/config sources and regenerate; do not hand-edit generated wrappers.

## Choose the operation

- **Update:** select the published multiconn release as below, update its exact dependency pin and lockfile, then complete the review/generation loop.
- **Regenerate:** retain the current dependency and regenerate from its exact release metadata. Review config only where regeneration exposes a demonstrated problem.
- **Audit:** inspect the current config, models, and generated tools without modifying or staging files. Report findings in the response.

Example: `$tapir-mcp-codegen update to multiconn 0.9.6 / Tapir 1.7.3`.

### Select the multiconn release

Updating `pyproject.toml` is part of this skill; the user need not edit it first.

- If a multiconn version is explicit, use it and verify any requested Tapir target against that release's `SUPPORTED_TAPIR_VERSION`.
- If only a Tapir version is explicit, first check whether a manually updated dependency pin selects a published release supporting exactly that version. Otherwise choose the newest stable published multiconn release whose constant matches the requested Tapir version. Verify the distribution and exact release tag; do not infer compatibility from version numbering or the sibling checkout.
- For an update with no version specified, select the newest stable published multiconn release and state its supported Tapir version. If the user explicitly asks for the latest Tapir, establish that Tapir release first; do not silently substitute an older supported version.

Preserve a matching manual pin. If explicit targets conflict or no published release supports the requested Tapir version, explain the mismatch before proceeding with a different target. The old comparison baseline comes from the lockfile and generated working tree, with installed version and Git history as corroboration; an already-edited TOML pin is not evidence that generation was completed.

## Establish the inputs

Read these repository sources as needed:

- `scripts/generator_config.py`: dependency-derived metadata URLs, group prefixes, exclusions, pagination, and images. Read every inline exclusion reason before deciding which release changes affect it.
- `scripts/generate_tools.py` and `scripts/format.py`: wrapper generation and formatting.
- `src/tapir_archicad_mcp/pagination.py`, `images.py`, and `tools/tool_registry.py`: the actual supported config behavior.
- `tools/custom/functions.py` and `tools/custom/models.py` under the same package when assessing discovery overlap; compare what the agent can retrieve, not merely metadata held internally.

Record the initial pin, installed version, generated command names/config, and staged/untracked paths. Preserve session work as the starting point. Distinguish it from HEAD and from the source release's API; earlier changes in the same chat are not new upstream additions.

Fetch old/target organized command metadata, model-name lists, and relevant schemas from their exact multiconn tags. The schema paths under that release's `code_generation/` are:

```text
unified/temp_files/01_organized_commands.json
tapir/schema/_command_model_names.json
tapir/schema/tapir_unpatched_schema.json
tapir/schema/tapir_master_schema.json
official/schema/_command_model_names.json
official/schema/official_api_master_schema.json
```

Use this skill's [preflight helper](scripts/codegen_preflight.py) for exact-release downloads, structural comparison and config checks. Run it from the repository root with the project interpreter; it locates the repository's production generator/config from its own skill location. It compares transitive referenced contracts while preserving siblings, unions, recursion and ordered tuples; extracting an inline schema into a named definition is not a structural change. Its JSON contains added/removed/changed commands and changed descriptions/categories for targeted review. Read description changes when they establish supported behavior; the helper does not make semantic exclusion decisions. Use targeted excerpts rather than loading complete generated files or schemas into context.

For an update, change only the selected multiconn dependency pin, then run:

```text
uv lock
uv sync --locked
```

Verify `importlib.metadata.version("multiconn-archicad")` matches the pin and `multiconn_archicad.constants.SUPPORTED_TAPIR_VERSION` matches the requested Tapir target. Metadata must come from the same release. Do not silently substitute a newer sibling checkout, mutable branch, or editable install if release inputs are unavailable.

After syncing and before generation, run the helper with the actual previous multiconn version and requested Tapir target; omit `--previous` for regeneration:

```text
uv run --locked python .agents/skills/tapir-mcp-codegen/scripts/codegen_preflight.py --previous <old-multiconn> --tapir-version <target-tapir> --cache-dir .tmp/codegen-preflight --output .tmp/codegen-preflight/preflight.json
```

The target comes from the exact installed dependency pin. The cache records exact-tag URLs and content hashes; `--offline` requires an intact cache, and `--refresh` refetches it. The helper exits nonzero for missing metadata, mismatched target versions, collisions, unmapped groups or ineffective active config paths. Exclusions absent from public metadata are reported separately because internal-only exclusions can intentionally have no public command. Repair config, then rerun before generation. For an uncached offline Git-tag export, retain the exact-tag provenance and perform equivalent checks; do not label an unchecked export as helper-validated.

## Decide the affected config

Assess every new command against all applicable config fields. Also review changed commands and the consumers of changed models. Existing exclusions get reconsidered only when those changes or a new counterpart affect their stated reason; a complete baseline review needs an explicit request.

### Exclusions and retirement

Use the existing reasons as the policy, not an immutable blacklist:

- Exclude duplicate capabilities, malformed contracts, internal-only commands, and workflows already intentionally handled through discovery, application UI, or namespace routing.
- For Tapir/Official overlap, prefer the command with useful information unavailable from other retained commands. Compare referenced types, supported targets and controls, not just names or top-level field counts. Prefer Official for equivalent schemas/capabilities because it is more stable. Batching, flatter parameters, or an index already available elsewhere do not alone establish unique returned information. Preserve documented broader target support even when GUID-shaped schemas look alike.
- Keep a **short same-line reason comment** on every exclusion. Examples: `# Same contract; prefer Official`, `# Tapir also supports subelements`, `# Internal use only`.
- Shortlist potentially very destructive commands with limited upside for a human decision; do not add such exclusions autonomously. Ordinary editing/deletion is not enough. Preserve already-approved decisions, including `QuitArchicad`, `CloseProject` and `NewProject`.

For a schema/implementation exclusion affected by the release, consult [known schema exclusions](references/schema-exclusions.md). Inspect the target unpatched schema, final multiconn schema/models, and affected consumers. Inspect narrowly scoped implementation source only when the exclusion depends on runtime behavior or the schema contradicts the actual result.

**Remove an exclusion when its stated reason is demonstrably resolved in the target release.** Do not retain it merely because it was previously approved or documented. Verify every independent defect behind that exclusion; fixing one typo is insufficient if the response shape or implementation remains wrong. A merged PR, release note, newer branch, or version number alone is insufficient proof. Ordinary retirement of a resolved schema/duplicate exclusion does not require another human decision.

When restoring a command, reassess its group, pagination and image handling, regenerate its wrapper, and update the tracking entry in the same run. When excluding a command, remove inactive pagination/image entries. Do not permanently suppress a useful general command for one defective branch unless the user chose that policy.

### Pagination

Focus on **Get commands that can return unexpectedly huge amounts of data relative to the request**. Judge approximate token volume, including GUIDs, XML/free text, nested geometry, property matrices and image lists. A large mutation's execution results normally follow an even larger request; do not routinely paginate those results. Coverage may be refined later; do not make exhaustive pagination a prerequisite for completing an update.

Select the response list most likely to dominate tokens if several exist. The current runtime pages one top-level field, in fixed pages of 100, and repeats sibling metadata. A dotted path is not supported, and a nested subtree can still make one item large. Explain material tradeoffs; do not change runtime page sizing or response shapes merely to add config entries.

### Base64 images

Inspect returned content and referenced item models. Configure `image_fields` for a base64 string or `image_lists` for a supported list shape; the current extractor expects list items like `{"image": {"content": "..."}}` or an error. File paths, texture filenames and image-related enum values are not returned images. Image lists may independently need pagination. If a new shape is unsupported, make the smallest necessary generator/runtime change and test it rather than adding an ineffective config field.

### Category mapping

`group_mapping` determines the tool-name prefix. Map every new upstream category explicitly; do not accept the generator's silent `dev` fallback. Compute intended names across both sources before generation and resolve collisions through the overlap policy; duplicate registrations can silently overwrite each other. Check accidental separators and account for any public-name changes during verification.

## Generate and verify

Run both sources through the repository pipeline, with the project environment and Ruff available:

```text
uv run --locked python scripts/generate_tools.py
```

The generator clears its generated source directories. Preserve any initial edits there and compare them before overwriting. Preflight all metadata before generation. Its fetch failures can produce an empty source while the entry point still exits successfully, so verify expected command coverage and imports rather than relying on exit status or the final log line. An exact local Git-tag export is an acceptable offline metadata source; disclose it and do not confuse it with the sibling working tree.

Repair demonstrated config/generator problems and regenerate until the intended tools register. Verify:

- Registered command names and counts match the target metadata after exclusions; no duplicate names, stale imports, or unexpected fallback prefixes.
- Every registered input schema can be built. Configured pagination fields are real top-level lists, image paths match the extractor, and excluded commands have no inactive config entries.
- Restored/excluded commands actually appear/disappear, and caller-visible identifier/schema changes are understood. MCP wrappers return raw results, so schema-generation success does not prove upstream result correctness.

Rerun the helper with `--check-generated --offline` after generation, using the same arguments/cache. This additionally checks static declarations and package imports before runtime registration can hide duplicates, then dispatch source, parameter models and input schemas. A successful check does not prove upstream result correctness or replace semantic review and the relevant tests.

Run existing generator-config tests and tests covering affected dispatch/pagination/image behavior; broaden to the full suite when changes warrant it. Use a writable `--basetemp` if the Windows sandbox's default pytest temp directory fails. If `uv run` fails on cache permissions, use the verified project interpreter directly rather than repeatedly retrying the cache. Report stalled/limited checks honestly. Do not execute live modifying Archicad commands just to validate code generation.

## Report and stage

For an update, produce two complementary artifacts and revise each in place during the same logical run:

- **Detailed temporary review:** write one Markdown file in a temporary directory outside the repository and link it for the user. Explain new capabilities, exclusion/retirement decisions and their evidence, meaningful config choices, tradeoffs and any decisions needed. Pair focused config/schema excerpts with their explanation. Include no verification/testing section or routine check logs. The user can discard this file after review; future runs do not depend on it.
- **Condensed repository record:** maintain `scripts/codegen_reports/tapir-<version>.md`, normally a few short paragraphs or bullets. Keep previous/target versions and command/tool counts, lasting decisions with brief reasons, links to active unresolved-defect tracking, and any pending human decisions. Do not copy the detailed review, full config mappings, command inventories, migration catalogues, or verification/testing sections. These are maintainer records, not server documentation.

Continue performing all required checks. Keep machine-readable helper results and test logs in untracked scratch storage; surface a material failure, skipped required check or limitation to the user even though report verification sections are omitted. For audit/regeneration, a response is sufficient unless a durable report was requested or needed for a material change.

Preserve completed historical repository records, but do not read the entire archive routinely: current config and the active schema-exclusion reference govern future runs; consult a past record only for a specific provenance or decision question. Intermediate attempts, helper JSON, caches and PR drafts remain scratch artifacts.

Use `references/schema-exclusions.md` only for ongoing schema/implementation reasons and retirement conditions; current config comments remain the primary exclusion policy. Update that reference when its tracked reason is resolved or materially changes. Do not copy whole investigations into the skill or report.

**Automatically stage newly created deliverable files**, including generated modules, the final report, skill files and maintained supporting resources; never stage scratch artifacts. Identify them against the initial working-tree snapshot, use exact paths, verify generated ownership, and preserve unrelated/pre-existing untracked files and existing staged changes. Restage new deliverables after final edits. Leave modifications to previously tracked files unstaged unless the session authorizes otherwise. Do not commit, push, publish, or open an issue/PR unless requested.

## Prepare the PR message

For a completed update, prepare a title and copyable Markdown body following [PR message guidance](references/pull-request.md). For audit/regeneration, do so only when requested. Preparing the message does not authorize a commit, push or PR submission.
