# AGENTS.md - AI Coding Assistant Guide for AiiDA Core

This file provides context for AI coding assistants (Claude Code, GitHub Copilot, etc.) working on the `aiida-core` codebase.

**IMPORTANT**: Always use the project's tooling. Use `uv run` to run Python, tests, and tools (e.g., `uv run pytest`, `uv run pre-commit`). Never use bare `python` or `pip`. Check `pyproject.toml` and `.pre-commit-config.yaml` for the full configuration.

## Project overview

AiiDA is a workflow manager for computational science with a strong focus on provenance, performance, and extensibility.
It is written in Python (3.9–3.13) and uses PostgreSQL/SQLite for metadata storage, [`disk-objectstore`](https://github.com/aiidateam/disk-objectstore) for file storage, and RabbitMQ as a message broker.

## Key design concepts

- **Provenance:** all data and computations are tracked as nodes in a directed acyclic graph (DAG). Nodes are immutable once stored, except extras (always mutable) and `ProcessNode._updatable_attributes` (process state, exit status, checkpoint, etc., mutable until `seal()`).
- **Process/Node duality:** processes (`CalcJob`, `WorkChain`, `calcfunction`, `workfunction`) define *how* to run; process nodes record *that* something ran.
- **CREATE vs RETURN links:** calculations *create* new data nodes; workflows *return* existing data nodes. Workflows orchestrate but don't create data themselves.
- **Don't break provenance:** never circumvent the link system or modify stored nodes in ways that would break the DAG.
- **Public API:** anything importable from a second-level package (e.g., `from aiida.orm import ...`) is public API with deprecation guarantees. Deeper internal modules may change without notice.
- **Plugin system:** entry points (`pyproject.toml` `[project.entry-points]`) allow extending AiiDA with new calculation types, data types, schedulers, transports, and storage backends.
- **Daemon signal handling:** the daemon captures `SIGINT`/`SIGTERM` for graceful shutdown. Subprocesses in daemon code must pass `start_new_session=True`.

### Process / Node duality

Each process class has a corresponding node class that records its execution:

| Process class | Node class | Link types |
|--------------|------------|------------|
| `@calcfunction` | `CalcFunctionNode` | INPUT_CALC → CREATE |
| `CalcJob` | `CalcJobNode` | INPUT_CALC → CREATE |
| `@workfunction` | `WorkFunctionNode` | INPUT_WORK → RETURN/CALL |
| `WorkChain` | `WorkChainNode` | INPUT_WORK → RETURN/CALL |

## Code style

Code style is enforced via **pre-commit hooks** (`.pre-commit-config.yaml`). Always run `uv run pre-commit` before pushing.
Formatting: `ruff`. Type checking: `mypy`. Write new code following ruff conventions with proper type hints.
Docstrings: Sphinx-style (`:param:`, `:return:`, `:raises:`), types in annotations not docstrings. Prefer `pathlib` over `os.path`.
New source files should include the standard copyright header (copy from any existing `.py` file).
In `cmdline/`: delay `aiida` imports to function level (keeps `verdi` CLI responsive, see the `adding-a-cli-command` skill).
See the `linting-and-ci` skill for details.

### Error handling

Use `aiida.common.exceptions` for AiiDA-specific exceptions, `aiida.common.warnings` for non-fatal issues.
Assign exception messages to a variable before raising: `msg = f'...'; raise TypeError(msg)`

### Best practices (not enforced)

- Prefer pure functions without side effects where possible
- Prefer explicit keyword arguments over positional, especially for same-type parameters. Minimize `*args`/`**kwargs`.
- Prefer `dataclass` or `TypedDict` over plain dicts for structured data
- Use `Enum` or `Literal` over bare strings to constrain inputs
- Avoid mutable default arguments — use `None` and assign inside the body
- Use context managers for resource cleanup (files, connections, transactions)
- Favor composition over inheritance. Use `Protocol` for structural subtyping where possible.
- Follow SOLID principles, Postel's law (accept broad inputs, return narrow types), the principle of least surprise, and separation of concerns

## Claude Code skills

The following skills (under `.claude/skills/`) provide task-specific guidance:

- `adding-a-cli-command`: `verdi` subcommands and import-time constraints
- `adding-dependencies`: third-party dependency checklist
- `architecture-overview`: codebase structure, key files, ABCs
- `commit-conventions`: branching, commit style, PR requirements
- `debugging-processes`: diagnosing failed or stuck processes and the daemon
- `deprecating-api`: deprecation warnings and removal timeline
- `linting-and-ci`: pre-commit, CI checks
- `running-tests`: pytest cheatsheet, plugins, fixtures
- `writing-and-building-docs`: documentation style and building
- `writing-tests`: test philosophy, markers, parametrization

## AI assistant guidelines

When working on this codebase:

- **Read before writing**: Always read existing code and understand patterns before proposing changes.
  Don't guess how AiiDA works.
- **Match existing style**: Follow patterns you see in surrounding code.
- **Don't modify code you weren't asked to change**: If fixing a bug in function A, don't also "improve" functions B and C nearby.
- **Don't add docstrings/type hints to unchanged code**: Only add to code you're actively modifying.

## Key dependencies

Key dependencies (all under [github.com/aiidateam](https://github.com/aiidateam)): `plumpy` (process state machine), `kiwipy` (message broker interface), `disk-objectstore` (file storage).
