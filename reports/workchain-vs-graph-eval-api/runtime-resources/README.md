# Workflow execution memory and CPU caches

New instrumented executions of the finished submissions, not retrospective agent measurements. Each case runs in a fresh Python process and temporary SQLite profile, pinned to the same logical CPU. The original coding-agent time/token/cost metrics are unchanged.

| Arm | Executions | Maximum workflow-window RSS | Median per-run peak RSS | L1 data | L2 | L3/LLC |
|---|---:|---:|---:|---|---|---|
| workchain | 39 | 118.17 MiB | 116.79 MiB | Unavailable | Unavailable | Unavailable |
| graph | 39 | 120.39 MiB | 118.71 MiB | Unavailable | Unavailable | Unavailable |

## Unpack individual measurements

Individual execution JSON/logs, the original `runs.jsonl`, smoke checks and perf diagnostics are preserved in
`execution-logs.tar.xz`. The summary, environment and audit stay directly readable.

```bash
(cd reports/workchain-vs-graph-eval-api/runtime-resources && \
  sha256sum -c execution-logs.tar.xz.sha256 && tar -xJf execution-logs.tar.xz)
```

## Measurement boundaries

- RSS is the Linux resident-set high-water mark (`/proc/self/status: VmHWM`), not heap or summed ORM node sizes.
- The worker resets its own peak before `run_get_node` via `/proc/self/clear_refs` value 5.
  It reads the peak immediately on return, before checking results. This includes the Python/AiiDA resident baseline,
  graph compilation/serialization at first launch and scientific child WorkChains/calcfunctions in the same interpreter;
  it excludes earlier profile/import initialization and later validation/cleanup peaks. No task runs before this window.
- Preparation/final RSS, CPU times, process peak through completion and reset support are also recorded.
  If the reset is unavailable, workflow-window peaks are null rather than mislabeled lifetime measurements.
- Absolute RSS includes shared mapped pages; this is not proportional set size or incremental allocated memory.
- Maxima and medians summarize matched cases, but three repetitions are not a statistically powered comparison.
- All runs verify results, budgets, child counts, finished states, output identity and no root CREATE links.

## Cache availability

Hardware cache counters are unavailable. The perf probe failed; this host reports `kernel.perf_event_paranoid=4`. See `perf-permission.log` and `environment.json` for the exact diagnostic. No host security setting or privilege was changed.

Unavailable counter values are null, never zero. CPU cache capacities in `environment.json` are hardware metadata,
not workflow cache usage. Cache occupancy is not inferred from RSS, filesystem page cache or model-token caches.

The intended metrics are accesses, misses and miss rates for L1 **data**, L2 and L3/LLC.
L1 instruction cache capacity is recorded, but instruction-cache usage was not measured either.
On a permitted machine the runner checks event support and collects the supported events with perf;
those counters cover the whole profiling process (imports/setup/execution/verification/teardown),
not the narrower RSS workflow window. Raw counts and counter running percentages are retained per execution.
Do not compare those counters with a narrower execution-only scope without adapting the instrumentation.
The L2 aliases are specific to the detected Intel CPU and may require adaptation on other architectures.

## Reproduce

First unpack the parent report's evaluation archive as described in [its README](../README.md).
The frozen source workspaces recorded in `run.json` must still exist or be faithfully restored;
source-hash checks reject different code rather than silently profiling a new implementation.

```bash
uv run --no-sync python reports/workchain-vs-graph-eval-api/measure_resources.py \
  --repetitions 3 --output-dir /tmp/aiida-workflow-resources-new
```

The runner uses the frozen source workspaces recorded in the eval report and verifies their source hashes first.
A new output directory avoids overwriting results; use `--case-index 0 --repetitions 1` for a smoke run.
If perf access is granted by the machine administrator, the same command attempts cache counters automatically.
No agent/model calls occur. Per-run JSON, logs, source checks and environment details remain alongside this summary.
