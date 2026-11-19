# Archicad command discovery benchmark

See the [audited findings](RESULTS.md) and [per-trial measurements](results.csv) for the seven-variant comparison.

Check whether an agent finds the full Archicad workflow or correctly reports that a capability is missing. Measure the tokens and elapsed time it takes to reach that answer. [cases.json](cases.json) contains 20 prompts and their answer key against the 801-command catalogue at the pinned baseline commit. Five are obvious lookups, five use terminology that differs from the command names, four cover missing commands or capabilities, and six require multiple commands.

## Agent instructions

Start a fresh agent for each case. Give it the instruction below and only the case's `prompt` as the user request. Keep the case ID, group, answer key, repository, and other agents' results in the runner. Expose only the variant's command discovery tool or tools and `archicad_get_command_schema`. Use Archicad 29 with Tapir 2.0.0 as fixed compatibility assumptions. Discovery and schema lookup can use the registered catalogue without a running Archicad project.

> Find the Tapir commands that would address the user's request. Assume Archicad 29 with Tapir 2.0.0. Use the available discovery tools and verify the command names from their results. You may inspect a command's schema if it helps you decide. Find commands only. Return one JSON object with `status` and `commands`. Use `supported` for an available command or workflow, `replacement` when the user asks about an absent exact command and you find its current replacement, or `no_direct_match` when the requested capability is unavailable. For `replacement`, include `absent_name` with the missing exact name. List the exact command names in a valid execution order. For `no_direct_match`, return an empty `commands` array.

Each trial starts at the first model request that receives those instructions, the user prompt, and the tool definitions. It ends at the model response that submits the JSON. Include all discovery queries, follow-ups, schema probes, failed calls, and the final response in that trial. Allow eight discovery or schema calls total, including failures. After the eighth result, allow a final response and score the trial as failed if the agent attempts another call or submits an invalid answer. Argument construction and command execution happen outside the benchmark.

## Implementations to compare

Use the same registry contents for every implementation. Verify the fixture hash by dumping `list(TOOL_DISCOVERY_CATALOG.values())` with `json.dumps(..., sort_keys=True, separators=(",", ":"))`, encoding as UTF-8, and computing SHA-256. Preserve the outer list order.

| Server flag value | Model-facing behaviour |
| --- | --- |
| `full` | Use the current `archicad_list_commands` response with all command names and descriptions as the baseline. |
| `groups` | A bare call lists groups with command counts. Pass `group` to list exact names and full descriptions for one group. |
| `keyword` | Pass `query` for exact-name lookup or lexical ranking over names and descriptions. Return up to 12 matches and the total match count. A bare call returns the full catalogue. |
| `groups-keyword` | List groups, browse one group, search globally, or search inside a group using `group` and `query`. |
| `names` | Return all exact command names as plain text, one per line. Use schema probes when needed. |
| `chain-lexical` | Batch keyword phrases, filter by a list of groups, or browse compact names. Carry `query_id` across pages and refinements. |
| `chain-hybrid` | Same tool contract and result budget as `chain-lexical`. Fuse its keyword ranking with local MiniLM cosine ranking. |

Freeze each variant before running the cases and use separate prompts when tuning it. Keep the query interface and result budget fixed when comparing rankers.

## Chain and hybrid comparison

The tool advertises the group IDs and supports `list_groups=true` for counts. `groups` narrows to the union of the listed groups. Each phrase in `keywords` gets its own ranking, and results are interleaved and deduplicated before selecting up to 12 matches. The hybrid variant uses the original `all-MiniLM-L6-v2` model with CPU inference through FastEmbed. It fuses the two rankings by reciprocal rank and considers vector hits with cosine similarity of at least 0.30.

Each reply has a `query_id` that records the compact and full results returned so far. Continue with the latest token even after editing keywords or groups. One command can appear first as a name and then with its description. A full result is returned only once per chain, and compact browsing skips commands already shown in either format. Replaying an earlier token replays that branch. Omit the token to start a new chain.

Install the optional vector dependencies into the existing venv and prepare the model and catalogue index before recording trial latency.

```powershell
uv pip install --python .venv/Scripts/python.exe fastembed==0.9.1
.venv/Scripts/python.exe tests/benchmarks/command_discovery/prepare_vectors.py --cache .tmp/tapir-discovery-vector-cache
.venv/Scripts/python.exe tests/benchmarks/command_discovery/run.py --variants chain-lexical chain-hybrid --baseline chain-lexical --vector-cache .tmp/tapir-discovery-vector-cache --output .tmp/command-discovery-chain-high
.venv/Scripts/python.exe tests/benchmarks/command_discovery/probe_chains.py --vector-cache .tmp/tapir-discovery-vector-cache --output .tmp/command-discovery-chain-high/probes.json
```

The comparison uses mean credit estimates, token counts, and elapsed time on strict passes. The [Codex Standard Luna rate card](https://learn.chatgpt.com/docs/pricing#token-rates) weights uncached input, cached input, and output separately. The fixed probes measure repeated result slots with and without a continuation token and record warm batch latency outside the agent loop.

## Run the Luna benchmark

Use the installed repository environment and a signed-in Codex CLI. Each trial is a fresh, single-turn Codex session pinned to GPT-6 Luna with high reasoning. The runner starts the actual stdio server with `--command-discovery`, exposes the list and schema tools, and captures Codex JSONL usage, the MCP transcript, and the local inference trace. It raises the per-tool and history limits and instructs the agent to set the outer Code Mode limit and render a single representation of each result.

```powershell
.venv\Scripts\python.exe tests/benchmarks/command_discovery/run.py --output .tmp/command-discovery-luna-high
```

One repetition gives 100 trials across the five variants. To repeat finalists, select them and `full` with `--variants` and choose a fresh output directory. Reuse the same output directory to resume an interrupted run with the same settings. Use `--rescore` after a run to apply answer-key corrections to saved transcripts. The output directory contains `summary.md`, `trials.jsonl`, and individual MCP and model-facing traces.

### Codex output limits

The original low-reasoning Luna pilot measured the default Code Mode presentation. The JSONL MCP events included the server's complete responses. In a follow-up inference trace with the pilot settings, Code Mode removed the middle of the full catalogue and left 170 of the 801 command names visible. The selection and collision commands were both in the omitted section. The names-only response fit in full.

To compare the full payloads under Luna, raise both the outer Code Mode `max_output_tokens` pragma and Codex's `tool_output_token_limit` setting. The per-MCP-tool override used by the pilot is a separate limit. Render a single representation of the result, then verify in the inference trace that all 801 names reached the model. A matched check on the clashes case used one catalogue call and zero schema calls per variant. Full used 79,700 tokens and names-only used 36,632, with correct command selection in both runs. [Codex rollout tracing](https://github.com/openai/codex/tree/main/codex-rs/rollout-trace)

## Capture and score

Run one repetition per variant for the broad comparison, then repeat the baseline and the strongest candidates. Pin the model version, reasoning setting, runner, result rendering, and trial deadline. Shuffle variant order within each case and repetition. Run one timed trial at a time on the same host. Start each trial with empty conversation history and record prompt-cache usage.

For per-request telemetry, a direct API runner can make the model requests itself and forward the allowed tool calls to the variant's MCP server. Capture each response's `usage`, the request start and end times, and the tool calls it generated. Log request failures and retries. Multiple MCP calls can be issued by one model response, so count model requests and MCP calls independently. [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)

For a Codex-specific comparison, run one fresh `codex exec --json` session per trial and capture `turn.completed.usage` once, plus the MCP call events. Time the interval from `turn.started` to `turn.completed` or failure. Record this as a Codex measurement series with its own baseline. The desktop collaboration results available to the parent agent do not expose the per-child usage needed for this benchmark. [Codex JSONL events](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable)

| Measure | Calculation |
| --- | --- |
| Strict pass | Require valid JSON, the expected status, a complete accepted command set with no duplicates, and any `before` pairs in the correct order. Require the expected `absent_name` only for `replacement`. Require at least one discovery call and evidence in the model-facing results for every submitted command. Record truncation and omitted command names as visibility audit failures. |
| Partial coverage | For supported and replacement cases, report the fraction of required commands that are both returned by the agent and present in discovery results. Track unknown names and false direct matches on missing cases separately. |
| Search-phase tokens | Sum provider-reported input and output tokens across every model request in the trial. This includes any context the provider counts again after tool results. Include cached input in the raw count, report cache reads and writes when available, and retain input and output subtotals. Report reasoning tokens as a breakdown of output when the provider includes them there. |
| Adjusted tokens | Subtract the first model request's reported input tokens once from the total. Subsequent requests and their repeated context remain in the comparison. |
| Search latency | Use a monotonic clock from submission of the first model request through receipt of the complete final answer or failure. Include model and network time, MCP requests, schema probes, and retry delays. Record MCP startup and index building separately if they happen before the trial. |
| Search effort | Record model requests, discovery calls, schema calls, errors, and retries. Keep the tool transcript for checking which command names the agent actually saw. |
| Tool-result payload tokens | Use the same pinned tokenizer to count the discovery result text as delivered to the model, once per delivery. Count schema probes separately. Use the actual rendered content, including any repeated representation if the runner presents it. |

Report missing usage as missing. Payload token counts are diagnostic and stay separate from search-phase totals. For latency breakdowns, timestamp model requests and MCP calls independently. Use measured elapsed time for the headline because calls can overlap. An empty ranked result is evidence only about that query. Agents can refine or broaden a search within the call limit before deciding that a capability is absent.

Report strict passes and partial coverage first. Compare arithmetic mean tokens and elapsed time on successful runs and include median, minimum, and maximum with prompt IDs. Pair each candidate trial with the full-catalogue trial for the same case and repetition. For pairs where both trials pass, report the arithmetic mean for each side and the percentage change between those means. Timeouts, malformed answers, visibility audit failures, and exhausted searches stay in the quality denominator. The trial log retains usage and latency for failed attempts.

Use correctness first when choosing which candidates to repeat. Compare pass rates, missed workflow steps and false direct matches before comparing successful-run means. Treat this fixed set as a regression benchmark and use fresh prompts to verify that a winning implementation generalizes.
