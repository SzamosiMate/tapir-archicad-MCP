Implementation plan for the Tapir Archicad MCP handle architecture. P0 delivers reusable stored results, automatic batch outcome propagation, matrix-aware property commands, semantic and token-based output selection, and actionable error summaries. Alignment, extraction, and presentation are maintained together as Python command metadata. P1 and P2 remain future directions to refine after P0 is working.

Status: finalized for implementation following the design discussion. Implement P0 in the ordered steps below. This plan update does not itself start implementation, regenerate wrappers, modify dependencies, or execute Archicad commands.

# Agreed scope and baseline

P0 exposes two distinct public handle types. A `job:…` handle identifies an execution for `archicad_get_job`. A `result:…` handle identifies a completed output for `result_read` and for use as a parameter in a later command. Both point into the same process-local job record and share its storage, retention, and invalidation.

Retain the existing 45-second execution/poll threshold, request-independent execution and completion capture, application-owned resources across transports, 32 unfinished executions, 24-hour terminal-job lifetime, and capacity of 128 completed/failed jobs. Running jobs are not evicted by terminal retention. No automatic command retries.

The current repository already provides these jobs, job-owned pagination snapshots, command discovery and input-schema retrieval, generated raw API wrappers, and handwritten element queries. It does not yet provide reusable references, per-command batch contracts, output-schema retrieval, token-based delivery policy, or result inspection.

The four long-term result tool areas remain describe, read, transform, and export. P0 implements bounded result_read plus the existing command schema getter extended with optional output schemas. The fuller result_describe tool is deferred because basic result metadata and grouped errors arrive directly in normal responses.

Property matrices are included in P0 to exercise the architecture on a frequent real workflow. Advanced population mapping and arbitrary data transformations are excluded.

# P0 implementation checkpoints

The following checkpoints belong to the planned implementation. Complete and verify their concrete representations in the relevant steps; they are not a request for another approval round. Keep the agreed scope fixed and revisit only a demonstrated incompatibility.

1. Use explicit references with `$handle` containing a result handle and an optional `path`. Support selection of stored result values and originating input values associated with the outcomes. Step 1 defines their typed representations and Step 5 implements the shared lookup and preparation. Write acknowledgements and successful input identifiers are distinct views.

2. Define and test one normalized batch/matrix representation in Step 1, including original coordinates and axes. Its agent-facing schema must describe the actual returned data. Keep ordinary small-result compatibility where possible; document any intentional shape changes caused by batch normalization.

3. Replace command pagination with semantic preferences, token budgets, and bounded reads through `result_read`. Remove the 100-item promotion rule, `page_token` input, and `next_page_token` output. Document the replacement workflow before release.

4. Use local o200k_base reference-token counts, an 8,000-token auto inline limit, a 32,000-token explicit inline limit, and an independent 128 KiB JSON ceiling. Limits are CLI/environment configurable. Runtime counting needs no model-provider API.

5. Snapshot reading works while retained, even after the original instance disappears. Resolved arguments follow the destination command's usual validation. Project identity tracking, project-based binding checks, and identifier translation are outside P0.

6. Include handwritten property grid reads and sparse writes in P0. Define their names, parameter schemas and low-level counterpart descriptions during Step 7. Keep generated low-level commands available unless an established exclusion applies; make the matrix commands' intended workflow clear in discovery.

The initial metadata pass reviews alignment, extraction, and automatic presentation together for every exposed command. Later codegen updates review only added or affected entries. P1/P2 decisions remain deferred until P0 is working.

# P0 target behavior

The execution tool keeps its discovery/schema/call workflow for Archicad commands. Result tools remain directly exposed, with compact definitions, independently of the large API command catalog.

A call is prepared explicitly before normal model validation. Preparation resolves references into concrete command arguments and execution-owned bindings that preserve source slots, axes, and selected positions. Serialization performs no reference lookup or stateful preparation.

Execution timing and result delivery are independent. A call still running after the initial wait returns a job handle. On completion, delivery returns either inline command data or a result handle with a summary. A caller that intends to chain or inspect the result can request `resultMode="handle"` from the outset. Polling a slow execution applies the same delivery policy as a fast completion.

For recognized positional batches, only successful values are sent to Archicad. Returned outcomes are projected into the original positions. Previous errors become upstream_failed; intentionally filtered entries remain filtered. Literal inputs participate through the same batch contract with initially successful slots.

For property matrices, the adapter receives the full grid and its row/column identities. Sparse dispatch sends only successful cells, then projects outcomes back to the original grid. Do not flatten a matrix or independently compact its axes during generic reference resolution.

A source batch with 100 successful and 10 failed slots, followed by 85 successful and 15 failed command outcomes, produces 110 aligned slots: 85 success, 15 failed, and 10 upstream_failed.

A 100-element by 3-property read with 290 successful and 10 failed cells, followed by 280 successful and 10 failed write outcomes, produces the original 100 by 3 grid: 280 success, 10 failed, and 10 upstream_failed.

# Step 1 Define result contracts and representations

Deliver a small typed internal model for stored command results, references, preparation bindings, command contracts, and serialized summaries. Reuse multiconn BatchResult, BatchGrid, BatchSlot, BatchError, and SlotState instead of duplicating their outcome system.

Separate execution status from item outcomes. A completed job may contain failed items. A transport or whole-command exception is a failed job and must not be fabricated into one error per item.

Represent ordinary outputs, positional batches, and property matrices. Preserve command field names where practical. For matrices, retain ordered element IDs, ordered property IDs, and the grid together. For positional results, retain the originating inputs needed for successful-input reuse.

Store one authoritative result graph in the job record. Represent job handles and result handles as distinct public types that resolve to that record through their respective lookup paths. Avoid independent full JSON copies and a second raw-result cache. Serialized projections may be cached only where they provide a demonstrated benefit.

Retain the coordinates and error information already present on the returned multiconn result. A downstream `upstream_failed` slot keeps its state and position. If multiconn supplies a cause, expose it through the existing result representation. An earlier error remains inspectable on its source result while that result is retained.

Acceptance: define the exact agent-facing JSON and schemas for representative ordinary, positional, and matrix results; verify round-trip serialization of mixed states; verify that current multiconn property-specific error categories survive normalization.

# Step 2 Establish explicit contracts for every command

Add one maintained Python mapping keyed by stable upstream source and command identity. Each entry is a typed CommandMetadata object containing batch alignment, input/output extraction paths, adapter identity where needed, and the automatic presentation preference. Every exposed generated or handwritten command has an explicit entry, including no automatic alignment. Use no YAML format and no separate alignment/presentation maps.

A positional contract declares the controlling input list, corresponding output list, ordered one-outcome-per-submitted-item guarantee, known error item types, and any other inputs that share that axis. Other lists are shared parameters or separate axes, not automatically zipped.

A matrix adapter declares element and property axes and cell-level behavior. Commands that return subsets, reorder outputs, create unrelated objects, or have unestablished correspondence are marked as having no automatic positional projection unless a supported explicit mapping exists.

Schema shapes help identify candidate mappings and presentation preferences but do not prove them. In one review of the input/output models, use exact-release descriptions and narrowly scoped implementation evidence to decide extraction paths, alignment guarantees, and informational value. Record concise reasons for non-obvious decisions. This is development-time LLM/human review, never runtime semantic inference.

Validate combined metadata coverage, duplicate identities, parameter/result paths, list types, adapter references, and presentation values deterministically. Declared positional contracts rely on Archicad's one-outcome-per-submitted-item guarantee. If an upstream response violates that contract, the existing multiconn projection check raises and normal job failure handling applies.

Acceptance: all registered commands have explicit combined metadata; GetDetailsOfElements with supplied elements is distinguishable from subset-returning FilterElements; independent element/property axes cannot be mistaken for parallel lists; acknowledgements and bare identifier collections receive reviewed presentation preferences.

# Step 3 Integrate contract maintenance into codegen

Create a repository skill dedicated to extracting, reviewing, and maintaining the combined command metadata. Invoke it from the existing tapir-mcp-codegen skill. The initial pass crawls each command's models once and decides alignment/extraction and presentation together; later relevant updates maintain those same entries.

Use exact pinned multiconn metadata and the existing preflight's added, removed, structural-change, and description-change results. Review consumers of changed referenced models. Do not require a full historical re-audit for every update.

The skill updates the single Python metadata mapping, recording supported mappings, explicit unsupported cases, and presentation decisions together. Runtime behavior is deterministic and does not ask a model to infer alignment or informational value.

Update generator/config sources and regenerate wrappers; do not hand-edit generated modules. Place the maintained mapping in the runtime package, for example tools/command_metadata.py, with lightweight typed metadata definitions. Keep it free of development-time version checks, network access, and eager command-model imports that could disrupt model configuration. Do not import scripts/generator_config.py from the running server.

At registration, attach the matching shared CommandMetadata object to ToolRegistryEntry.metadata in TOOL_CALLABLE_REGISTRY. Generated wrappers reference the maintained entry rather than duplicating its contents. Register output model/schema information alongside it. TOOL_DISCOVERY_CATALOG remains a lightweight name/title/description view; schema retrieval and execution access the authoritative registry entry. Do not store the complete metadata in every discovery response.

Structural or relevant semantic description changes trigger review of both alignment and presentation. Missing/stale metadata must fail codegen checks rather than silently acquiring guessed behavior. A wrapper's generic dict return annotation is not evidence for its actual output schema.

Acceptance: tests cover an added command, removed command, changed referenced result type, semantic description change, missing metadata, stale path, and regeneration preserving reviewed alignment and presentation. Prove one maintained object reaches runtime registration without importing the development-time generator config.

# Step 4 Extend schema discovery and reference documentation

Extend archicad_get_command_schema with an optional output-schema request, defaulting to input-only retrieval. Preserve existing callers and the input_schema field.

When requested, return the actual agent-facing output schema, including normalized result data and batch/matrix semantics. Distinguish the result-data schema from job delivery envelopes and the ordinary running/completed/failed job states.

Render accepted reference alternatives in incoming argument schemas without changing multiconn's upstream wire models. Keep the existing ForbidExtrasMixin configuration. Reference resolution will be explicit, so a stateful validator/serializer mixin is not required.

Use one reference definition throughout P0, for example `{"$handle":"result:abc","path":["elements"]}`. Paths are arrays of field names and nonnegative integer indices. An omitted path selects the stored result root. Job handles are for polling and are rejected in result references.

The always-visible execution description explains the reference syntax and automatic batch behavior concisely. Advertise only implemented result tools. Do not attach suggested field paths to every handle response.

Acceptance: ordinary calls retain usable schemas; reference alternatives appear at supported destinations; optional output schemas preserve unions/recursion; output schemas describe real wrapper results rather than an unmodified upstream response.

# Step 5 Implement explicit call preparation

Introduce a preparation function used by archicad_call_tool before normal parameter validation. It accepts the command contract, raw arguments, and the job store, and returns prepared arguments plus reference bindings.

Resolve only explicit reference objects. Ordinary strings, dictionaries, and GUIDs remain literal data. Do not search arbitrary strings for handles or interpret user data as executable accessor expressions.

Lookup requires a result handle that resolves to a retained completed result. Unknown or expired result handles, job handles, missing paths, out-of-range indices, and type-incompatible values receive actionable ToolErrors before Archicad dispatch. For a command whose output will be reused, request `resultMode="handle"` on the original call. If it is still running after the initial wait, poll its job handle until the result handle is available.

For positional batches, preserve the selected source batch in the binding, compute submitted positions, construct successful concrete inputs, and validate them against the destination model. Preserve bindings for nested destinations and the paths by which they were supplied.

Support selecting original inputs associated with successful outcomes as well as successful returned values. A write acknowledgement must never be mistaken for the element ID the next command needs. Define this distinction in the reference schema and preserve the same positional state information whichever view is selected.

For matrix-aware commands, preserve the structured grid and labeled axes for the adapter. Reference lookup itself does not universally extract successes.

Use per-call objects, not globals, thread-local state, or metadata secretly attached to generated models. Once admitted, the worker holds the resolved objects needed to finish even if their source entries are evicted.

Acceptance: successful-output and successful-input reuse; nested references; literal arguments unchanged; errors before dispatch; concurrent preparations isolated; downstream execution survives source eviction; metadata never leaks into the Archicad payload.

# Step 6 Add positional execution and projection

Integrate preparation bindings with the existing worker-owned execution path. Keep blocking preparation/execution and expensive result work off the event loop, and keep execution and response rendering outside long-held store locks.

Use the declared axis mapping to apply one success mask to every input that shares that axis. Reject ambiguous multi-source alignments before dispatch. Do not infer identity from equal list lengths, especially where duplicates or different orderings are possible.

Dispatch exactly once using concrete validated parameters. Normalize known upstream item errors using multiconn's result machinery and project with BatchResult.project_successes or the corresponding declared adapter. Rely on multiconn's existing cardinality check for projection. Projection exceptions follow the ordinary failed-job path.

When no item is eligible, do not call Archicad. Produce the corresponding skipped result with full alignment. Handle empty literal inputs according to the declared command semantics; never turn an empty selection into an omitted argument that means all elements.

Whole-command and response-processing failures preserve the distinction between failed execution and mixed item outcomes. Communication failures retain the existing warning that Archicad's actual outcome may be unknown.

Acceptance: literal batches; 100-success/10-error to 85-success/15-error propagation; repeated chaining; duplicate inputs; filtered slots; all-skipped inputs; shared-axis parameter alignment; exactly one dispatch; cancellation-safe completion.

# Step 7 Add handwritten matrix-aware property commands

Register handwritten property read and write commands using the same discovery, schema, execution, job, and reference infrastructure as other commands. Keep their public parameter schemas compact.

Use PropertyUtilities.get_property_values_per_element_result for reads and set_property_values_per_element_sparse_result for success-only writes. Reuse multiconn's dimensions checks, normalization, sparse payload construction, and projection rather than implementing these again in MCP.

Retain ordered element IDs and property IDs with each grid. Successful cells are written independently. Input errors become upstream_failed, filtered cells remain filtered, and API failures occupy the attempted cells. No eligible cells means no write request.

Expose whole-row errors when the returned grid carries them, as it does for property reads. Distinguish failed-cell counts from affected-element counts. A projected write grid follows multiconn's current behavior. Cells blocked by an earlier error remain aligned as `upstream_failed`, with the original reason available on the source read. Any enhancement to carry causes or whole-row errors through projection belongs in multiconn.

Property reads currently return strings, distinguish undefined/unavailable conditions through typed errors, and offer SI formatting. State that in schemas and summaries. Do not silently parse numeric strings or alter units.

Resolve failed element/property references by explicit axis-aware rules recorded in the adapter contract. If an axis lacks enough identity to preserve correspondence, reject that input form rather than guessing. Tests establish supported forms before the property commands are exposed.

Register the handwritten matrix commands with clear workflow descriptions. Keep generated low-level counterparts unless an established exclusion applies, and distinguish their raw contract from the matrix-aware adapter. Public names are routine implementation choices, not a separate approval gate.

Acceptance: 2 by 3 mixed grid; failed row and cell; axis ordering and duplicates; mismatched dimensions; empty/no-success behavior; undefined/unavailable states; sparse writes with projected results; preserved source grid after partial writes.

# Step 8 Implement semantic presentation and token budgeting

Add `resultMode` with `auto`, `inline`, and `handle` to the execution envelope, outside the Archicad command parameters. The same 45-second initial wait applies to every mode. A still-running execution returns a `jobHandle`, regardless of its eventual result mode.

Use tiktoken with the local o200k_base reference tokenizer. Count the compact JSON representation of the data being considered for inline delivery. These counts are a reproducible estimate, not the consuming client's exact context or billing usage.

Defaults: auto inline limit 8,000 reference tokens; explicit inline limit 32,000 reference tokens; independent maximum JSON size 131,072 UTF-8 bytes. CLI options override environment values. Validate positive limits and auto limit no greater than inline limit.

Configuration options: --result-auto-max-tokens / TAPIR_MCP_RESULT_AUTO_MAX_TOKENS; --result-inline-max-tokens / TAPIR_MCP_RESULT_INLINE_MAX_TOKENS; --result-inline-max-bytes / TAPIR_MCP_RESULT_INLINE_MAX_BYTES.

Apply delivery rules in this order. Explicit `handle` selects a result handle. Explicit `inline` bypasses the semantic preference and remains subject to token and byte limits. `auto` uses the reviewed metadata preference, then the size rules. HANDLE_PREFERRED selects a result handle plus a useful summary even for a tiny result. SIZE_BASED selects inline data for small informative results and is the default classification when the semantic preference is uncertain.

Completed responses have mutually exclusive delivery forms. Inline delivery contains the command data. Handle delivery contains `resultHandle` and compact summary information. A terminal poll may echo the `jobHandle` used to poll it. Apply the same delivery decision to the initial response and to every later poll.

Classify acknowledgement batches and bare identifier collections as handle-preferred where the reviewed contract supports that choice. Descriptive records, such as names paired with IDs, remain size-based when their contents help the agent choose its next action. Newly created objects are classified by their actual content, not their origin. Add a narrow result-variant override only where genuinely needed; do not build a general policy language.

Preserve meaningful warnings and status information in the compact response when the main payload is represented by a handle. Use declared output/summary semantics, not heuristics based on field names or GUID-looking strings. Review these decisions in the same metadata pass as alignment and extraction.

Cache the tokenizer once and provide its encoding data for offline packaged operation. No provider counting API and no dependency on detecting the active agent model. Treat arbitrary result text as ordinary text, including strings resembling tokenizer special tokens.

Below the byte ceiling, tokenize once when needed. Beyond it, select a result handle without a full tokenization pass. Above the inline budget, explicit inline falls back to a result handle with a concise reason. Never silently truncate a complete command result.

Count the serialized JSON once even if the MCP transport exposes both text and structured content. Client rendering overhead is outside the server's estimate. Inline delivery uses native MCP image content for supported media. Handle delivery retains media for bounded `result_read` retrieval. A selected image can be returned as native MCP image content, and base64 stays out of the agent-facing JSON.

Keep full results in their jobs regardless of delivery mode. For handle delivery, associate one stable result handle with the job record. Polling respects the selected delivery policy. `result_read` has its own bounded rendering behavior.

Acceptance: tiny acknowledgement/identifier batches become result handles in auto; informative small records stay inline; explicit inline bypasses semantic preference within hard limits; completed responses contain exactly one delivery form; meaningful sibling warnings remain visible; result-variant policies work when declared; threshold boundaries, GUID JSON, Unicode, special-token-looking strings, forced handles, repeated polling, offline tokenizer loading, CLI/env precedence and native-image behavior pass.

# Step 9 Return useful handle information and grouped errors

Return basic information at the point it is needed. A new running job response includes `jobHandle`, command identity, and short polling guidance. Repeated running polls remain minimal. A completed response delivered by handle includes `resultHandle`, result kind, item count or matrix dimensions, outcome totals, grouped errors, and brief reference and `result_read` guidance.

Do not include a full return schema, automatically suggested accessor paths, or arbitrary examples in every handle response. Schemas are obtained through the existing schema getter when requested.

Grouped errors are P0 and must not require another call. Group by meaningful error category and upstream code where available, with count and one safe representative message. A generic BatchError Python class is not a useful category by itself.

Separate new failures from `upstream_failed` slots and group known causes when the result supplies them. Count skipped cells even when the projected result carries no cause. Distinguish cells from rows and items. Keep intentionally filtered entries separate from failures. Whole-command failures use the failed-job response.

Bound the number and text size of groups. Report omitted group/error counts explicitly; do not imply the displayed groups cover everything when they do not. Compute counts/grouping while normalizing results so ordinary handle output does not trigger a fresh expensive traversal.

Use semantic summaries for adapters with known result types. For unclassified ordinary results, return known type/count information without claiming generic success or recursively treating every field named error as a failure.

Acceptance: repeated errors collapse; distinct errors remain meaningful; blocked slots remain visible when the projected result carries no cause; row and cell counts are clear; grouping is bounded; unexpected exception details remain hidden.

# Step 10 Expose bounded result reading

Add a directly exposed `result_read` tool with a small schema. It accepts a result handle and reads its retained completed output without contacting Archicad or creating a new execution job.

Support selected paths, indices/ranges, matrix row/column selections, outcome views, and inspection of original inputs and error coordinates. Use the same accessor convention as references. Return stable source coordinates when inspecting successes or errors.

Provide deterministic traversal and continuation. Validate continuation against the result handle and selection. Return an explicit truncation/continuation indication when the requested selection exceeds the inspection budget. Avoid serializing an unbounded full result just to return a small page.

Use the same reference-token counting policy and byte guard for context-bound output, with deterministic range/continuation semantics covered by the tool schema. A large single string or nested item needs bounded inspection, not just a row limit. Return only the bounded selection and explicit continuation information; keep the complete result in its existing job.

Return actionable errors for unknown or expired result handles, job handles supplied in place of result handles, and invalid selections. Snapshot reading remains available without the original Archicad connection while the result is retained.

Acceptance: multiple selected paths; mixed outcomes with coordinates; matrix selection; large single item; continuation and mismatch rejection; source expiry; no Archicad call; no accidental full-result output.

# Step 11 Share retention and remove command pagination

Preserve the existing job lifetime and capacity rules. The execution, retained result, original inputs needed for reuse, summaries, and bounded-read state belong to one record. Expiry or capacity eviction invalidates its job handle and any result handle together.

Hold strong references to sources needed by admitted downstream workers. Do not introduce a second TTL, dependency pinning feature, persistent database, or separate public release lifecycle in P0.

Remove command pagination from execution, generated argument schemas and registrations, and tool guidance. Remove the old page-token store lookups and pagination snapshots. Document `resultMode="handle"` and `result_read` as the replacement for requesting and reading large results.

Image extraction and structured/text MCP delivery use the same retained-result representation as result lookup.

Acceptance: terminal expiry or capacity eviction invalidates both handle types; job polling rejects result handles and result lookup rejects job handles; downstream work already holding inputs still finishes; fast executions remain discoverable; command schemas and responses omit page tokens; transport reconnect and cancellation behavior remains intact.

# Step 12 Verify P0 as end to end workflows

Run focused tests during each step, then the affected unit/integration suites and a final complete repository suite. Use behavioral assertions, controllable workers, short wait settings, and a fake clock where appropriate.

Required workflows:

- A fast small informative read in auto returns inline data only. The same read in handle mode returns a result handle with its summary. Use that result handle as a parameter in a later command.

- A large immediate result is delivered by result handle. A slow command initially returns a job handle, then polling returns either inline data or a distinct result handle according to the original delivery policy.

- Read a batch, forward successes, observe aligned new failures and upstream failures, then inspect errors without downloading the full batch.

- Reuse successful original inputs after a write returns acknowledgements.

- Read a property grid, sparse-write its eligible cells, and inspect the aligned matrix outcome.

- Receive grouped errors and decide whether to continue without a preliminary description call.

- Cancel an initial request/poll, reconnect over supported transports, and recover the retained result.

- Evict/expire a source while a dependent command is already running.

- Regenerate tools against the pinned release and prove command contracts/output schemas remain registered and valid.

Use mocked Archicad dispatch for automated coverage. Live modifying commands require an appropriate disposable fixture and a separately agreed experiment; do not run arbitrary writes against an open project as a generation check.

Add concise user-facing reference and batch/matrix examples, delivery-mode configuration, error-summary meaning, and migration notes. Keep implementation details in developer documentation rather than the short README.

P0 is ready when these workflows pass, every exposed command has an explicit contract classification, matrix commands demonstrate cell-level propagation, and the agent can reuse or inspect retained data without unnecessary discovery calls.

# Implementation locations

Primary existing integration points:

- src/tapir_archicad_mcp/tools/custom/functions.py: explicit preparation, execution integration, schema retrieval, job response flow.

- src/tapir_archicad_mcp/tools/tool_registry.py and scripts/generate_tools.py: result models, schema metadata, execution contracts, accepted reference schemas.

- src/tapir_archicad_mcp/tools/command_metadata.py and lightweight metadata types: the single maintained Python mapping for extraction, alignment and semantic presentation. scripts/generator_config.py remains development-time generator configuration.

- src/tapir_archicad_mcp/jobs.py: one retained-result owner, distinct job and result lookups, delivery policy, result bindings and summaries.

- src/tapir_archicad_mcp/tool_results.py and server.py: bounded rendering and settings. Remove pagination.py and its command pagination wiring.

- tools/custom: handwritten property commands and result_read, with separate focused modules for references, contracts, and result normalization as needed.

- .agents/skills/tapir-mcp-codegen and a new combined command-metadata review skill: one initial model crawl, targeted future review, and deterministic validation.

- tests/unit and tests/integration: extend current behavioral coverage.

Multiconn sources to reuse:

- models/config.py and current model configuration: preserve existing import-time configuration; explicit preparation replaces the proposed resolution mixin.

- utilities/results/batch_results.py: BatchResult, BatchGrid, states and projection.

- utilities/results/property_errors.py: undefined/unavailable categories.

- utilities/namespaces/properties.py: result-returning reads and sparse writes.

- utilities/results/population.py: use only when a P0 behavior actually needs its existing reporting facilities; general population tracking is future work.

Use the exact installed/released multiconn dependency for implementation and regeneration. The sibling checkout supplies design evidence but must not silently replace the pinned distribution.

# Future P1 work

Refine these after P0 is ready; no detailed syntax or framework choices are required now.

1. result_describe: supplementary schema retrieval, observed subtree structure and interpretation. Basic schemas remain available through command discovery. Returning only union variants actually present is a later optimization.

2. result_transform: derived handles for projection/renaming, reshaping, predicates, sorting, distinct values and useful grouped numeric summaries.

3. result_read improvements: text/value search and sampling.

4. Richer provenance and optional chain reports using the coordinates retained by P0 and any upstream causes supplied by multiconn.

Keep the directly exposed tool set small. Simple accessor reuse and automatic failure exclusion remain execution features, not transform-tool round trips.

# Future P2 work

Refine only after P0 experience identifies concrete needs.

- result_export: JSON/JSON Lines and tabular CSV/Parquet, preserving identifiers, outcome states, units and schema information where supported.

- Python interoperability adapters such as Polars conversion.

- Combining/comparing results: concatenation, set operations, joins and snapshot differences.

- Explicit relations between different populations, reshaped coordinate spaces, and more complete execution lineage.

- Optional lifecycle conveniences such as labels, retention extension, explicit release and import, if justified.

Do not add persistence, automatic retries, agent wake-up, heartbeat timeout workarounds, native task scheduling, or an arbitrary code execution runtime to P0.

# Implementation readiness

The P0 direction is finalized. Begin with typed representations and the combined metadata baseline, then follow the ordered steps. Resolve routine public spelling and internal representation details through focused schemas, examples and behavioral tests. Revisit the design only if implementation demonstrates a material incompatibility.

P1/P2 remain future scope and should be refined after P0 is ready. Finalizing this document completes planning; implementation is a separate next task.
