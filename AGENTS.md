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

## Architecture

### Source layout

The source code lives under `src/aiida/` with these main packages:

| Package | Purpose |
|---------|---------|
| `brokers/` | Message broker interface (RabbitMQ via [`kiwipy`](https://github.com/aiidateam/kiwipy)) |
| `calculations/` | Built-in calculations |
| `cmdline/` | CLI (`verdi` command) built with `click` |
| `common/` | Shared utilities, exceptions, warnings, constants |
| `engine/` | Workflow engine: process runner, daemon, persistence, transport tasks (with [`plumpy`](https://github.com/aiidateam/plumpy) dependency) |
| `manage/` | Configuration management, manager singleton |
| `orm/` | Object-relational mapping: nodes, groups, users, computers, querybuilder |
| `parsers/` | Built-in parser plugins |
| `plugins/` | Plugin entry point system and factories |
| `repository/` | File repository abstraction layer |
| `restapi/` | Flask-based REST API (soon to be replaced by `aiida-restapi`) |
| `schedulers/` | Built-in HPC scheduler plugins (SLURM, PBS, SGE, LSF, etc.) |
| `storage/` | Storage backends (primarily `psql_dos` (`sqlite_dos`) for PostgreSQL (SQLite) + disk-objectstore) |
| `tools/` | Utility tools (graph visualization, archive operations, data dumping, etc.) |
| `transports/` | Built-in Transport plugins (SSH, local) |
| `workflows/` | Built-in workflows |

### Key entry points

| Area | Key file(s) | Purpose |
|------|------------|---------|
| Engine core | `src/aiida/engine/processes/process.py` | Base `Process` class |
| CalcJob | `src/aiida/engine/processes/calcjobs/calcjob.py` | `CalcJob` implementation |
| CalcJob file ops | `src/aiida/engine/daemon/execmanager.py` | File copying, job submission, retrieval |
| WorkChain | `src/aiida/engine/processes/workchains/workchain.py` | `WorkChain` implementation |
| ORM node | `src/aiida/orm/nodes/node.py` | Base `Node` class |
| QueryBuilder | `src/aiida/orm/querybuilder.py` | Query interface for the provenance graph |
| Process runner | `src/aiida/engine/runners.py` | `Runner` executes and submits processes |
| Plugin factories | `src/aiida/plugins/factories.py` | `DataFactory`, `CalculationFactory`, etc. |
| Storage ABC | `src/aiida/orm/implementation/storage_backend.py` | `StorageBackend` abstract base class |
| Transport ABC | `src/aiida/transports/transport.py` | `Transport`, `BlockingTransport`, `AsyncTransport` |
| Scheduler ABC | `src/aiida/schedulers/scheduler.py` | `Scheduler` base class |

Other notable files: `ProcessBuilder` (`engine/processes/builder.py`), `Computer` (`orm/computers.py`), `Config` (`manage/configuration/config.py`), `Manager` (`manage/manager.py`), `DaemonClient` (`engine/daemon/client.py`), `Profile` (`manage/configuration/profile.py`), `psql_dos` backend (`storage/psql_dos/backend.py`), `RabbitmqBroker` (`brokers/rabbitmq/broker.py`), `Repository` (`repository/repository.py`).

### Key design concepts

- **Provenance:** all data and computations are tracked as nodes in a directed acyclic graph (DAG).
  Nodes are immutable once stored, with one exception: `ProcessNode` exposes a small whitelist of `_updatable_attributes` (process state, exit status, checkpoint, etc.) that the engine can still modify on a stored node until `seal()` is called at process termination.
- **Process/Node duality:** processes (`CalcJob`, `WorkChain`, `calcfunction`, `workfunction`) define *how* to run; process nodes record *that* something ran.
- **Plugin system:** entry points (`pyproject.toml` `[project.entry-points]`) allow extending AiiDA with new calculation types, data types, schedulers, transports, and storage backends.
- **Public API:** anything importable from a second-level package (e.g., `from aiida.orm import ...`, `from aiida.engine import ...`) is considered public API with deprecation guarantees.
  In practice, what constitutes "public API" is not strictly enforced and depends on the user type: workflow users interact mainly with the CLI and high-level ORM, workflow developers use the engine and process APIs, and plugin developers rely on ABCs and entry point interfaces.
  Deeper internal modules may change without deprecation notices.
- **Data compatibility:** data created with older AiiDA versions is guaranteed to work with newer versions.
  Database migrations are applied automatically when needed.

### Database and file storage

- ORM: SQLAlchemy. File storage: disk-objectstore. Migrations: Alembic (under `src/aiida/storage/psql_dos/migrations/`).
- Main backend: `psql_dos` (PostgreSQL + disk-objectstore). Lightweight: `sqlite_dos` (SQLite + disk-objectstore).

### Abstract base classes (ABCs)

AiiDA defines ABCs for extensible components.
To create a plugin, implement the corresponding ABC and register it as an entry point.

| ABC | Location | Purpose | Entry point |
|-----|----------|---------|-------------|
| `Transport` | `aiida.transports.transport` | File transfer and remote command execution | `aiida.transports` |
| `Scheduler` | `aiida.schedulers.scheduler` | HPC job scheduler interface | `aiida.schedulers` |
| `Parser` | `aiida.parsers.parser` | Parse calculation outputs | `aiida.parsers` |
| `StorageBackend` | `aiida.orm.implementation.storage_backend` | Database and file storage | `aiida.storage` |
| `AbstractCode` | `aiida.orm.nodes.data.code.abstract` | Code/executable representation | `aiida.data` |
| `CalcJobImporter` | `aiida.engine.processes.calcjobs.importer` | Import existing calculation results | `aiida.calculations.importers` |

### Process / Node duality

Each process class has a corresponding node class that records its execution:

| Process class | Node class | Link types |
|--------------|------------|------------|
| `CalcJob` | `CalcJobNode` | INPUT_CALC → CREATE |
| `WorkChain` | `WorkChainNode` | INPUT_WORK → RETURN/CALL |
| `@calcfunction` | `CalcFunctionNode` | INPUT_CALC → CREATE |
| `@workfunction` | `WorkFunctionNode` | INPUT_WORK → RETURN/CALL |

### Project configuration

`pyproject.toml` (dependencies, entry points, ruff/mypy config), `uv.lock`, `.pre-commit-config.yaml`, `.readthedocs.yml`, `.github/workflows/`, `.docker/`.

## Development conventions

### Code style

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

**Documentation style** (when writing/editing `.md` or `.rst` files in `docs/`):

- Write **one sentence per line** (no manual line wrapping) &mdash; makes diffs easy to review
- File/directory names: alphanumeric, lowercase, underscores as separators
- Headers in **sentence case** (e.g., "Entry points")
- Documentation follows the [Divio documentation system](https://www.divio.com/blog/documentation/): tutorials (learning-oriented), how-to guides (goal-oriented), topics (understanding-oriented), reference (information-oriented)

### Testing

- Framework: `pytest`. Install and run: `uv sync && uv run pytest`
- Quick subset (no PostgreSQL/RabbitMQ): `uv run pytest -m presto`
- Parallel execution: `uv run pytest -n auto`
- Tests in `tests/` mirror the source structure
- `presto`-marked tests use `SqliteTempBackend` (in-memory, no external services). If they fail, the issue is in the code, not in service configuration.
- Transport tests require passwordless SSH to localhost
- Reusable fixtures in `tests/conftest.py`

Test philosophy:

- **Prefer real objects over mocks**: Use fixtures to create real nodes, processes, etc.
  Mocks should only be used for truly external dependencies (e.g., network calls, SSH connections), cases where setup would be too complex, or where it is otherwise difficult to get the desired behavior (e.g., mocking to enforce exceptions being raised that would not appear naturally).
- **Don't chase coverage with shallow tests**: A test that mocks everything tests nothing.
- **Test the contract, not the implementation**: Don't assert internal method calls; assert observable outcomes.
- **Make assertions as strong as possible**: `assert result == expected_value`, not `assert result is not None`. Check exact values, types, and lengths.
- **Regression tests for bugs**: First write a test that reproduces the bug, then fix the code.
- **Use `pytest.mark.parametrize`** for input variations instead of duplicating test logic.
- **Use existing fixtures**: Check `tests/conftest.py` before writing ad-hoc setup.
- **Test isolation**: Each test must be independent. **One behavior per test**. **Deterministic**: no timing/randomness dependencies. **Don't test framework behavior** (Python, SQLAlchemy, Click).

### Development commands

```bash
# Install development dependencies (uses uv.lock)
uv sync

# Run tests
uv run pytest                                     # Full suite
uv run pytest -m presto                           # Quick (no PostgreSQL/RabbitMQ)
uv run pytest tests/orm/test_nodes.py             # Specific module
uv run pytest -n auto                             # Parallel

# Pre-commit
uv run pre-commit                                 # Staged files
uv run pre-commit run --all-files                 # Everything
uv run pre-commit run mypy                        # Specific hook

# Build documentation
uv run sphinx-build -b html docs/source docs/build/html

# AiiDA-specific commands
verdi shell                       # Interactive IPython shell with AiiDA loaded
verdi status                      # Check status of services (daemon, PostgreSQL, RabbitMQ)
verdi daemon start/stop/restart   # Manage the daemon
verdi devel launch-add            # Launch test ArithmeticAddCalculation
verdi devel launch-multiply-add   # Launch test MultiplyAddWorkChain
verdi devel check-load-time       # Check for import slowdowns
verdi calcjob gotocomputer <PK>   # Jump to CalcJob's remote working directory on HPC
verdi process dump <PK>           # Dump a single process and its provenance
```

`verdi` subcommand implementations live in `src/aiida/cmdline/commands/cmd_*.py` (e.g., `cmd_process.py`, `cmd_calcjob.py`, `cmd_devel.py`).

Set `AIIDA_WARN_v3=1` to surface deprecation warnings.

### Branching and versioning

- All development happens on `main` through pull requests
- Recommended branch naming convention: `<prefix>/<issue>/<short_description>`
  - Prefixes: `feature/`, `fix/`, `docs/`, `ci/`, `refactor/`
  - Example: `fix/1234/querybuilder-improvements`
- The `main` branch uses a `.post0` version suffix to indicate development after the last release (e.g., `2.6.0.post0` = development after `2.6.0`)
- Versioning follows [SemVer](https://semver.org/) (major.minor.patch)

### Commit style (not enforced)

Follow the **50/72 rule**:

- Subject line: max 50 characters, imperative mood ("Add feature", not "Added feature"), capitalized, no period
- Body: wrap at 72 characters, explain *what* and *why* (the code shows *how*)
- Merged PRs (via squash) append the PR number: `Fix bug in QueryBuilder (#1234)` (GH web UI automatically appends on squash-merge)
- Some contributors use emoji prefixes as a semantic type indicator (see [Up for discussion](#up-for-discussion) for details)

```
Short summary in imperative mood (50 chars)

More detailed explanation wrapped at 72 characters. Focus on
why the change was made, not how.
```

Guidelines:

- One issue per commit, self-contained changes &mdash; makes bisecting and reverting safe
- Link GitHub issues either via the PR description or the GH web UI.

### Best practices (not enforced)

**Code quality:**

- Prefer pure functions without side effects where possible.
- Prefer explicit keyword arguments over positional, especially for same-type parameters. Minimize `*args`/`**kwargs`.

**Error handling:**

- Use `aiida.common.exceptions` for AiiDA-specific exceptions so callers can catch predictable, typed errors.
  Use `aiida.common.warnings` for non-fatal issues so users can selectively filter them.
  Assign exception messages to a local variable before raising:
  ```python
  msg = f'WorkGraph process<{workgraph.process.pk}> already created. Use submit() instead.'
  raise ValueError(msg)
  ```

**Adding dependencies:**

Before adding a new dependency to `pyproject.toml`, ensure it:

- Fills a non-trivial feature gap not easily resolved otherwise
- Is actively maintained
- Supports all Python versions supported by aiida-core
- Is available on both [PyPI](https://pypi.org/) and [conda-forge](https://conda-forge.org/)
- Uses an MIT-compatible license (MIT, BSD, Apache, LGPL &mdash; **not** GPL)

**Git tooling:**

- The `.git-blame-ignore-revs` file lists commits that should be ignored by `git blame` (e.g., bulk reformatting or whitespace-only changes). When landing a large-scale formatting-only commit, add its SHA to this file so that future `git blame` output stays meaningful. [Optional: `git config blame.ignoreRevsFile .git-blame-ignore-revs` makes local `git blame` honor it automatically.]

### Up for discussion

The following practices are used by some contributors but not consistently adopted.
They may be formalized or dropped in the future.

- **Emoji prefixes in commit messages**: Some contributors use emojis as a one-character semantic type prefix.
  The emoji *is* the type indicator, so the message after it should be just the description: write `🐛 QueryBuilder crashes on empty filter`, not `🐛 Fix: QueryBuilder crashes on empty filter`.
  Emoji selection is adapted from [MyST-Parser](https://github.com/executablebooks/MyST-Parser/blob/master/AGENTS.md#commit-message-format):

  | Emoji | Meaning | Branch Prefix |
  |-------|---------|---------------|
  | `✨` | New feature | `feature/` |
  | `🐛` | Bug fix | `fix/` |
  | `🚑` | Hotfix (urgent production fix) | `hotfix/` |
  | `👌` | Improvement (no breaking changes) | `improve/` |
  | `‼️` | Breaking change | `breaking/` |
  | `📚` | Documentation | `docs/` |
  | `🔧` | Maintenance (typos, etc.) | `chore/` |
  | `🧪` | Tests or CI changes only | `test/` |
  | `♻️` | Refactoring | `refactor/` |
  | `⬆️` | Dependency upgrade | `deps/` |
  | `🔖` | Release | `release/` |

### Pull request requirements

When submitting changes:

1. **Description**: Include a meaningful description explaining the change and link to related issues
1. **Tests**: Include test cases for new functionality or bug fixes
1. **Documentation**: Update docs if behavior changes or new features are added
1. **Code quality**: Ensure `uv run pre-commit` passes

Merging (maintainers): **Squash and merge** for single-issue PRs, **rebase and merge** for multi-commit PRs with individually significant commits.

## Debugging

### Diagnosing process failures

```bash
verdi process status <PK>       # Call stack and where it stopped
verdi process report <PK>       # Log messages emitted during execution
verdi process show <PK>         # Inputs, outputs, exit code
verdi node show <PK>            # Node attributes and extras
```

### Diagnosing daemon issues

```bash
verdi daemon logshow            # Tail daemon logs in real-time
verdi process repair            # Fix processes stuck after a daemon crash
```

### Common issues

- **Process stuck in `waiting`**: Usually means the daemon lost track of it. Run `verdi process repair` to requeue.
- **Test failures with `presto` marker**: These tests use `SqliteTempBackend` (in-memory, no external services). If they fail, the issue is in the code, not in service configuration.

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

### Adding a CLI command (aiida-core only)

1. Create command in `src/aiida/cmdline/commands/`
1. Use Click decorators and AiiDA's custom decorators from `aiida.cmdline.utils.decorators`
1. Register in the appropriate command group
1. Add tests in `tests/cmdline/commands/`

### Deprecations

When deprecating Python API:

```python
import warnings
from aiida.common.warnings import AiidaDeprecationWarning

warnings.warn('Use new_function() instead', AiidaDeprecationWarning)
```

For CLI commands, use `@decorators.deprecated_command()` from `aiida.cmdline.utils.decorators`.

Add `.. deprecated:: vX.Y.Z` notes in docstrings with replacement guidance.

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
