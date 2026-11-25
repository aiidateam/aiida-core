# Analysis and remaining opportunities

## What changed in the measured pair

The comparison is with `../workchain-vs-graph-eval-after/`, the immediately previous final pair, not the original pilot or the pre-language-improvement run.

| Metric | Graph: previous → current | Change |
|---|---:|---:|
| Agent solve time | 151.5 → 116.5 s | -23.1% |
| Total tokens, including cache | 207,414 → 91,193 | -56.0% |
| Noncached input tokens | 51,067 → 11,703 | -77.1% |
| Output tokens | 2,107 → 2,178 | +3.4% |
| Cached-read tokens | 154,240 → 77,312 | -49.9% |
| Pi-reported estimated cost | $0.1386 → $0.0529 | -61.8% |
| Completed model turns | 14 → 9 | -35.7% |
| Discovery tool output before first edit | 33,798 → 20,550 characters | -39.2% |
| All tool output | 61,742 → 22,262 characters | -63.9% |
| Time inside test commands | 78.2 → 50.2 s | -35.8% |

Both graph submissions pass the same 13 acceptance cases. The current graph agent additionally wrote 17 tests (16 runtime parameter combinations plus a build smoke test), versus 10 additional tests last time. It was not given less work or fewer shared acceptance cases.

The WorkChain control went the other way: 113.0 → 124.9 seconds, 76,743 → 109,017 total tokens, $0.0697 → $0.0849, and 9 → 12 model turns. It passed the same acceptance suite plus nine own tests in both runs. This is evidence of substantial run-to-run agent/provider variability; these measurements cannot establish statistical significance or a causal speedup.

## Concrete evidence that the intended changes helped this attempt

1. **Discovery worked.** The graph agent's first tool call read `.agents/skills/authoring-graphs/SKILL.md`. It then read the collaborators and canonical `test_authoring_recipe.py`, not historical loop fixtures or compiler internals. It consulted the relevant guide section and writing-tests skill before writing its solution.
2. **The implementation uses the intended public authoring API.** It uses direct constants, an iteration-local `step`, and `while value != target and attempts < max_steps`. No internal IR calls, counter-arithmetic hacks, helper predicate processes, or duplicated finalizer placements were needed.
3. **Validation-first was adopted.** The agent wrote `assert workflow.build() is None` and ran `pytest .../test_solution.py -k build` before executing scientific children in the full suite. That smoke check passed; the full suite also passed on the first attempt. Build did not discover an error this time, so its error-prevention value is not quantified by this run.
4. **Flat node input inspection worked.** Its own tests read `root.inputs[name]` directly. The previous run's first own-test attempt failed ten times on `root.inputs.initial`, then needed inspection and a correction to `graph_inputs`. That correction cycle is absent now.
5. **No solution or test corrections were needed.** The graph agent wrote each file once and did not edit either. There were no graph-language errors or failed pytest runs. The WorkChain solution also passed first time.

About 28 seconds of the observed 35-second graph solve-time reduction coincides with less time in test tools. Most of that is explained by avoiding the previous full-suite rerun after the input-access mistake. This is an arithmetic decomposition of these logs, not a controlled attribution experiment.

## Why cost fell more than time

Current graph estimated cost consists of $0.023406 for input, $0.021780 for output, and $0.0077312 for cached reads. Generated output actually grew slightly, so shorter generated code is not the reason for the cost reduction. There were fewer turns, smaller accumulated context, and better reported cache reuse.

The previous final answer alone reported 22,829 noncached input tokens for 88 output tokens. The new final answer reports 256 noncached input plus 12,288 cached tokens for 95 output tokens. We do not know why caching was unavailable in the earlier call and cannot attribute that entire difference to an API change.

All dollar figures use Pi's `usage.cost.total` estimates. The records have no populated provider-authoritative billing total (`totalFromProvider` is zero); they are not invoice amounts. Context character counts are directly measured tool text, not estimates of token counts.

## Remaining improvements, ranked

### 1. A measured, meaningful time opportunity: modest pytest parallelism

Testing still occupies about 50 of the 116 seconds of the current graph solve. To investigate without changing the agent benchmark, the evaluator reran the **unchanged 30-test submission** after both agents finished, using serial / two workers / two workers / serial order:

| Execution | Repeat 1 | Repeat 2 | Mean |
|---|---:|---:|---:|
| Serial | 46.29 s | 45.09 s | 45.69 s |
| `pytest -n 2` | 26.50 s | 26.39 s | 26.44 s |

All 30 tests passed on all four runs. Two workers reduced this fixed test workload by **42.1%, about 19.2 seconds**. Full commands, logs and JUnit XML are in `test-timing-probe/`.

**Recommendation:** after the cheap build check, recommend a small worker count for independent database-backed test cases with the existing per-worker profile fixtures. Keep scientific task execution and provenance unchanged; do not remove tests to improve the number. Avoid spawning half of a very large host's CPUs for a small suite.

The measured saving is about 16% of the observed agent solve time if everything else were unchanged. That is a plausible end-to-end opportunity, not a measured new agent result. Parallelism alone does not meaningfully reduce model tokens or cost. Two repeats per mode are not a statistically powered performance study.

### 2. A plausible smaller token opportunity: eliminate redundant discovery material

The graph agent still read the full 6,233-character canonical module, including its tests, and another 8,443 characters of the reference guide. Together with the compact skill and test-writing skill, discovery output was 20,550 characters before the first file was written.

**Recommendation:** keep the default reading path to the skill and the relevant workflow/collaborator section. Put a clear stopping point before unrelated test details and consult the reference only for a specific unresolved contract question. A compact standalone canonical source section with separate tests could make targeted reads easier. Do not duplicate an entire tutorial in the skill itself.

This should reduce context and possibly turns, but no further ablation was performed. With no test failures and only nine model turns left, this does not support another order-of-magnitude savings claim.

### 3. WorkChain discovery also has avoidable navigation

The WorkChain agent spent 17,761 characters of discovery output and several calls searching examples, fixtures, specification typing and provenance access. It tried nonexistent example paths before finding the right modules. It had no implementation failure.

**Recommendation:** a similarly compact conventional WorkChain entry point covering `define`/outline, `ToContext`, context state, spec typing and returned-node identity may reduce that navigation. The sample alone does not prove how much it would save.

### 4. Stop attempting an unavailable direct Ruff executable

Both agents attempted `uv run --no-sync ruff ...`, although Ruff is not installed in the shared environment. The shell command ended with `git status`, so its overall successful exit masks the Ruff spawn failure in a simple tool-error count. Both agents correctly disclosed this limitation.

Use the already-working project pre-commit hooks, or provision the intended lint tooling before the benchmark. This removes noise and uncertainty but is only a small opportunity: the failed command took about 0.05 seconds and was combined with the useful final status check. It does not explain the remaining 116-second solve time.

## Bottom line

There is a substantial **measured testing-time opportunity** and a smaller, plausible **discovery/context opportunity**. This run does not justify further broad graph-language or public-API redesign for performance: the authoring and inspection failures targeted by the last changes are gone from this attempt.

For defensible claims about agent productivity, run multiple fresh matched pairs on the same revision and add tasks outside this bounded-loop recipe (for example declared-failure recovery and CalcJob orchestration). The new guide intentionally matches this workflow family; success here is evidence of discoverability for that pattern, not unseen-task generalization. Keep correctness, tests and provenance checks fixed, and report cache-sensitive estimated cost separately from elapsed time.

## Added workflow resource measurements

A subsequent isolated execution experiment runs each finished implementation on the same 13 cases, three times per case. All 78 executions succeed with checked results and provenance. Maximum observed workflow-window RSS is **118.17 MiB for WorkChain** and **120.39 MiB for graph**; median per-run peaks are 116.79 and 118.71 MiB respectively. These absolute Linux resident-set peaks include the Python/AiiDA baseline and child calculations, not the coding agents. The roughly 2 MiB difference on these tiny workloads does not establish a general memory-scaling result or justify a broad redesign.

L1/L2/L3 hardware counters are **unavailable** because this host's perf security policy rejects access (`kernel.perf_event_paranoid=4`). Their fields are null, not zero; no cache miss/hit behavior can be concluded from these runs. Static cache capacities are not substituted for measured usage. The profiler can attempt supported access/miss counters on a permitted host, with its wider full-process counter scope explicitly documented.

See [runtime-resources/README.md](runtime-resources/README.md) for measurement boundaries, raw per-run data, verification and reproduction. The original authoring time/token/cost measurements remain unchanged.
