# Tapir 1.7.3 codegen record

**Dependency:** multiconn 0.9.5 → 0.9.6. **Tapir:** 1.7.2 → 1.7.3. Inputs come from the exact published multiconn tags; the manually edited TOML pin was already 0.9.6 when this update began.

Upstream adds 112 Tapir commands, removes none, and structurally changes 48 existing command contracts after resolving references. Official API contracts are unchanged. Exposure grows from **348 to 456 tools**: 402 Tapir and 54 Official, with **108 new public names** and none removed. Earlier [baseline decisions](generator-config-clean-slate.md) are separate from these release additions.

The additions cover element/opening geometry and relations, library/favorites, navigator/3D controls, attributes/properties/IFC, project settings/data, Teamwork and analytical models.

## Retained decisions

- Restore `GetDetailsOfElements`: the published unpatched/final schemas and consumed model replace the undeclared curtain-wall requirement with `height`, `flipped` and `angle`. Restore pagination on `detailsOfElements`.
- Keep both revision getters excluded: the singular/plural required-field defect and outer response-shape mismatch remain; the element getter also uses the database-ID extractor. Retirement conditions remain in the [active schema-exclusion reference](../../.agents/skills/tapir-mcp-codegen/references/schema-exclusions.md).
- Exclude `NewProject` by the user's decision because it discards unsaved work. Preserve `QuitArchicad` and `CloseProject` exclusions.
- Resolve attribute-folder collisions by retaining Official delete/rename and Tapir create/move. Tapir creation accepts MEP/operation folder types; Tapir move returns per-item results. Two existing public names now route to Tapir.
- Map the new categories to `project_data` and `analytical` explicitly. Add 23 top-level pagination mappings for enumeration, nested collections, stored content and geometry; the total is 53. Individual nested items can remain large, and paging the small outer type groups of `GetAttributesFromProject` would not meaningfully bound its output.
- Extract `GetCurrentViewImage.image` with the existing image handler; arbitrary base64 group data remains ordinary data.

The skill's [preflight helper](../../.agents/skills/tapir-mcp-codegen/scripts/codegen_preflight.py) replaces ad hoc metadata/registry checks. The skill now separates a disposable detailed review from this condensed record and prepares PR text automatically. New-command tables stop at 40 entries; larger updates use capability summaries.

No pending human decisions.
