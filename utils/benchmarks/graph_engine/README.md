# Matched graph runtime benchmarks

This directory contains only opt-in correctness checks and timing harnesses,
separate from the regular regression suite under `tests/`.

| Timing harness | Correctness tests |
| --- | --- |
| `test_graph_engine.py` | `test_matched.py` |
| `test_graph_engine_inline.py` | `test_matched_inline.py` |
| `test_graph_restart.py` | `test_matched_restart.py` |

Both suites reuse the workloads in `programs/matched*.py`.
The engine comparisons also reuse the existing upstream WorkChain baseline in
`tests/benchmark/test_engine.py`, which is unchanged.

## Running

Validate workloads from the repository root:

```bash
uv run python -m pytest -p tests.conftest -m presto utils/benchmarks/graph_engine/test_matched.py \
  utils/benchmarks/graph_engine/test_matched_inline.py \
  utils/benchmarks/graph_engine/test_matched_restart.py
```

Use `python -m pytest` so repository modules are importable, and explicitly load
`tests.conftest` to reuse backend options, temporary profiles, daemon fixtures,
and cleanup rather than duplicating them here.

Measure runtimes, serially and without concurrent test or evaluation runs:

```bash
uv run python -m pytest -p tests.conftest -m presto utils/benchmarks/graph_engine \
  --benchmark-only --benchmark-json=/tmp/graph-engine-benchmarks.json
```

Pass an individual module path to select one study.
For local-only timing, add `-k 'not daemon'`.
`-m presto` selects SQLite and ZeroMQ without external PostgreSQL or RabbitMQ.

These timing modules are outside the configured default `testpaths`; they run
only when explicitly selected, and are skipped unless `--benchmark-only` is
passed. Their module docstrings describe workload differences and measurement
boundaries. Historical reports and raw logs under `reports/graph-restart-study/`
retain their original paths and measurements.
