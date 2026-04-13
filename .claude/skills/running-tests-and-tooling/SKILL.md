---
name: running-tests-and-tooling
description: Use when running tests, pre-commit, docs builds, or any aiida-core development commands. Contains the full cheatsheet of `uv run` / `verdi` / `sphinx` invocations and explains the `presto` marker, parallel execution, and the import-time check.
---

# Running tests and tooling in aiida-core

Always invoke Python tools via `uv run` so they pick up the locked project environment instead of the system Python.
Never use bare `python`, `pip`, or `pytest`.

## Installing the dev environment

```bash
uv sync                                           # install from uv.lock
```

## Tests

```bash
uv run pytest                                     # full suite (requires PostgreSQL + RabbitMQ)
uv run pytest -m presto                           # quick subset (SqliteTempBackend, no services)
uv run pytest tests/orm/test_nodes.py             # specific module
uv run pytest tests/orm/test_nodes.py::TestNode   # specific class
uv run pytest -n auto                             # parallel
uv run pytest -x --ff                             # stop on first failure, failed first on rerun
```

Notes:

- `presto`-marked tests use an in-memory `SqliteTempBackend`. If they fail, the bug is in the code, not in service configuration.
- Transport tests require passwordless SSH to localhost.
- Reusable fixtures live in `tests/conftest.py` and per-subtree `conftest.py` files &mdash; check there before writing ad-hoc setup.

## Pre-commit

```bash
uv run pre-commit                                 # check staged files
uv run pre-commit run --all-files                 # check everything
uv run pre-commit run mypy                        # run a specific hook
uv run pre-commit run ruff --all-files            # run ruff on all files
```

Other hooks worth knowing about: `uv-lock` (lockfile consistency), `imports` (auto-generates `__all__`), `nbstripout`, `generate-conda-environment`, `verdi-autodocs`.

## Documentation

```bash
uv run sphinx-build -b html docs/source docs/build/html
```

Write one sentence per line in `.md` and `.rst` files under `docs/`.

## verdi helpers for development

```bash
verdi shell                       # IPython shell with AiiDA loaded
verdi status                      # service status (daemon, PostgreSQL, RabbitMQ)
verdi daemon start/stop/restart   # manage the daemon
verdi devel launch-add            # test ArithmeticAddCalculation
verdi devel launch-multiply-add   # test MultiplyAddWorkChain
verdi devel check-load-time       # fails if unexpected aiida.* modules import at verdi startup
```

Set `AIIDA_WARN_v3=1` to surface deprecation warnings.

## CI-enforced import-time check

`verdi devel check-load-time` fails in CI if any module outside `aiida.brokers`, `aiida.cmdline`, `aiida.common`, `aiida.manage`, `aiida.plugins`, or `aiida.restapi` is imported at `verdi` startup.
When touching `src/aiida/cmdline/`, defer `aiida` imports to inside the command function body, not at module top level.
See the `adding-a-cli-command` skill for details.
