---
name: tapir-mcp-codegen
description: Update or regenerate this repository's Archicad MCP tools from a pinned multiconn release and review affected generator configuration. Use for Tapir MCP API/codegen updates, not generating multiconn models or executing commands in Archicad.
---

# Tapir MCP code generation

Update the multiconn dependency, regenerate MCP wrappers, decide the affected config entries, and leave one concise review report. Fix generator/config sources and regenerate; do not hand-edit generated wrappers.

## Choose the operation

- **Update:** use the requested multiconn version and verify its supported Tapir version. Change the exact dependency pin and lockfile, then complete the review/generation loop below.
- **Regenerate:** retain the current dependency and regenerate from its exact release metadata. Review config only where regeneration exposes a demonstrated problem.
- **Audit:** inspect the current config, models, and generated tools without modifying or staging files. Report findings in the response.

Example: `$tapir-mcp-codegen update to multiconn 0.9.6 / Tapir 1.7.3`.

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

Compare added/removed commands and structurally changed parameter/result contracts, including transitive referenced models. Ignore ordering and description-only noise for structural counts; read changed descriptions when they establish supported behavior. Use targeted excerpts/parsers rather than loading complete generated files or schemas into context.

For an update, change only the requested multiconn dependency pin, then run:

```text
uv lock
uv sync --locked
```

Verify `importlib.metadata.version("multiconn-archicad")` matches the pin and `multiconn_archicad.constants.SUPPORTED_TAPIR_VERSION` matches the requested Tapir target. Metadata must come from the same release. Do not silently substitute a newer sibling checkout, mutable branch, or editable install if release inputs are unavailable.

## Decide the affected config

Assess every new command against all applicable config fields. Also review changed commands and the consumers of changed models. Existing exclusions get reconsidered only when those changes or a new counterpart affect their stated reason; a complete baseline review needs an explicit request.

### Exclusions and retirement

Use the existing reasons as the policy, not an immutable blacklist:

- Exclude duplicate capabilities, malformed contracts, internal-only commands, and workflows already intentionally handled through discovery, application UI, or namespace routing.
- For Tapir/Official overlap, prefer the command with useful information unavailable from other retained commands. Compare referenced types, supported targets and controls, not just names or top-level field counts. Prefer Official for equivalent schemas/capabilities because it is more stable. Batching, flatter parameters, or an index already available elsewhere do not alone establish unique returned information. Preserve documented broader target support even when GUID-shaped schemas look alike.
- Keep a **short same-line reason comment** on every exclusion. Examples: `# Same contract; prefer Official`, `# Tapir also supports subelements`, `# Internal use only`.
- Shortlist potentially very destructive commands with limited upside for a human decision; do not add such exclusions autonomously. Ordinary editing/deletion is not enough. Preserve already-approved decisions, including `QuitArchicad` and `CloseProject`.

For a schema/implementation exclusion affected by the release, consult [known schema exclusions](references/schema-exclusions.md). Inspect the target unpatched schema, final multiconn schema/models, and affected consumers. Inspect narrowly scoped implementation source only when the exclusion depends on runtime behavior or the schema contradicts the actual result.

**Remove an exclusion when its stated reason is demonstrably resolved in the target release.** Do not retain it merely because it was previously approved or documented. Verify every independent defect behind that exclusion; fixing one typo is insufficient if the response shape or implementation remains wrong. A merged PR, release note, newer branch, or version number alone is insufficient proof. Ordinary retirement of a resolved schema/duplicate exclusion does not require another human decision.

When restoring a command, reassess its group, pagination and image handling, regenerate its wrapper, and update the tracking entry in the same run. When excluding a command, remove inactive pagination/image entries. Do not permanently suppress a useful general command for one defective branch unless the user chose that policy.

### Pagination

Focus on **Get commands that can return unexpectedly huge amounts of data relative to the request**. Judge approximate token volume, including GUIDs, XML/free text, nested geometry, property matrices and image lists. A large mutation's execution results normally follow an even larger request; do not routinely paginate those results. Coverage may be refined later; do not make exhaustive pagination a prerequisite for completing an update.

Select the response list most likely to dominate tokens if several exist. The current runtime pages one top-level field, in fixed pages of 100, and repeats sibling metadata. A dotted path is not supported, and a nested subtree can still make one item large. Explain material tradeoffs; do not change runtime page sizing or response shapes merely to add config entries.

### Base64 images

Inspect returned content and referenced item models. Configure `image_fields` for a base64 string or `image_lists` for a supported list shape; the current extractor expects list items like `{"image": {"content": "..."}}` or an error. File paths, texture filenames and image-related enum values are not returned images. Image lists may independently need pagination. If a new shape is unsupported, make the smallest necessary generator/runtime change and test it rather than adding an ineffective config field.

### Category mapping

`group_mapping` determines the tool-name prefix. Map every new upstream category explicitly; do not accept the generator's silent `dev` fallback. Check for collisions and accidental separators. Report public-name changes; changing a prefix is a caller migration, not cosmetic formatting.

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

Run existing generator-config tests and tests covering affected dispatch/pagination/image behavior; broaden to the full suite when changes warrant it. Use a writable `--basetemp` if the Windows sandbox's default pytest temp directory fails. Report stalled/limited checks honestly. Do not execute live modifying Archicad commands just to validate code generation.

## Report and stage

For an update, maintain **one** report at `docs/reports/codegen/tapir-<version>.md`; revise it during the run. For audit/regeneration, a response is sufficient unless a durable report was requested or needed for a material change. Keep logs, snapshots and exhaustive intermediate inventories in untracked scratch storage. Preserve completed historical reports, but do not create a new Markdown file for each investigative step.

Adapt the multiconn codegen report style: a release-level summary, then short decision groups organized by the actual reason, with exact config snippets beside each explanation. Include:

- Previous/target multiconn and Tapir versions, command/tool counts, and relevant baseline distinctions.
- New capabilities and meaningful existing-command changes; new/retired exclusions and their proof; pagination, image and mapping decisions. Summarize ordinary additions by group rather than creating another full command inventory.
- Tool-name/input migrations, verification scope/results, and a short human-decision shortlist, or no pending decisions. Omit empty sections and repeated inventories.

Use `references/schema-exclusions.md` only for ongoing schema/implementation reasons and retirement conditions; current config comments remain the primary exclusion policy. Update that reference when its tracked reason is resolved or materially changes. Do not copy whole investigations into the skill or report.

**Automatically stage all newly created task files**, including generated modules, reports, skill files and supporting resources. Identify them against the initial working-tree snapshot, use exact paths, verify generated ownership, and preserve unrelated/pre-existing untracked files and existing staged changes. Restage newly created files after final edits. Leave modifications to previously tracked files unstaged unless the session authorizes otherwise. Do not commit, push, publish, or open an issue/PR unless requested.
