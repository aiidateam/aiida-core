# Graph restart study: benchmark timing (GO run)

Brief human summary. **Authoritative data: `report.json`** (derived mechanically from
`raw-pytest-benchmark.json` by `derive_report.py`; all stats in seconds).

## Run

- Commit `4ae87025e` (`graph-benchmark-v6`), tracked tree clean (only untracked `reports/` output).
- Command: `uv run pytest -m presto tests/benchmark/test_graph_engine.py tests/benchmark/test_graph_engine_inline.py tests/benchmark/test_graph_restart.py --benchmark-only --benchmark-json=reports/graph-restart-study/benchmarks/raw-pytest-benchmark.json`
- Serial, no xdist, exclusive machine. Result: **32 passed, 57 skipped, 0 failed** in 766.06 s (0:12:46).
  The 57 skips are the non-benchmark correctness tests auto-skipped by `--benchmark-only`.
- Correctness evidence is the **parent run** `/tmp/graph-exit-committed-verification.log`
  (794 passed, 32 skipped timing skips — not claimed as this run): this run is its complement.
- Backend: `core.sqlite_dos` temp profiles, ZeroMQ broker, CPython 3.12.4, AiiDA 3.0.0.dev0.
- Host: Intel i9-10940X (28 threads), 251 GB RAM, Linux 6.8.0-101-generic. No host identifiers
  or credentials are serialized in `report.json`.

## Restart modes (budget 5, recover = 3 FlakyStep runs, attempts 0,1,2, value 1.5)

| Mode | Phase | Rounds | Mean (s) | Median (s) | Processes/run |
|---|---|---|---|---|---|
| `restart-workchain` (local `run_get_node`) | local | 10+1 warmup | 0.886 | 0.859 | 3 workchains, 0 calcfunctions |
| `restart-graph` (authoring handle) | local | 10+1 | 2.455 | 2.421 | 3 workchains, 7 helper calcfunctions |
| `restart-graph-direct-ir` (stored IR launch) | local | 10+1 | 2.444 | 2.440 | 3 workchains, 7 helper calcfunctions |
| `restart-ir` (warm build + to_dict/from_dict) | IRserialization | 10+1 | 0.0037 | 0.0036 | n/a (no execution) |
| `restart-workchain-daemon` (submitted) | submitted | 5+1 | 1.141 | 1.138 | 3 workchains, 0 calcfunctions |
| `restart-graph-daemon` (authoring, inputs resolved per round in timing) | submitted | 5+1 | 2.793 | 2.864 | 3 workchains, 7 helper calcfunctions |
| `restart-graph-direct-ir-daemon` (fresh Dict per round from template) | submitted | 5+1 | 3.034 | 2.981 | 3 workchains, 7 helper calcfunctions |

Notes: graph pays 7 helper-task calcfunctions (`zero` + 3×`should_restart` + 2×`advance` +
`ensure_recovered`) with no work-chain counterpart — the comparison is workload-matched, not
operation-identical (graph declaration/loop plumbing differs; failure vocabulary differs). Local
authoring vs direct-IR are
identical within noise (same warm execution); daemon direct-IR is slowest per round because it
builds a fresh declaration `Dict` per round, while the authoring daemon mode re-parses launch
inputs per round. Daemon rounds include broker scheduling plus 0.1 s-granularity completion
polling (`submit_and_await`). Failure vocabulary differs (work chain 401/402 vs graph 400 via
raising `ensure`) — failure paths were not timed. IR cost is a warmed cache hit plus dict
round trip, not cold compilation. Provenance: the shared `FlakyStep` forwards its stored `result`
input `Float` unchanged (step `outputs.value` uuid == shared uuid; no new `Data`, no workflow CREATE
links) and the work-chain root returns that same node; the graph root `result` is the output of
the `ensure_recovered` calcfunction (a NEW `Float`, uuid differs) with identical value 1.5 —
step-level computation provenance preserved, root node identity differs.

## Inline summary (5 workloads × workchain / graph / inline, 10 rounds + 1 warmup)

Inline control (expressions instead of `decrement`/`is_positive` tasks) removes all control
tasks: `basic-loop` 0.082 s inline vs 0.178 s workchain vs 1.768 s graph (9 tasks);
`serial-wc-loop` 0.111 s inline vs 0.780 s workchain vs 8.443 s graph (21 tasks);
`threaded-wc-loop` 0.325 s inline (1 collector) vs 0.734 s workchain vs 2.520 s graph (13 tasks).
Calcjob loops are placement-dominated and converge: serial ≈ 2.74/4.48/2.79 s,
threaded ≈ 2.53/2.46/2.38 s (workchain/graph/inline). Historical matched suite (10 cases)
reproduces the same shape (graph basic-loop 1.712 s, serial-wc 8.387 s). Per-case
`finished_ok` and descendant counts are in each case's `extra_info.provenance`.

## Counts

32 timed cases (10 engine-matched + 15 inline + 7 restart: 3 local + 3 submitted + 1 IR),
57 correctness tests skipped via `--benchmark-only`, 0 deselected, 0 failed.
No timing was silently skipped: every expected case has 10 (local/IR) or 5 (daemon) measured rounds.

## Artifacts (relative to repo root)

- `reports/graph-restart-study/benchmarks/report.json` — authoritative
- `reports/graph-restart-study/benchmarks/raw-pytest-benchmark.json` — raw pytest-benchmark output
- `reports/graph-restart-study/benchmarks/run.log` — full pytest log
- `reports/graph-restart-study/benchmarks/derive_report.py` — derivation script
- `reports/graph-restart-study/benchmarks/env-snapshot.txt` — pre-run environment
- `/tmp/graph-exit-committed-verification.log` — parent correctness run (external to repo)

## Caveats

Workload-matched, not operation-identical (graphs declare outputs; loop state rewinds through
tasks; one `GraphProcess`, no child graphs; `par_map` collector; statically unrolled
threaded-calcjob-loop; per-placement `metadata.options`). Single machine, single warm-cache run:
comparative within this run only. Month-old idle orphan processes from other environments
existed on the shared host (no active test runs); load average at start 0.85 on 28 cores.
Daemon submitted timing measures end-to-end submission latency, not engine speed alone.
