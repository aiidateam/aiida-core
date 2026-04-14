---
name: running-tests
description: Use when running pytest, checking test results, or understanding test infrastructure in aiida-core.
---

# Running tests in aiida-core

Always invoke via `uv run` so tests pick up the locked project environment.
Never use bare `python` or `pytest`.

## Installing the dev environment

```bash
uv sync                                           # install from uv.lock
```

## Running tests

```bash
uv run pytest                                     # full suite (requires PostgreSQL + RabbitMQ)
uv run pytest -m presto                           # quick subset (SqliteTempBackend, no services)
uv run pytest tests/orm/test_nodes.py             # specific module
uv run pytest tests/orm/test_nodes.py::TestNode   # specific class
uv run pytest tests/orm/test_nodes.py::TestNode::test_store  # specific method
uv run pytest -n auto                             # parallel
uv run pytest -x --ff                             # stop on first failure, failed first on rerun
uv run pytest --no-instafail                       # disable instant failure output (enabled by default via addopts)
uv run pytest --cov aiida                         # run with coverage
```

## Pytest plugins and default options

The project uses several pytest plugins (configured in `pyproject.toml` under `[tool.pytest.ini_options]`):
`pytest-instafail` (show failures instantly, enabled by default), `pytest-xdist` (parallel via `-n`), `pytest-cov`, `pytest-timeout`, `pytest-rerunfailures`, `pytest-benchmark` (skipped by default), `pytest-regressions`.

Default `addopts`: `--instafail --tb=short --strict-config --strict-markers -ra --benchmark-skip --durations=5`.

## Notes

- `presto`-marked tests use an in-memory `SqliteTempBackend`. If they fail, the bug is in the code, not in service configuration.
- Tests have a default timeout of 240 seconds (`pytest-timeout`). Override per-test with `@pytest.mark.timeout(seconds)` if needed.
- Transport tests require passwordless SSH to localhost.
- Reusable fixtures live in `tests/conftest.py` and per-subtree `conftest.py` files, check there before writing ad-hoc setup.
- See the `writing-tests` skill for test philosophy, marker conventions, and parametrization patterns.

## verdi test helpers

```bash
verdi devel launch-add            # launch test ArithmeticAddCalculation
verdi devel launch-multiply-add   # launch test MultiplyAddWorkChain
```
