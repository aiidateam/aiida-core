---
name: running-tests
description: Use when running pytest, checking test results, or understanding test infrastructure in aiida-core. Contains the full `uv run pytest` cheatsheet, `presto` marker semantics, parallel execution, coverage, and fixture locations.
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
uv run pytest -n auto                             # parallel
uv run pytest -x --ff                             # stop on first failure, failed first on rerun
uv run pytest --cov aiida                         # run with coverage
```

## Notes

- `presto`-marked tests use an in-memory `SqliteTempBackend`. If they fail, the bug is in the code, not in service configuration.
- Transport tests require passwordless SSH to localhost.
- Reusable fixtures live in `tests/conftest.py` and per-subtree `conftest.py` files, check there before writing ad-hoc setup.
- See the `writing-tests` skill for test philosophy, marker conventions, and parametrization patterns.

## verdi test helpers

```bash
verdi devel launch-add            # launch test ArithmeticAddCalculation
verdi devel launch-multiply-add   # launch test MultiplyAddWorkChain
```
