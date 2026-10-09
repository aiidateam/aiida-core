---
name: linting-and-ci
description: Use for pre-commit, linting, type checking, and CI failures.
---

# Linting and CI

Use `uv run` for the locked project environment.

```bash
uv run pre-commit                          # staged files
uv run pre-commit run --all-files           # full repository
uv run pre-commit run --files <paths>       # selected files
uv run pre-commit run mypy                  # one hook
uv run pre-commit run ruff-check --all-files
uv run pre-commit run --from-ref "$(git merge-base main HEAD)" --to-ref HEAD
```

* `uv-lock`: lockfile consistency.
* `nbstripout`: notebook output cleanup.
* `generate-conda-environment`: regenerate `environment.yml`.
* `verdi-autodocs`: CLI documentation.
* CLI startup imports: `verdi devel check-load-time`; see `adding-a-cli-command`.
* Inspection: `debugging-processes`; lifecycle: `verdi daemon start`, `verdi daemon stop`, `verdi daemon restart`.
* `AIIDA_WARN_v3=1`: pending v3 deprecation warnings.
