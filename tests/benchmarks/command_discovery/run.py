"""Compare command discovery variants in isolated, single-turn Codex runs."""

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path
from queue import Empty, Queue
from statistics import mean, median
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic

import tapir_archicad_mcp.model_configuration  # noqa: F401
from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG

HERE = Path(__file__).resolve().parent
DISCOVERY = "archicad_list_commands"
SCHEMA = "archicad_get_command_schema"
DEFAULT_VARIANTS = ("full", "groups", "keyword", "groups-keyword", "names")
VARIANTS = (*DEFAULT_VARIANTS, "chain-lexical", "chain-hybrid")
LUNA_STANDARD_RATES = (2.5, 0.25, 12.5)
CALL_LIMIT = 8
OUTPUT_LIMIT = 160000
RENDER_INSTRUCTIONS = """Start every Code Mode cell that calls Tapir with this first line:
// @exec: {"max_output_tokens": 160000}
Assign each tool result to result, then render it once without filtering or rewriting it:
text(result.structuredContent ?? result.structured_content ?? result.content);
Use the active tool's advertised arguments. When independent lookups are useful, you may issue them together."""
TRUNCATION_MARKER = re.compile(r"[\d,]+ tokens truncated|[\d,]+ bytes omitted|output was truncated", re.IGNORECASE)


def trial_command(codex, variant, prompt, model, reasoning, cwd, vector_cache):
    command = [
        codex,
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "--cd",
        str(cwd),
        "-c",
        f"model_reasoning_effort={json.dumps(reasoning)}",
        "-c",
        "mcp_servers.tapir.required=true",
        "-c",
        "mcp_servers.tapir.startup_timeout_sec=30",
        "-c",
        f"mcp_servers.tapir.command={json.dumps(sys.executable)}",
        "-c",
        "mcp_servers.tapir.args=" + json.dumps(["-m", "tapir_archicad_mcp.server", "--command-discovery", variant]),
        "-c",
        f"mcp_servers.tapir.enabled_tools={json.dumps([DISCOVERY, SCHEMA])}",
        "-c",
        f"tool_output_token_limit={OUTPUT_LIMIT}",
        "-c",
        f"mcp_servers.tapir.tools.{DISCOVERY}.output_token_limit={OUTPUT_LIMIT}",
        "-c",
        f"mcp_servers.tapir.tools.{SCHEMA}.output_token_limit={OUTPUT_LIMIT}",
    ]
    if variant == "chain-hybrid" and vector_cache:
        command.extend(["-c", f"mcp_servers.tapir.env.TAPIR_DISCOVERY_VECTOR_CACHE={json.dumps(str(vector_cache))}"])
    return [*command, prompt]


def read_events(command, cwd, trace, timeout, inference_root):
    """Collect JSONL events and time the Codex turn, with a separate startup deadline."""
    lines = Queue()
    started = None
    events = []
    timed_out = False
    with (
        trace.open("w", encoding="utf-8") as event_log,
        trace.with_suffix(".stderr.log").open("wb") as stderr,
        subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=stderr,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "CODEX_ROLLOUT_TRACE_ROOT": str(inference_root)},
        ) as process,
    ):

        def read_stdout():
            with process.stdout as output:
                for line in output:
                    lines.put((monotonic(), line))
            lines.put((monotonic(), None))

        Thread(target=read_stdout, daemon=True).start()
        deadline = monotonic() + 45
        ended = None
        try:
            while True:
                timestamp, line = lines.get(timeout=max(0, deadline - monotonic()))
                if line is None:
                    break
                event_log.write(line)
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                events.append(event)
                if event.get("type") == "turn.started":
                    started = timestamp
                    deadline = started + timeout
                elif event.get("type") in {"turn.completed", "turn.failed"}:
                    ended = timestamp
                    break
        except Empty:
            timed_out = True
            ended = monotonic()
        finally:
            try:
                process.wait(timeout=3 if ended is not None else 0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    elapsed = (ended or monotonic()) - started if started is not None else None
    return events, elapsed, timed_out


def read_inference(root):
    """Extract provider usage and model-facing tool output from this trial's local trace."""
    requests = 0
    usages = []
    outputs = []
    for trace in sorted(root.glob("trace-*/trace.jsonl")):
        for line in trace.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)["payload"]
            if event["type"] == "inference_started":
                requests += 1
                request = json.loads((trace.parent / event["request_payload"]["path"]).read_text(encoding="utf-8"))
                for item in request.get("input", []):
                    if item.get("type") not in {"custom_tool_call_output", "function_call_output"}:
                        continue
                    output = item.get("output", [])
                    if isinstance(output, str):
                        outputs.append(output)
                    else:
                        outputs.extend(block["text"] for block in output if block.get("type") == "input_text")
            elif event["type"] == "inference_completed":
                response = json.loads((trace.parent / event["response_payload"]["path"]).read_text(encoding="utf-8"))
                if response.get("token_usage"):
                    usages.append(response["token_usage"])
    visible = set()
    for output in outputs:
        normalized = output.replace("\\n", "\n").replace("\\r", "\n")
        visible.update(name for name in re.findall(r"[a-z][a-z0-9_]+", normalized) if name in TOOL_DISCOVERY_CATALOG)
    return {
        "model_requests": requests,
        "request_usage": usages,
        "first_input_tokens": usages[0]["input_tokens"] if usages else None,
        "visible_names": visible,
        "truncated": any(TRUNCATION_MARKER.search(output) for output in outputs),
        "tool_output_seen": bool(outputs),
    }


def names_in_payload(value):
    if isinstance(value, str):
        if value.startswith(("{", "[")):
            try:
                yield from names_in_payload(json.loads(value))
            except json.JSONDecodeError:
                pass
        else:
            yield from (line for line in value.splitlines() if line in TOOL_DISCOVERY_CATALOG)
    elif isinstance(value, dict):
        if value.get("name") in TOOL_DISCOVERY_CATALOG:
            yield value["name"]
        for key in ("text", "content", "names", "matches", "result", "structuredContent", "structured_content"):
            yield from names_in_payload(value.get(key))
    elif isinstance(value, list):
        for item in value:
            yield from names_in_payload(item)


def grade(case, events, elapsed, timed_out, inference=None):
    items = [event["item"] for event in events if event.get("type") == "item.completed"]
    tools = [item for item in items if item.get("type") == "mcp_tool_call"]
    discovery = [item for item in tools if item.get("tool") == DISCOVERY and item.get("server") == "tapir"]
    schemas = [item for item in tools if item.get("tool") == SCHEMA and item.get("server") == "tapir"]
    continuations = [item for item in discovery if item.get("arguments", {}).get("query_id")]
    known = {name for item in discovery for name in names_in_payload(item.get("result"))}
    audit = {}
    if inference is not None:
        missing = sorted(known - inference["visible_names"])
        audit = {key: value for key, value in inference.items() if key != "visible_names"}
        audit["omitted_command_count"] = len(missing)
        audit["visibility_verified"] = (
            bool(inference["request_usage"])
            and (not discovery or inference["tool_output_seen"])
            and not inference["truncated"]
            and not missing
        )
        known &= inference["visible_names"]
    unexpected = len(tools) != len(discovery) + len(schemas) or any(
        item.get("type") in {"command_execution", "file_change", "web_search", "collab_tool_call"} for item in items
    )
    usage = next((event["usage"] for event in events if event.get("type") == "turn.completed"), None)
    completed = any(event.get("type") == "turn.completed" for event in events)
    final = next((item["text"] for item in reversed(items) if item.get("type") == "agent_message"), "")
    try:
        answer = json.loads(final)
    except json.JSONDecodeError:
        answer = None

    expected = case["expected"]
    valid = (
        isinstance(answer, dict)
        and isinstance(answer.get("commands"), list)
        and all(isinstance(name, str) for name in answer["commands"])
    )
    commands = answer["commands"] if valid else []
    submitted = set(commands)
    command_sets = [expected["commands"], *expected.get("alternative_command_sets", [])]
    targets = max(map(set, command_sets), key=lambda option: (option == submitted, len(option & submitted & known)))
    passed = (
        valid
        and completed
        and not timed_out
        and not unexpected
        and audit.get("visibility_verified", True)
        and 1 <= len(discovery)
        and len(tools) <= CALL_LIMIT
        and answer.get("status") == expected["status"]
        and answer.get("absent_name") == expected.get("absent_name")
        and len(commands) == len(targets)
        and submitted == targets
        and submitted <= known
        and all(commands.index(first) < commands.index(second) for first, second in expected.get("before", []))
    )
    return {
        "passed": passed,
        "answer": answer,
        "grounded_required": sorted(targets & known & submitted),
        "required_commands": len(targets),
        "unknown_names": sorted(submitted - TOOL_DISCOVERY_CATALOG.keys()),
        "false_direct_match": bool(
            expected["status"] == "no_direct_match" and valid and (answer.get("status") == "supported" or commands)
        ),
        "discovery_calls": len(discovery),
        "schema_calls": len(schemas),
        "chain_calls": len(continuations),
        "accepted_chain_calls": sum(item.get("status") == "completed" for item in continuations),
        "batch_calls": sum(len(item.get("arguments", {}).get("keywords") or []) > 1 for item in discovery),
        "tool_errors": sum(item.get("status") == "failed" for item in tools),
        "unexpected_tool": unexpected,
        "elapsed_seconds": elapsed,
        "timeout": timed_out,
        "usage": usage,
        **audit,
    }


def totals(trial):
    usage = trial["usage"]
    return usage["input_tokens"] + usage["output_tokens"] if usage is not None else None


def adjusted(trial):
    total = totals(trial)
    initial = trial.get("first_input_tokens")
    return total - initial if total is not None and initial is not None else None


def estimate_credits(trial):
    usage = trial["usage"]
    if usage is None:
        return None
    ordinary, cached, output = LUNA_STANDARD_RATES
    return (
        ordinary * (usage["input_tokens"] - usage["cached_input_tokens"])
        + cached * usage["cached_input_tokens"]
        + output * usage["output_tokens"]
    ) / 1_000_000


def elapsed_time(trial):
    return trial["elapsed_seconds"]


def average(values, precision=0):
    observed = [value for value in values if value is not None]
    return f"{mean(observed):,.{precision}f}" if observed else "—"


def paired_means(pairs, measure, precision=0):
    observed = [(measure(left), measure(right)) for left, right in pairs]
    observed = [(left, right) for left, right in observed if left is not None and right is not None]
    if not observed:
        return "—"
    before, after = map(mean, zip(*observed, strict=True))
    delta = f"{100 * (after - before) / before:+.1f}%" if before else "—"
    return f"{before:,.{precision}f} → {after:,.{precision}f} ({delta})"


def distribution(trials, measure, precision):
    observed = [(value, row) for row in trials if (value := measure(row)) is not None]
    if not observed:
        return "— | — | — | —"
    values = [value for value, _ in observed]
    extremes = [choose(observed, key=lambda item: item[0]) for choose in (min, max)]
    endpoints = [f"{value:,.{precision}f} ({row['case']}, run {row['repetition']})" for value, row in extremes]
    return " | ".join([f"{mean(values):,.{precision}f}", f"{median(values):,.{precision}f}", *endpoints])


def report(results, metadata):
    manifest = f"{metadata['model']}, {metadata['reasoning']} reasoning, {metadata['timeout']} s turn deadline"
    baseline_variant = metadata.get("baseline", "full")
    credit_measure = estimate_credits if metadata["model"] == "gpt-6-luna" else lambda _: None
    by_variant = {variant: [row for row in results if row["variant"] == variant] for variant in VARIANTS}
    by_variant = {variant: rows for variant, rows in by_variant.items() if rows}
    successes = {variant: [row for row in trials if row["passed"]] for variant, trials in by_variant.items()}
    lines = [
        "# Command discovery benchmark",
        "",
        manifest,
        "",
        "All means use strict passes. Estimated credits use GPT-6 Luna Standard rates on observed uncached input, cached input, and output. Adjusted tokens subtract first-request input once.",
        "",
        "| Variant | Strict passes | Command coverage | Mean estimated credits | Mean total tokens | Mean adjusted tokens | Mean seconds | Timeouts | Visibility audit failures |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant, trials in by_variant.items():
        successful = successes[variant]
        required = sum(row["required_commands"] for row in trials)
        covered = sum(len(row["grounded_required"]) for row in trials)
        lines.append(
            f"| {variant} | {len(successful)}/{len(trials)} | {covered}/{required} | "
            f"{average(map(credit_measure, successful), 4)} | {average(map(totals, successful))} | "
            f"{average(map(adjusted, successful))} | {average(map(elapsed_time, successful), 2)} | "
            f"{sum(row['timeout'] for row in trials)} | {sum(row.get('visibility_verified') is False for row in trials)} |"
        )

    lines += [
        "",
        "## Matched successful prompts",
        "",
        f"Each cell compares `{baseline_variant}` and candidate means on the same successful case and repetition pairs.",
        "",
        "| Variant | Pairs both correct | Mean estimated credits | Mean total tokens | Mean adjusted tokens | Mean seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    baseline = {(row["case"], row["repetition"]): row for row in successes.get(baseline_variant, [])}
    for variant, successful in successes.items():
        if variant == baseline_variant:
            continue
        pairs = [(baseline[key], row) for row in successful if (key := (row["case"], row["repetition"])) in baseline]
        lines.append(
            f"| {variant} | {len(pairs)} | {paired_means(pairs, credit_measure, 4)} | {paired_means(pairs, totals)} | "
            f"{paired_means(pairs, adjusted)} | {paired_means(pairs, elapsed_time, 2)} |"
        )

    lines += [
        "",
        "## Successful-run distribution",
        "",
        "| Variant | Measure | Mean | Median | Minimum | Maximum |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for variant, successful in successes.items():
        for name, measure, precision in (
            ("Total tokens", totals, 0),
            ("Adjusted tokens", adjusted, 0),
            ("Seconds", elapsed_time, 2),
        ):
            lines.append(f"| {variant} | {name} | {distribution(successful, measure, precision)} |")

    lines += [
        "",
        "## Search effort on successful runs",
        "",
        "| Variant | Mean model requests | Mean catalogue calls | Mean schema calls | Mean attempted continuations | Mean batch calls | Mean cached input tokens | Mean reasoning output tokens |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variant, successful in successes.items():
        metrics = [
            average((row.get(key) for row in successful), 1)
            for key in ("model_requests", "discovery_calls", "schema_calls", "chain_calls", "batch_calls")
        ]
        metrics += [
            average(row["usage"].get(key) for row in successful if row["usage"])
            for key in ("cached_input_tokens", "reasoning_output_tokens")
        ]
        lines.append(f"| {variant} | " + " | ".join(metrics) + " |")

    chain_variants = {name: trials for name, trials in by_variant.items() if name.startswith("chain-")}
    if chain_variants:
        lines += [
            "",
            "## Continuation use",
            "",
            "| Variant | Trials with a batch | Trials that attempted a continuation | Accepted continuations | Rejected continuations |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for variant, trials in chain_variants.items():
            attempted = sum(row.get("chain_calls", 0) for row in trials)
            accepted = sum(row.get("accepted_chain_calls", 0) for row in trials)
            batched_trials = sum(row.get("batch_calls", 0) > 0 for row in trials)
            chained_trials = sum(row.get("chain_calls", 0) > 0 for row in trials)
            lines.append(f"| {variant} | {batched_trials} | {chained_trials} | {accepted} | {attempted - accepted} |")

    lines += [
        "",
        "## Results by task type",
        "",
        "| Variant | Group | Passes | False direct matches | Mean adjusted tokens on passes | Mean seconds on passes |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for variant, trials in by_variant.items():
        for group in dict.fromkeys(row["group"] for row in trials):
            subset = [row for row in trials if row["group"] == group]
            successful = [row for row in subset if row["passed"]]
            lines.append(
                f"| {variant} | {group} | {len(successful)}/{len(subset)} | "
                f"{sum(row['false_direct_match'] for row in subset)} | {average(map(adjusted, successful))} | "
                f"{average(map(elapsed_time, successful), 2)} |"
            )

    lines += [
        "",
        "## Results by prompt",
        "",
        "Each cell shows strict passes, mean adjusted tokens, and mean seconds for successful runs.",
        "",
        "| Prompt | " + " | ".join(by_variant) + " |",
        "| --- | " + " | ".join("---:" for _ in by_variant) + " |",
    ]
    for case in dict.fromkeys(row["case"] for row in results):
        cells = []
        for trials in by_variant.values():
            subset = [row for row in trials if row["case"] == case]
            successful = [row for row in subset if row["passed"]]
            metrics = f"{average(map(adjusted, successful))} · {average(map(elapsed_time, successful), 2)}"
            cells.append(f"{len(successful)}/{len(subset)} · {metrics}" if subset else "—")
        lines.append(f"| {case} | " + " | ".join(cells) + " |")

    lines += ["", "## Failed trials", ""]
    for row in results:
        if not row["passed"]:
            notes = []
            if row["timeout"]:
                notes.append("timed out")
            if row.get("visibility_verified") is False:
                notes.append(f"visibility audit failed, {row['omitted_command_count']} missing names")
            if row.get("truncated"):
                notes.append("model-facing output truncated")
            if (calls := row["discovery_calls"] + row["schema_calls"]) > CALL_LIMIT:
                notes.append(f"{calls} MCP calls exceeded the {CALL_LIMIT}-call budget")
            if row.get("usage") is None:
                notes.append("usage unavailable")
            detail = f" ({', '.join(notes)})" if notes else ""
            answer = json.dumps(row["answer"], ensure_ascii=False).replace("`", "'")
            lines.append(f"- {row['variant']} / {row['case']} / run {row['repetition']}{detail} · `{answer}`")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--reasoning", default="high")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=150)
    parser.add_argument("--variants", nargs="+", choices=VARIANTS, default=DEFAULT_VARIANTS)
    parser.add_argument("--baseline", choices=VARIANTS, default="full")
    parser.add_argument("--vector-cache", type=Path)
    parser.add_argument("--cases", nargs="+")
    parser.add_argument("--rescore", action="store_true", help="Regrade saved transcripts without running agents.")
    args = parser.parse_args()
    fixture = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    catalogue = json.dumps(list(TOOL_DISCOVERY_CATALOG.values()), sort_keys=True, separators=(",", ":"))
    if hashlib.sha256(catalogue.encode()).hexdigest() != fixture["catalogue"]["sha256"]:
        parser.error("The installed catalogue does not match the fixture snapshot.")
    cases = [case for case in fixture["cases"] if not args.cases or case["id"] in args.cases]
    if not cases or args.repetitions < 1 or args.timeout < 1:
        parser.error("Provide valid cases and positive repetitions and timeout.")

    output = args.output.resolve()
    trials_file = output / "trials.jsonl"
    metadata_file = output / "run.json"
    results = (
        [json.loads(line) for line in trials_file.read_text(encoding="utf-8").splitlines()]
        if trials_file.exists()
        else []
    )
    if args.rescore:
        if not results or not metadata_file.is_file():
            parser.error("There are no saved trials to regrade.")
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        if metadata["catalogue_sha256"] != fixture["catalogue"]["sha256"]:
            parser.error("These trials use a different catalogue snapshot.")
        case_by_id = {case["id"]: case for case in fixture["cases"]}
        for row in results:
            trace = output / "traces" / f"{row['repetition']}-{row['case']}-{row['variant']}.jsonl"
            events = [
                json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines() if line.startswith("{")
            ]
            root = output / "inference" / trace.stem
            inference = read_inference(root) if metadata.get("trace_inference") else None
            row.update(grade(case_by_id[row["case"]], events, row["elapsed_seconds"], row["timeout"], inference))
        rescored = trials_file.with_suffix(".rescored.jsonl")
        rescored.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in results), encoding="utf-8")
        rescored.replace(trials_file)
        (output / "summary.md").write_text(report(results, metadata), encoding="utf-8")
        return

    codex = shutil.which("codex")
    if codex is None:
        parser.error("Codex CLI is required on PATH.")
    (output / "traces").mkdir(parents=True, exist_ok=True)
    instruction = next(
        line[2:] for line in (HERE / "README.md").read_text(encoding="utf-8").splitlines() if line.startswith("> ")
    )
    instruction += (
        f" Treat the user request as a workflow description. Stop once you verify the command names. "
        f"Use only the Tapir discovery and schema tools and make at most {CALL_LIMIT} tool calls."
    )
    instruction += "\n\n" + RENDER_INSTRUCTIONS
    vector_cache = args.vector_cache.resolve() if args.vector_cache else None
    metadata = {
        "model": args.model,
        "reasoning": args.reasoning,
        "timeout": args.timeout,
        "catalogue_sha256": fixture["catalogue"]["sha256"],
        "fixture_sha256": hashlib.sha256(json.dumps(fixture, sort_keys=True).encode()).hexdigest(),
        "output_limit": OUTPUT_LIMIT,
        "trace_inference": True,
        "baseline": args.baseline,
        "vector_cache": str(vector_cache) if vector_cache else None,
        "instruction_sha256": hashlib.sha256(instruction.encode()).hexdigest(),
    }
    if metadata_file.exists() and json.loads(metadata_file.read_text(encoding="utf-8")) != metadata:
        parser.error("Existing trials use different settings. Choose a fresh output directory.")
    metadata_file.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    completed = {(row["case"], row["variant"], row["repetition"]) for row in results}
    with trials_file.open("a", encoding="utf-8") as log:
        for repetition in range(1, args.repetitions + 1):
            for case in cases:
                variants = list(args.variants)
                random.Random(f"{case['id']}:{repetition}").shuffle(variants)
                for variant in variants:
                    if (case["id"], variant, repetition) in completed:
                        continue
                    trace = output / "traces" / f"{repetition}-{case['id']}-{variant}.jsonl"
                    inference_root = output / "inference" / trace.stem
                    with TemporaryDirectory(prefix="tapir-agent-") as cwd:
                        prompt = f"{instruction}\n\nUser request:\n{case['prompt']}"
                        command = trial_command(codex, variant, prompt, args.model, args.reasoning, cwd, vector_cache)
                        events, elapsed, timed_out = read_events(command, cwd, trace, args.timeout, inference_root)
                    row = grade(case, events, elapsed, timed_out, read_inference(inference_root))
                    row.update(case=case["id"], group=case["group"], variant=variant, repetition=repetition)
                    results.append(row)
                    log.write(json.dumps(row, ensure_ascii=False) + "\n")
                    log.flush()
                    (output / "summary.md").write_text(report(results, metadata), encoding="utf-8")
                    print(
                        f"{repetition} {case['id']} {variant}: {'pass' if row['passed'] else 'fail'}, "
                        f"{totals(row)} tokens, {elapsed if elapsed is not None else 'no turn'} s",
                        flush=True,
                    )
                    if not events or (elapsed is None and row["usage"] is None):
                        raise SystemExit(
                            f"Codex failed before the trial started. See {trace.with_suffix('.stderr.log')}"
                        )


if __name__ == "__main__":
    main()
