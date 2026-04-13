---
name: linting-and-ci
description: Use when running pre-commit, linting, type checking, building docs, or fixing CI failures in aiida-core.
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
uv run pre-commit run --from-ref $(git merge-base main HEAD) --to-ref HEAD  # same, but robust when main has advanced
```

Hooks worth knowing about: `uv-lock` (lockfile consistency), `imports` (auto-generates `__all__`), `nbstripout`, `generate-conda-environment`, `verdi-autodocs`.

CI enforces import-time constraints on `src/aiida/cmdline/`; see the `adding-a-cli-command` skill for details.

## Building documentation

```bash
uv run sphinx-build -b html docs/source docs/build/html
```

See the `writing-docs` skill for style conventions.

## Other verdi development helpers

```bash
verdi shell                       # IPython shell with AiiDA loaded
verdi status                      # service status (daemon, storage, broker if configured)
verdi daemon start/stop/restart   # manage the daemon
verdi devel check-load-time       # check for import-time violations
```

Set `AIIDA_WARN_v3=1` to surface deprecation warnings.
