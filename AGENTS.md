# AGENTS.md - AI Coding Assistant Guide for AiiDA Core

This file provides context for AI coding assistants (Claude Code, GitHub Copilot, etc.) working on the `aiida-core` codebase.

**IMPORTANT**: Always use the project's tooling. Use `uv run` to run Python, tests, and tools (e.g., `uv run pytest`, `uv run pre-commit`). Never use bare `python` or `pip`. Check `pyproject.toml` and `.pre-commit-config.yaml` for the full configuration.

## Project overview

AiiDA is a workflow manager for computational science with a strong focus on provenance, performance, and extensibility.
It is written in Python (3.9–3.13) and uses PostgreSQL/SQLite for metadata storage, [`disk-objectstore`](https://github.com/aiidateam/disk-objectstore) for file storage, and RabbitMQ as a message broker.

- **Repository:** https://github.com/aiidateam/aiida-core
- **Documentation:** https://aiida.readthedocs.io/projects/aiida-core/en/stable/
- **License:** MIT
- **Build system:** Flit (`flit_core.buildapi`)

## Key design concepts

- **Provenance:** all data and computations are tracked as nodes in a directed acyclic graph (DAG).
  Nodes are immutable once stored, with one exception: `ProcessNode` exposes a small whitelist of `_updatable_attributes` (process state, exit status, checkpoint, etc.) that the engine can still modify on a stored node until `seal()` is called at process termination.
- **Process/Node duality:** processes (`CalcJob`, `WorkChain`, `calcfunction`, `workfunction`) define *how* to run; process nodes record *that* something ran.
- **Plugin system:** entry points (`pyproject.toml` `[project.entry-points]`) allow extending AiiDA with new calculation types, data types, schedulers, transports, and storage backends.
- **Public API:** anything importable from a second-level package (e.g., `from aiida.orm import ...`, `from aiida.engine import ...`) is considered public API with deprecation guarantees.
  In practice, what constitutes "public API" is not strictly enforced and depends on the user type: workflow users interact mainly with the CLI and high-level ORM, workflow developers use the engine and process APIs, and plugin developers rely on ABCs and entry point interfaces.
  Deeper internal modules may change without deprecation notices.
- **Data compatibility:** data created with older AiiDA versions is guaranteed to work with newer versions.
  Database migrations are applied automatically when needed.

### Process / Node duality

Each process class has a corresponding node class that records its execution:

| Process class | Node class | Link types |
|--------------|------------|------------|
| `CalcJob` | `CalcJobNode` | INPUT_CALC → CREATE |
| `WorkChain` | `WorkChainNode` | INPUT_WORK → RETURN/CALL |
| `@calcfunction` | `CalcFunctionNode` | INPUT_CALC → CREATE |
| `@workfunction` | `WorkFunctionNode` | INPUT_WORK → RETURN/CALL |

## Code style

All code style is enforced via **pre-commit hooks** (configured in `.pre-commit-config.yaml`).
Run `uv run pre-commit` to check staged files, or `uv run pre-commit run --all-files` to check everything.

- Formatting/linting: `ruff` (single quotes, see `[tool.ruff.lint]` in `pyproject.toml` for enabled rule sets)
- Type checking: `mypy` (runs in pre-commit; add type hints to new code)
- Prefer `pathlib` over `os.path` &mdash; not currently enforced; legacy `os.path` usage exists throughout the codebase
- Docstrings: Sphinx-style (reST) (`:param:`, `:return:`, `:raises:`). Types belong in type hints, not docstrings.
- New source files should include the standard copyright header (copy from any existing source file).
- Other pre-commit hooks: `uv-lock` (lockfile consistency), `imports` (auto-generates `__all__`), `nbstripout`, `generate-conda-environment`, `verdi-autodocs`

**Special cases**:

- In `cmdline/`: delay `aiida` imports to function level (keeps `verdi` CLI responsive &mdash; top-level imports would slow down every invocation, even `verdi --help`).
  Enforced in CI via `verdi devel check-load-time`, which fails if unexpected `aiida.*` modules (outside `aiida.brokers`, `aiida.cmdline`, `aiida.common`, `aiida.manage`, `aiida.plugins`, `aiida.restapi`) are imported at startup.

### Error handling

Use `aiida.common.exceptions` for AiiDA-specific exceptions so callers can catch predictable, typed errors.
Use `aiida.common.warnings` for non-fatal issues so users can selectively filter them.
Assign exception messages to a local variable before raising:

```python
msg = f'WorkGraph process<{workgraph.process.pk}> already created. Use submit() instead.'
raise ValueError(msg)
```

### Best practices (not enforced)

- Prefer pure functions without side effects where possible.
- Prefer explicit keyword arguments over positional, especially for same-type parameters. Minimize `*args`/`**kwargs`.

### Git tooling

The `.git-blame-ignore-revs` file lists commits that should be ignored by `git blame` (e.g., bulk reformatting or whitespace-only changes).
When landing a large-scale formatting-only commit, add its SHA to this file so that future `git blame` output stays meaningful.

## Common patterns

> **Note:** New data types, calculations, parsers, and other plugins are typically developed in **external plugin packages** rather than in `aiida-core` itself.
> Use the [aiida-plugin-cutter](https://github.com/aiidateam/aiida-plugin-cutter) cookiecutter template to quickly scaffold a new plugin package with best practices, testing setup, and CI configuration.
> The patterns below apply to both external plugins and core contributions.
> In all cases, add tests and documentation alongside the new code.

### Adding a new Node type

1. Create a new class inheriting from appropriate base (e.g., `Data`, `ArrayData`)
1. Register as entry point in `pyproject.toml` under `[project.entry-points."aiida.data"]`

### Adding a new CalcJob plugin

1. Create class inheriting from `CalcJob`
1. Implement `define()` method with inputs/outputs spec
1. Implement `prepare_for_submission()` method
1. Register as entry point under `[project.entry-points."aiida.calculations"]`
1. Add corresponding parser if needed

### Adding a new WorkChain plugin

1. Create class inheriting from `WorkChain`
1. Implement `define()` method with inputs/outputs spec and the `outline`
1. Implement outline step methods (each step can submit calculations, inspect results, and return to context)
1. Register as entry point under `[project.entry-points."aiida.workflows"]`

## AI assistant guidelines

When working on this codebase:

- **Read before writing**: Always read existing code and understand patterns before proposing changes.
  Don't guess how AiiDA works.
- **Match existing style**: Follow patterns you see in surrounding code, even if you'd do it differently.
- **Don't modify code you weren't asked to change**: If fixing a bug in function A, don't also "improve" functions B and C nearby.
- **Don't add docstrings/type hints to unchanged code**: Only add to code you're actively modifying.

### AiiDA-specific gotchas

- **Post-storage mutability**: On stored nodes, only extras can be modified (and, for `ProcessNode`, the `_updatable_attributes` whitelist until `seal()`, see [Key design concepts](#key-design-concepts)).
- **CREATE vs RETURN links**: Calculations *create* new data nodes; workflows *return* existing data nodes.
  Workflows orchestrate but don't create data themselves.
- **Don't break provenance**: Never circumvent the link system or modify stored nodes in ways that would break the directed acyclic graph.
- **Daemon signal handling**: The daemon captures `SIGINT`/`SIGTERM` for graceful shutdown.
  When creating subprocesses in daemon code, pass `start_new_session=True` to prevent the subprocess from being killed when the daemon receives a signal.
- **Code review norms**: Technical facts overrule personal preferences. Prefix optional style suggestions with "Nit:". A PR should be approved if it improves code health overall, even if not perfect.

## Reference documentation

- AiiDA: [repo](https://github.com/aiidateam/aiida-core) &mdash; [docs](https://aiida.readthedocs.io/projects/aiida-core/)
- Plumpy: [repo](https://github.com/aiidateam/plumpy) &mdash; [docs](https://plumpy.readthedocs.io/)
- Kiwipy: [repo](https://github.com/aiidateam/kiwipy) &mdash; [docs](https://kiwipy.readthedocs.io/)
- disk-objectstore: [repo](https://github.com/aiidateam/disk-objectstore) &mdash; [docs](https://disk-objectstore.readthedocs.io/)
- AiiDA Plugin Registry: [repo](https://github.com/aiidateam/aiida-registry) &mdash; [site](https://aiidateam.github.io/aiida-registry/)
