---
name: tapir-command-metadata
description: Review and maintain Tapir MCP command contracts when the pinned multiconn release, exposed commands, or handwritten adapters change.
---

# Review Tapir command metadata

Maintain `src/tapir_archicad_mcp/command_metadata.py` as the single source for alignment, extraction, and automatic presentation. Each entry is keyed by the upstream source and command title. Review those decisions together.

1. Run the [codegen preflight](../tapir-mcp-codegen/SKILL.md#establish-the-inputs) using exact-tag metadata and the previous version. Use its report of added, removed, structurally changed, and description-changed commands, plus its metadata diagnostics. Changed referenced models can affect several command consumers. Review those consumers and keep untouched entries intact.
2. Read the relevant parameter and result models and descriptions. For correspondence, use an explicit ordering guarantee or inspect the narrow command implementation or typed multiconn consumer. Equal list lengths and a union containing an error type are insufficient evidence. Mark queries with unestablished correspondence and subset or reordered outputs without positional projection. Retain a concise reason for decisions that need context.
3. Declare the controlling list, returned outcome list, known item errors, identity fields when relevant, and only genuinely parallel inputs. Shared filters, independent axes, and alternative input lists stay independent. For matrix adapters, review identity and dimensions for both axes and what to do when an axis reference has missing identifiers.
4. Classify bare identifiers and acknowledgement lists as handle-preferred when their informative siblings can be summarized. Use size-based delivery for descriptive results and uncertain cases. Check true dry-run variants for informative values before adding an inline override.
5. Update the affected entries and their `reviewed` fingerprints from preflight after reviewing the changes. Remove retired entries. Rerun preflight and regenerate through the production generator. Finish with `--check-generated` and the affected dispatch, schema, and result tests.
