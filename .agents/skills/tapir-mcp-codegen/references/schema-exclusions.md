# Schema exclusions to revisit when affected

The config holds the active exclusions and short reasons. This note preserves only evidence and retirement conditions that do not fit inline. Verify against the target release; these observations are not instructions to keep an exclusion forever.

Last checked: published multiconn tag `v0.9.6` / Tapir `1.7.3` (2026-10-27). The resolved CurtainWallDetails exclusion was retired; only ongoing defects remain below.

## GetCurrentRevisionChangesOfLayouts and GetRevisionChangesOfElements

- Source: `#/$defs/RevisionChangesArrayItem` requires singular `revisionChange` instead of declared plural `revisionChanges`, again in a closed object.
- `#/$defs/RevisionChangesOfEntities` describes one object, but the command writers return outer arrays with one success/error item per input. Fix both the required spelling and the outer shape; the actual lists are top-level fields, not a nested-pagination requirement.
- Both problems remain in upstream 1.7.3 and published multiconn 0.9.6, before and after patching. The generated result models reject the actual list-shaped response when explicitly validated.
- Additionally, `GetRevisionChangesOfElementsCommand::Execute` calls `GetGuidFromDatabaseArrayItem` on element inputs. That helper reads `databaseId`; valid inputs contain `elementId`, so the extractor returns `APINULLGuid`. Restore this command only after verifying the element-ID extraction correction as well as both schema corrections. The layout command correctly uses database IDs.
- Upstream deliberately omits response validation from `CommandBase::GetResponseSchema()`, and the MCP preserves raw results. Schema defects alone do not prove every raw layout call fails. The wrong element extractor is a separate implementation defect; no live outcome was tested.
- Evidence: [shared schema](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.3/docs/archicad-addon/common_schema_definitions.js#L10002), [layout declaration/writer](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.3/archicad-addon/Sources/RevisionCommands.cpp#L340), [element declaration/writer](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.3/archicad-addon/Sources/RevisionCommands.cpp#L414), [ID helpers](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.3/archicad-addon/Sources/CommandBase.hpp#L67), [null fallback](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.3/archicad-addon/Sources/CommandBase.cpp#L115).

For a later release, inspect only the changed definitions/consumers and implementation lines tied to these reasons. Remove a resolved entry or reduce it to the remaining reason; do not accumulate a historical investigation log here.
