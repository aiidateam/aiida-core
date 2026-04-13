---
name: linting-and-ci
description: Use when running pre-commit, linting, type checking, building docs, or fixing CI failures in aiida-core. Contains the full `uv run pre-commit` cheatsheet, hook list, import-time check, and `verdi` development helpers.
---

# Linting, pre-commit, and CI in aiida-core

Always invoke via `uv run` so tools pick up the locked project environment.
Never use bare `python` or `pip`.

## Pre-commit

```bash
uv run pre-commit                                    # check staged files
uv run pre-commit run --all-files                    # check everything
uv run pre-commit run mypy                           # run a specific hook
uv run pre-commit run ruff --all-files               # run ruff on all files
uv run pre-commit run --from-ref main --to-ref HEAD  # check only changes since branching off main
```

Hooks worth knowing about: `uv-lock` (lockfile consistency), `imports` (auto-generates `__all__`), `nbstripout`, `generate-conda-environment`, `verdi-autodocs`.

## Building documentation

```bash
uv run sphinx-build -b html docs/source docs/build/html
```

See the `writing-docs` skill for style conventions.

## CI-enforced import-time check

`verdi devel check-load-time` fails in CI if any module outside `aiida.brokers`, `aiida.cmdline`, `aiida.common`, `aiida.manage`, `aiida.plugins`, or `aiida.restapi` is imported at `verdi` startup.
When touching `src/aiida/cmdline/`, defer `aiida` imports to inside the command function body, not at module top level.
See the `adding-a-cli-command` skill for details.

## Other verdi development helpers

```bash
verdi shell                       # IPython shell with AiiDA loaded
verdi status                      # service status (daemon, PostgreSQL, RabbitMQ)
verdi daemon start/stop/restart   # manage the daemon
verdi devel check-load-time       # check for import-time violations
```

Set `AIIDA_WARN_v3=1` to surface deprecation warnings.
