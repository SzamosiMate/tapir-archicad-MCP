# MCP generator baseline

**Result:** Applied and verified before the dependency update. **multiconn:** 0.9.5. **Tapir:** 1.7.2.

## Applied decisions

- Added the seven selected pagination fields: Tapir `GetPropertyValuesOfElements`, `GetIFCPropertiesOfElements`, `GetRelationsOfElements`, `GetMEPRoutingElements`, `GetCollisions`; Official `GetDetailsOfProperties`, `GetPropertyValuesOfElementComponents`.
- Removed the inactive `GetGraphicalOverrideRules` pagination entry. Temporarily excluded `GetDetailsOfElements` and removed its pagination entry too. There are now **30 active pagination mappings**; no bulk-result paging was added.
- Restored nine commands whose useful information or Official capability justified exposure: Tapir `GetProjectInfo`, `GetArchicadLocation`; Official `GetProductInfo`, `GetCompositeAttributes`, `GetFillAttributes`, `GetLayerAttributes`, `GetLineAttributes`, `GetPenTableAttributes`, `GetZoneCategoryAttributes`.
- Excluded twelve commands: `CloseProject`; three duplicate navigator operations; five duplicate attribute getters; and `GetDetailsOfElements`, `GetCurrentRevisionChangesOfLayouts`, `GetRevisionChangesOfElements`. Every exclusion has a short same-line reason in `scripts/generator_config.py`.
- Fixed the solid-operation prefix: all six `solid_ops__*` names are now `solid_ops_*`.

Current exposure is **348 tools**: 292 Tapir and 56 Official, compared with 351 before these baseline decisions. The dependency and lockfile remain unchanged.

## Caller migrations

| Retired tool | Retained tool |
| --- | --- |
| `attributes_get_composites` | `attributes_get_composite_attributes` |
| `attributes_get_layers` | `attributes_get_layer_attributes` |
| `attributes_get_lines` | `attributes_get_line_attributes` |
| `attributes_get_pen_tables` | `attributes_get_pen_table_attributes` |
| `attributes_get_zone_categories` | `attributes_get_zone_category_attributes` |
| `navigator_clone_project_map_item_to_view_map` | `view_clone_project_map_item_to_view_map` |
| `navigator_create_layout_subset` | `layout_create_layout_subset` |
| `navigator_create_view_map_folder` | `view_create_view_map_folder` |

Official counterparts have their own input schemas; callers must rediscover them. These are not transparent aliases. The close/details/revision exclusions have no replacement added here.

## Ongoing update context

The reusable workflow is [tapir-mcp-codegen](../../.agents/skills/tapir-mcp-codegen/SKILL.md). It focuses pagination on unexpectedly large Get responses, revisits release-affected exclusions, automatically retires resolved reasons, and stages all new task files.

Only the [schema-exclusion note](../../.agents/skills/tapir-mcp-codegen/references/schema-exclusions.md) is needed for unresolved schema/implementation details. The curtain-wall defect is corrected upstream in 1.7.3; revision defects remain there. The target release must be verified before any exclusion is retired. The temporary details exclusion is deliberately still present for the future update to evaluate.

Long exploratory reviews/inventories were archived outside the repository and removed from its proposed changes. The config is the exclusion policy; the skill holds the workflow; this file records only accepted baseline decisions and migrations.

## Verification

Both production source-generation pipelines used metadata from the exact local multiconn `v0.9.5` tag. Registered names/counts, input schemas, all active pagination mappings, the three schema exclusions, and corrected solid-operation names were checked. Generator-config tests: **7 passed**. Config lint and formatting checks for both generated source directories pass. The skill passes its frontmatter/scaffold validator.

No live Archicad commands or dependency update were run. New task-owned files are staged; unrelated pre-existing work is preserved.
