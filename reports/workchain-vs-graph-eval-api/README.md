# WorkChain vs graph authoring: private-IR / flat-input API eval

## Unpack the complete raw artifacts

Full agent logs, HTML sessions, submissions, evaluator fixtures and source manifests are preserved in
`evaluation-logs.tar.xz`; they are not discarded. Unpack them before following the raw-artifact links or rerun instructions:

```bash
(cd reports/workchain-vs-graph-eval-api && \\
  sha256sum -c evaluation-logs.tar.xz.sha256 && tar -xJf evaluation-logs.tar.xz)
```

The small result/metadata files below remain directly readable without extraction.


## Results versus the immediately previous pair

Two fresh Pi processes solved the same bounded adaptive relaxation task in separate source snapshots and new sessions.
Same model: `openai-codex/gpt-6.1-sol`, medium thinking; same tools, prompts, collaborators and 13 acceptance cases.
The new revision is `596d86aa4`, with validation-only `build()`, flat node inputs and the discoverable authoring recipe.
The previous pair is [workchain-vs-graph-eval-after](../workchain-vs-graph-eval-after/README.md).

| Arm | Solve seconds: previous → current | Total tokens: previous → current | Estimated USD: previous → current |
|---|---:|---:|---:|
| WorkChain | 113.0 → 124.9 | 76,743 → 109,017 | $0.0697 → $0.0849 |
| Graph | 151.5 → 116.5 | 207,414 → 91,193 | $0.1386 → $0.0529 |

The graph attempt took **23.1% less time**, used **56.0% fewer total tokens**, and had **61.8% lower estimated cost**.
These are observed changes in one pair, not statistically significant or causal estimates.
WorkChain's numbers increased, illustrating agent/provider variability.

| Current arm | Noncached input | Output | Cached read | Model turns | Common acceptance | All independent tests |
|---|---:|---:|---:|---:|---:|---:|
| WorkChain | 23,336 | 2,993 | 82,688 | 12 | 13/13 | 22/22 |
| Graph | 11,703 | 2,178 | 77,312 | 9 | 13/13 | 30/30 |

Total tokens include repeated cached context. Cost is Pi's usage-based estimate, not an invoice.
Solve time includes the agent's discovery, reasoning, edits and own tests, but not independent validation.
All-tests counts differ because each agent wrote different additional tests; shared acceptance is identical.

## Workflow execution memory and CPU caches

New instrumented reruns executed all 13 shared cases three times per implementation, each in a fresh Python process
and temporary SQLite profile. These are workflow execution measurements, not coding-agent resource measurements.

| Implementation | Executions | Maximum observed RSS | Median per-run peak RSS | L1 data | L2 | L3/LLC |
|---|---:|---:|---:|---|---|---|
| WorkChain | 39 | 118.17 MiB | 116.79 MiB | Unavailable | Unavailable | Unavailable |
| Graph | 39 | 120.39 MiB | 118.71 MiB | Unavailable | Unavailable | Unavailable |

RSS is the Linux high-water mark during `run_get_node`, including the resident Python/AiiDA baseline and child tasks.
Initialization and later validation are outside this window; process-wide peaks through completion are also recorded.
All 78 executions finished successfully and verified their results, budgets and provenance. These small-workload maxima
are observations, not memory limits or a statistically significant comparison.

**L1/L2/L3 usage counters could not be collected:** this host blocks `perf` with `kernel.perf_event_paranoid=4`.
Counter fields are null/unavailable, not zero. Hardware cache capacities are recorded separately and are not usage.
See [resource results and boundaries](runtime-resources/README.md), [raw summary](runtime-resources/summary.json),
[WorkChain resource JSON](workchain/execution-resources.json), and [graph resource JSON](graph/execution-resources.json).
The reproducible profiler attempts supported accesses/misses counters automatically on a machine with perf permission.
Original agent time, token and cost metrics remain unchanged.

## Conclusions

The graph agent found the new skill and canonical recipe first, used the supported compact loop syntax,
validated with `build()` before execution, and needed no solution or test corrections.
The old input-inspection correction cycle did not recur.

**The strongest remaining measured opportunity is test parallelism:** an additional fixed-submission probe ran all
30 unchanged graph tests four times (serial / two workers / two workers / serial). Mean test time fell from
45.69 to 26.44 seconds with two workers: **42.1%, about 19 seconds**, without dropping tests.
This probe is separate from the agent results; no end-to-end agent speedup from parallelism is claimed.

More targeted reads of the canonical recipe/reference, a conventional WorkChain quickstart, and avoiding unavailable
lint commands are plausible smaller improvements. No further broad graph-language redesign is supported by this run.

Read [analysis.md](analysis.md) for the detailed evidence, cache caveats, ranked improvements and limitations.

## Artifacts

Each of `graph/` and `workchain/` contains:

- `prompt.md`, `invocation.json`: complete task/style prompt and process invocation.
- `events.jsonl`: complete streamed agent log with tool calls/results and model usage.
- `sessions/*.jsonl`, `session.html`: full persisted session and browsable export.
- `stderr.log`, `assistant-text.md`: diagnostics and all assistant text.
- `metrics.json`: time, token categories, estimated cost, exit codes and fixed-file integrity.
- `submission/`, `solution.patch`: complete submitted source/tests and diff against the starting snapshot.
- `validation.log`, `validation.xml`: independently rerun shared acceptance and agent-authored tests.
- `trace.json`: per-turn usage and per-tool commands/paths, output sizes and durations.

Shared artifacts:

- [task.md](task.md), `collaborators.py`, `test_acceptance.py`: unchanged evaluation contract and fixtures.
- `run.json`, `baseline-manifest.json`: revision, model/harness settings and copied source hashes.
- `results.json`, `comparison.json`, [comparison.md](comparison.md): results and detailed previous/current comparison.
- `audit.json`: session/event usage agreement, new-session separation and evaluator integrity checks.
- `test-timing-probe/`: post-hoc timing commands, logs, JUnit XML and summary.
- `run_eval.py`, `analyze.py`, `timing_probe.py`: reproducible runner and analysis/probe scripts.
- `profile_execution.py`, `measure_resources.py`, `runtime-resources/`: workflow RSS and cache-counter profiling,
  all per-execution data/logs, hardware permissions/capacities, source-integrity checks and profiler tests.
- [methodology.md](methodology.md): isolation, measurement definitions and comparison limits.

## Reproduce

Requires the existing project environment, Pi and configured provider credentials.
Use a new report directory so these results remain immutable:

```bash
mkdir -p reports/workchain-vs-graph-eval-next
source=reports/workchain-vs-graph-eval-api
cp "$source"/{run_eval.py,task.md,collaborators.py,test_acceptance.py} reports/workchain-vs-graph-eval-next/
uv run --no-sync python reports/workchain-vs-graph-eval-next/run_eval.py
```

`PI_PROVIDER`, `PI_MODEL` and `PI_REASONING_LEVEL` select the shared model settings.
The working copies are retained under the temporary path in `run.json`.
`uv run --no-sync python reports/workchain-vs-graph-eval-api/analyze.py` regenerates the machine comparison and HTML
exports; `timing_probe.py` reruns the additional fixed-submission timing probe, not the agents.
