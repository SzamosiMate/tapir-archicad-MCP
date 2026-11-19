# Command discovery

`archicad_list_commands` uses lexical search over command names and descriptions. Batch phrases for separate workflow steps in `keywords`, and use `groups` to narrow the search. This search finds commands for locating and publishing a Publisher Set.

```json
{"groups":["navigator"],"keywords":["find configured publisher sets","publish a publisher set"]}
```

- Use `list_groups: true` to get the group directory and command counts. Omit `keywords` to browse compact names.
- Pass the latest `query_id` to get more results or refine the keywords or groups. The chain skips commands already shown at the requested detail. Set `detail: "full"` to get descriptions for names found during compact browsing.
- The 12-character ID refers to an in-memory search snapshot. It can expire after 30 minutes of inactivity, be evicted under load, or become unavailable after a restart. Omit it to start a fresh search.
- Use `archicad_get_command_schema` to verify arguments and behavior before running a selected command.

## Why lexical search

Lexical + chain and Hybrid + chain each answered **19 of 20** prompts correctly after auditing the benchmark. Hybrid had a **3–4%** estimated credit advantage across the three scenarios. Lexical avoids the embedding model and vector index, and used about **74% fewer estimated credits** than the full catalogue in fresh sessions. The test ran each prompt once per variant across two rounds with slightly different agent instructions.

The bars show mean estimated credits per successful run. The search portion includes every schema probe and retry. The penalty models one additional model request per redundant command listed in the final workflow. The moderate and heavy projections add 32,000 and 128,000 warm cached tokens, respectively, to every model request. These figures use the benchmark implementation, which carried a longer continuation token.

### Empty context

![Mean credits per successful run with empty context across seven command discovery variants](images/command-discovery-empty.svg)

### Moderate prior context

![Mean credits per successful run with 32,000 cached prior tokens across seven command discovery variants](images/command-discovery-moderate.svg)

### Heavy prior context

![Mean credits per successful run with 128,000 cached prior tokens across seven command discovery variants](images/command-discovery-heavy.svg)

The full report, runner, prompts, and per-trial measurements are preserved in commit `84503cd`. Read the report with `git show 84503cd:tests/benchmarks/command_discovery/RESULTS.md`.
