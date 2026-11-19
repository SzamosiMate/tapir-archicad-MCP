# Archicad command discovery benchmark

## Decision

Ship Lexical + chain. It matched Hybrid + chain at 19 correct answers out of 20 after auditing the results. Hybrid's estimated credit advantage was about 3–4% with the modeled penalty for redundant commands. Lexical needs only the command registry. Hybrid also needs an embedding model, a vector index, and a cache preparation step.

## Setup

- Catalogue of 801 commands at baseline `20737a1`, pinned by SHA-256 in [cases.json](cases.json).
- Twenty fixed prompts per variant. Five obvious lookups, five terminology cases, four missing capabilities or names, and six workflows.
- GPT-6 Luna with high reasoning. One independent Codex CLI session per prompt and variant, for 140 trials. The five catalogue variants ran in one round and the two chain variants in another. The chain round clarified that the task was command discovery only and omitted the example empty catalogue call. The paired comparisons are descriptive.
- The agent saw the discovery and schema tools. The agent did not execute Archicad commands. Each turn had a 150-second deadline. Raised tool and Code Mode output limits kept results visible. The inference audit recorded zero truncations across the 140 high-reasoning trials.
- Earlier low-reasoning pilot runs hit Code Mode's output cap. In a replay, the server returned all 801 names while the model received only 170. The omitted middle section included the selection and clash commands.

The [runner](run.py), [prompt and grading fixture](cases.json), [reproduction instructions](README.md), and [per-trial results](results.csv) are in this directory. The runner and answer key here preserve the benchmark setup. Use the audited columns in the CSV for the corrected comparison below.

## Variants and credit estimates

All credit cells are estimated mean credits per audited successful run. Parentheses show the additional estimate for redundant commands where applicable. The last column includes that penalty.

| Variant | Retrieval strategy | Strict | Audited | Empty | 32k cached | 128k cached | 128k total |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full catalogue | All names and descriptions | 19/20 | 18/20 | 0.14899 | 0.17121 | 0.23788 | 0.23788 |
| Groups only | Group directory, one group at a time | 19/20 | 19/20 | 0.06844 | 0.10760 | 0.22507 | 0.22507 |
| Keyword only | Ranked lexical search, full catalogue on an empty query | 19/20 | 19/20 | 0.12447 | 0.14552 | 0.20868 | 0.20868 |
| Groups + keyword | Browse groups or rank within them | 18/20 | 19/20 | 0.04674 | 0.08253 | 0.18989 | 0.18989 |
| Names only | All command names in a text list | 16/20 | 19/20 | 0.05680 (+0.00162) | 0.08796 (+0.00288) | 0.18143 (+0.00667) | 0.18810 |
| Lexical + chain | Batched lexical search, optional groups, deduplicated continuation | 19/20 | 19/20 | 0.03892 (+0.00052) | 0.07176 (+0.00094) | 0.17029 (+0.00221) | 0.17249 |
| Hybrid + chain | Same interface, with lexical and MiniLM rankings fused | 20/20 | 19/20 | 0.03791 | 0.07033 | 0.16759 | 0.16759 |

Estimated credits use the benchmark's [Codex Luna Standard rates](https://learn.chatgpt.com/docs/pricing#token-rates) of 2.5 per million uncached input tokens, 0.25 per million cached input tokens, and 12.5 per million output tokens. Compute fresh-session credits from reported usage. For a prior context of size *H*, add *H* cached tokens for each observed model request. The two projections assume the prior context stays warm and is retained on every request. They keep the observed number of requests fixed.

Search costs already include schema probes, retries, and failed tool calls. For each redundant command listed in an otherwise correct final answer, the added scenario assumes one extra model request. It prices the trial's final request input and any prior history as cached, plus 1,043 uncached input and 136 output tokens. These are the separate medians from the 399 observed requests after each trial's initial request. Per-trial credit estimates are averaged over audited passes. Commands run in a batch or omitted at execution would incur a different cost.

## Tokens and elapsed time

Means, medians, and extremes use audited successful runs. Adjusted tokens subtract the first model request's actual input once per run. The median initial input was 15,572 tokens in this sample. Wall time includes searches, schema lookups, and round trips to the model.

| Variant | Total tokens mean / median | Adjusted tokens mean / median | Seconds mean / median | Fastest successful case | Slowest successful case |
| --- | ---: | ---: | ---: | --- | --- |
| Full catalogue | 117,564 / 80,553 | 101,997 / 64,988 | 13.76 / 10.27 | 5.99, story schedule | 42.13, publish tender set |
| Groups only | 98,162 / 98,949 | 82,594 / 83,393 | 20.01 / 18.59 | 11.79, 3D bounding boxes | 30.85, merge Design Options |
| Keyword only | 97,000 / 80,361 | 81,433 / 64,790 | 12.90 / 11.32 | 7.52, clash between groups | 27.83, retired type lookup |
| Groups + keyword | 78,575 / 84,669 | 63,008 / 69,112 | 18.12 / 18.03 | 10.50, story schedule | 28.26, coordination issue |
| Names only | 80,175 / 82,360 | 64,607 / 66,801 | 20.79 / 18.09 | 7.69, keynote tree | 45.73, publish tender set |
| Lexical + chain | 69,980 / 69,313 | 54,408 / 53,733 | 14.46 / 13.62 | 8.64, 3D bounding boxes | 22.88, coordination issue |
| Hybrid + chain | 69,117 / 67,711 | 53,546 / 52,152 | 14.70 / 14.39 | 8.11, selection | 28.93, OCR scan on layout |

The tender-set full-catalogue outlier used one catalogue call, two schema probes, and six model requests. It counted 303,934 tokens because later requests carried the catalogue in their context. Names only also called its catalogue once on that prompt, then made two schema probes and eight model requests for 178,897 tokens. Cached reads were cheaper and still accumulated in the raw totals.

## Failure audit

- **Render with another scene.** The answer key originally accepted `project_photo_render` with a named scene. Its schema says a named scene becomes active and stays active. The prompt required the active scene to remain unchanged throughout. Names only inspected the schema and correctly reported the missing capability. The three originally passing variants, Full catalogue and both chains, were reclassified as failures. Groups, Keyword, and Groups + keyword already failed.
- **Coordination issue.** Groups + keyword found all four commands in order and made nine MCP calls. Treat the eight-call limit as an effort signal and include all nine calls in the measured cost.
- **Read-only extras.** Names only found the required command for the active layer preset and per-solid materials, and Lexical + chain found all three commands for Fire Rating. Their answers listed three and one redundant commands, respectively. Count these answers as discovery successes and model the extra workflow cost separately.
- **Merge Design Options.** The full catalogue identified the missing one-call capability but recommended a three-command workaround. Names only claimed support with a two-command workflow. Both failed the one-call requirement.
- **Continuation IDs.** The tested IDs were 241–281 characters in the three rejected submissions. All three trials recovered or answered correctly after the failed call. The errors added measured cost. The lexical Fire Rating failure used no continuation.

## Continuation probes

On three fixed query refinements, lexical search repeated 6–8 of the previous hits without a continuation ID, and hybrid repeated 6–7. Both returned zero repeated hits with the ID. Warm median batch latency was 4.85 ms for lexical and 7.79 ms for hybrid on the benchmark host. The [probe code](probe_chains.py) measures search implementation latency separately from the agent's wall time.

The result supports shipping lexical search with continuation. A larger correctness study would need repeated trials and the same instructions for all variants.
