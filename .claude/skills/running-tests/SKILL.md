---
name: running-tests
description: Use for pytest runs, results, fixtures, and test infrastructure.
---

# Running tests

Install the locked environment with `uv sync`; run tests with `uv run pytest`.
Use half the CPU cores unless serial execution is needed:

```bash
workers=$(( $(nproc) / 2 ))
uv run pytest -n "$workers"           # full suite; SQLite + RabbitMQ
uv run pytest -n "$workers" -m presto # SQLite + ZeroMQ; no external services
uv run pytest -n "$workers" tests/orm/nodes/test_node.py
uv run pytest -n "$workers" tests/orm/nodes/test_node.py::TestNode
uv run pytest -n "$workers" tests/orm/nodes/test_node.py::TestNode::test_repository_metadata
```

* `-x --ff`: stop at first failure; failed tests first.
* `--no-instafail`: disable immediate failure output.
* `--cov aiida`: coverage.
* Defaults: `pyproject.toml`, `[tool.pytest.ini_options]`.
* Plugins: `pytest-instafail`, `pytest-xdist`, `pytest-cov`, `pytest-timeout`, `pytest-rerunfailures`, `pytest-benchmark` (skipped by default), `pytest-regressions`.
* Default timeout: 240 seconds; override with `@pytest.mark.timeout(seconds)`.
* Design, fixtures, markers, SSH requirements: `writing-tests`.
* Failure diagnosis: `debugging-processes`.

## Workflow helpers

```bash
verdi devel launch-add           # ArithmeticAddCalculation
verdi devel launch-multiply-add  # MultiplyAddWorkChain
```
