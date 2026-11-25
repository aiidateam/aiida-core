# Graph restart study

Consolidated report for the restart benchmark timings plus the isolated
restart-authoring agent evaluation. **Authoritative data: `report.json`**
(assembled mechanically by `assemble_report.py` from the input JSON artifacts;
no hand-transcribed measurements). Baseline: revision `4ae87025e`
(`graph-benchmark-v6`), model `gpt-6.1-sol` (thinking `medium`), **n=1 per
method** — one anecdotal paired run, not a general claim.

## Benchmark restarts (budget 5, recover = 3 FlakyStep runs, attempts 0,1,2, value 1.5)

| Mode | Phase | Rounds | Mean (s) | Median (s) | Processes/run |
|---|---|---|---|---|---|
| `restart-workchain` (`run_get_node`, local) | local | 10+1 warmup | 0.886 | 0.859 | 3 workchains, 0 calcfunctions |
| `restart-graph` (authoring handle, local) | local | 10+1 | 2.455 | 2.421 | 3 workchains, 7 helper calcfunctions |
| `restart-graph-direct-ir` (stored IR, local) | local | 10+1 | 2.444 | 2.440 | 3 workchains, 7 helper calcfunctions |
| `restart-ir` (warm build + to_dict/from_dict) | IR serialization | 10+1 | 0.0037 | 0.0036 | n/a (no execution) |
| `restart-workchain-daemon` (submitted) | submitted | 5+1 | 1.141 | 1.138 | 3 workchains, 0 calcfunctions |
| `restart-graph-daemon` (authoring, inputs/round in timing) | submitted | 5+1 | 2.793 | 2.864 | 3 workchains, 7 helper calcfunctions |
| `restart-graph-direct-ir-daemon` (fresh Dict/round from template) | submitted | 5+1 | 3.034 | 2.981 | 3 workchains, 7 helper calcfunctions |

Full suite: **32 timed cases** (10 engine-matched + 15 inline + 7 restart),
57 correctness tests skipped via `--benchmark-only`, 0 failed, 766.06 s
(0:12:46). Per-case `finished_ok` and descendant counts are embedded in each
case record in `report.json` (and `benchmarks/report.json`).

Provenance (corrected): the shared `FlakyStep` forwards its stored `result`
input `Float` unchanged (step uuid == shared uuid; no new `Data`, no workflow
CREATE links); the work-chain root returns that same node. The graph root
`result` is the output of the `ensure_recovered` calcfunction — a **new**
`Float` (uuid differs) with identical value 1.5. Comparison is
workload-matched, **not** operation-identical: 7 extra graph helper
calcfunctions, different failure vocabulary (WC 401/402 vs graph 400 via
raising `ensure`; failure paths not timed).

## Agent eval (isolated restart authoring, `graph-restart-eval-v1`)

Both arms solved with the same model/thinking/tools/timeout; no follow-up
hints, solution fixes, or model reruns. The grader correction is documented below.

| Arm | Method | In (uncached) | CacheRead | Out | Total | Wall (s) | Responses | Tools (start/ok/err) | Authoritative grade |
|---|---|---|---|---|---|---|---|---|---|
| a | `BaseRestartWorkChain` | 19609 | 100096 | 1626 | 121331 | 71.8 | 8 | 12/11/1 | **4/4** (v2) |
| b | `GraphIR`-direct | 37102 | 510080 | 3427 | 550609 | 156.0 | 20 | 36/32/4 | **4/4** (v2) |

Usage is streamed assistant usage recomputed from the authoritative
`message_end` records (`assemble_report.py` checks it against
`metrics-arm-*.json` and run cards). Cache dominates both totals; uncached
input + output totals are 21235 and 40529 tokens respectively. These are token
counts, not monetary costs; billing depends on the provider's cache pricing.

**Corrected grader provenance:** the initial v1 scoring (a 0/4, b 1/4) was a
frozen-grader fixture-loading defect — the v1 grader imported eval-root
`flaky_child` while both solutions legally use scratch `fixtures.flaky_child`,
so module-identity/`QueryBuilder` discovery found 0 children despite correct
retry dispatch visible in the v1 logs. Acceptance semantics unchanged; the v2
grader (`evaluation/grader-v2/`, canonical scratch fixture) re-ran the
**unchanged** solutions once per arm: both **4/4**. V1 results are retained as
`arms.{a,b}.initial_v1_hidden_tests` plus untouched `verification-{a,b}.json` /
`verify-{a,b}.log` / `grader-v1/`; `arms.{a,b}.hidden_tests` is normalized to
the authoritative v2 4/4. Tokens/time untouched (no new model calls). Parent
independently verified both solutions again: 4/4 passed each
(`verify-parent-{a,b}.log`).

## Logs and artifacts (relative to repo root)

The full evaluation directory is stored in `evaluation-logs.tar.xz`, including
both raw event streams, complete session logs, prompts, original solutions,
fixture copies, and both grader versions. The unpacked directory remains
available locally. To extract it after checkout:

```sh
tar -xJf reports/graph-restart-study/evaluation-logs.tar.xz -C reports/graph-restart-study
uv run python reports/graph-restart-study/assemble_report.py
```

The grader can also verify the archived solution packages under
`evaluation/solutions/{a,b}/restart_solution` without the original temporary
worktrees; both copies passed all four tests.

- `reports/graph-restart-study/report.json` — this consolidated report
- `reports/graph-restart-study/assemble_report.py` — reproducible assembler/validator
- `reports/graph-restart-study/benchmarks/report.json` — authoritative benchmark report
- `reports/graph-restart-study/benchmarks/raw-pytest-benchmark.json` — raw timings
- `reports/graph-restart-study/benchmarks/run.log` — full benchmark pytest log
- `reports/graph-restart-study/benchmarks/derive_report.py` — benchmark derivation
- `reports/graph-restart-study/benchmarks/env-snapshot.txt` — pre-run environment
- `reports/graph-restart-study/evaluation/report.json` — eval report (normalized)
- `reports/graph-restart-study/evaluation/events-arm-{a,b}.jsonl` — raw agent streams
- `reports/graph-restart-study/evaluation/metrics-arm-{a,b}.json` — parsed usage
- `reports/graph-restart-study/evaluation/run-card-arm-{a,b}.json` — harness cards
- `reports/graph-restart-study/evaluation/sessions-arm-{a,b}/` — raw session files
- `reports/graph-restart-study/evaluation/solutions/{a,b}/` — frozen agent solutions
- `reports/graph-restart-study/evaluation/verification-v2-{a,b}.json`, `verify-v2-{a,b}.log` — authoritative grading
- `reports/graph-restart-study/evaluation/verification-{a,b}.json`, `verify-{a,b}.log`, `grader-v1/` — preserved initial scoring
- `reports/graph-restart-study/evaluation/verify-parent-{a,b}.log` — final independent parent verification
- `reports/graph-restart-study/validation.log` — full copy of the parent correctness run
  (original: `/tmp/graph-exit-committed-verification.log`; 794 passed, 32 timing skips)

## Caveats

n=1 per method; single machine, single warm-cache run — comparative within
this run only. Daemon submitted timing measures end-to-end submission latency
(broker + 0.1 s polling), not engine speed alone. Idle orphan processes from
other environments existed on the shared host (load average 0.85 on 28 cores
at start). Token-cap enforcement is sampled at `message_end` boundaries (can
overshoot by one response). See `uncertainty_and_protocol_limitations` in
`report.json` for the full list.
