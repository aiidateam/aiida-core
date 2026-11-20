# Graph benchmarks and authoring evaluations

These opt-in studies are separate from the regular regression suite:

- `graph_engine/`: matched WorkChain/graph correctness checks, shared
  workloads, and runtime timing harnesses.
- `graph_restart_eval/`: isolated agent-authoring evaluation, including task
  prompts, fixtures, grading, and the evaluation runner. See its own README.

Correctness checks and their shared workloads live in
`graph_engine/test_matched*.py` and `graph_engine/programs/matched*.py`.
They run only when explicitly selected, like the timing harnesses:

```bash
uv run python -m pytest -p tests.conftest -m presto utils/benchmarks/graph_engine/test_matched.py
```

Existing upstream benchmarks in `tests/benchmark/` are unchanged.

Recorded results and immutable execution logs remain under `reports/`.
Historical reports refer to the paths used when they were measured; timing
harnesses formerly in `tests/benchmark/` now live in
`utils/benchmarks/graph_engine/`.
