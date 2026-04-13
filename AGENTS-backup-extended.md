# AGENTS.md - Extended / removed content for review

Content removed or condensed during alignment with [Claude Code best practices](https://code.claude.com/docs/en/best-practices).
Each section notes its current status in the main `AGENTS.md` (condensed to a one-liner, partially kept, or removed entirely) and **why** the change was made.
After review, this file can be deleted.

---

## Database and file storage (condensed to 2 lines in `AGENTS.md`: discoverable from `pyproject.toml` dependencies and source code)

- **ORM:** SQLAlchemy (for node metadata, attributes, links, etc.)
- **File storage:** disk-objectstore (for file contents associated with nodes)
- **Migrations:** Alembic (under `src/aiida/storage/psql_dos/migrations/`)
- **High-performance storage backend:** `psql_dos` (PostgreSQL + disk-objectstore)
- **Lightweight storage backend:** `sqlite_dos` (SQLite + disk-objectstore)

## Internal ABCs table (removed entirely: infrastructure detail, discoverable from code)

| ABC | Location | Purpose |
|-----|----------|---------|
| `Entity` | `aiida.orm.entities` | Base for all ORM entities |
| `Collection` | `aiida.orm.entities` | Entity collection interface |
| `BackendEntity` | `aiida.orm.implementation.entities` | Backend entity implementation |
| `BackendQueryBuilder` | `aiida.orm.implementation.querybuilder` | Query builder backend |
| `AbstractRepositoryBackend` | `aiida.repository.backend.abstract` | File repository storage |
| `ArchiveFormatAbstract` | `aiida.tools.archive.abstract` | Archive format handler |

## Project configuration (condensed to 1 line in `AGENTS.md`: all discoverable by `ls` at repo root)

- `pyproject.toml` - Project configuration, dependencies, and entry points
- `uv.lock` - Locked dependencies (managed by `uv`)
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `.readthedocs.yml` - Documentation build configuration
- `.github/workflows/` - CI workflow definitions
- `.docker/` - Docker and Docker Compose configurations

## Formatting and linting details (condensed to 1 line in `AGENTS.md`: discoverable from `pyproject.toml [tool.ruff]`)

- Auto-formatted by `ruff format` (single quotes, PEP 8 compliance)
- Enabled lint rule sets (see `[tool.ruff.lint]` in `pyproject.toml`):
  `E`/`W` (pycodestyle), `F` (pyflakes), `I` (isort), `N` (pep8-naming),
  `PLC`/`PLE`/`PLR`/`PLW` (pylint), `RUF` (ruff-specific), `FLY` (f-string enforcement), `NPY201` (NumPy 2.0 compatibility)

## Type checking details (condensed to 1 line in `AGENTS.md`: discoverable from `.pre-commit-config.yaml`)

- Add type hints to new code &mdash; checked by `mypy` in pre-commit (CI runs the same pre-commit hooks, so it catches anything missed locally)
- Enables static analysis, IDE autocompletion, and serves as machine-verified documentation

## Docstring example (condensed to 1 line in `AGENTS.md`: standard Sphinx style, one-liner reference suffices)

```python
def put_object_from_filelike(self, handle: BinaryIO) -> str:
    """Store the byte contents of a file in the repository.

    :param handle: filelike object with the byte content to be stored.
    :return: the generated fully qualified identifier for the object within the repository.
    :raises TypeError: if the handle is not a byte stream.
    """
```

## Source file header block (condensed to 1 line in `AGENTS.md`: replaced with "copy from existing file")

```python
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
```

## Other pre-commit hooks list (condensed to 1 line in `AGENTS.md`: discoverable from `.pre-commit-config.yaml`)

- `uv-lock` &mdash; validates lockfile consistency
- `check-yaml`, `check-merge-conflict` &mdash; basic file checks
- `pretty-format-toml`, `pretty-format-yaml` &mdash; auto-format TOML/YAML files
- `nbstripout` &mdash; strips output from Jupyter notebooks
- `imports` &mdash; auto-generates `__all__` imports for `src/aiida/`
- `generate-conda-environment`, `validate-conda-environment` &mdash; keeps `environment.yml` in sync with `pyproject.toml`
- `verdi-autodocs` &mdash; auto-generates verdi CLI documentation

## Key entry points rows (condensed to a single "Other notable files" line in `AGENTS.md`: trimmed to ~11 most critical files in the table)

| Area | Key file(s) | Purpose |
|------|------------|---------|
| Broker ABC | `src/aiida/brokers/broker.py` | `Broker` &mdash; message broker interface |
| CalcJob lifecycle | `src/aiida/engine/processes/calcjobs/tasks.py` | Upload, submit, retrieve, stash, kill tasks |
| Computer | `src/aiida/orm/computers.py` | `Computer` entity (represents a computational resource) |
| Configuration | `src/aiida/manage/configuration/config.py` | `Config` &mdash; global AiiDA configuration |
| Daemon | `src/aiida/engine/daemon/client.py` | `DaemonClient` &mdash; daemon communication |
| Manager | `src/aiida/manage/manager.py` | Global singleton managing profiles, backends, runners |
| ORM entities | `src/aiida/orm/entities.py` | Base `Entity` and `Collection` classes |
| Plugin entry points | `src/aiida/plugins/entry_point.py` | Entry point loading and discovery |
| Process builder | `src/aiida/engine/processes/builder.py` | `ProcessBuilder` used to construct process inputs |
| Profile | `src/aiida/manage/configuration/profile.py` | `Profile` &mdash; configuration for a single profile |
| psql_dos backend | `src/aiida/storage/psql_dos/backend.py` | PostgreSQL + disk-objectstore implementation |
| RabbitMQ broker | `src/aiida/brokers/rabbitmq/broker.py` | `RabbitmqBroker` implementation |
| Repository | `src/aiida/repository/repository.py` | `Repository` &mdash; file storage interface per node |
| Repository backend | `src/aiida/repository/backend/abstract.py` | `AbstractRepositoryBackend` ABC |
| Scheduler data | `src/aiida/schedulers/datastructures.py` | `JobTemplate`, `JobInfo`, `JobResource` |

## Standard testing info (partially kept in `AGENTS.md`: framework, run commands, and `presto` marker retained; other markers and test-types table removed as discoverable from `pyproject.toml [tool.pytest]`)

- Framework: `pytest`
- Install and run: `uv sync && uv run pytest`
- Parallel execution: `uv run pytest -n auto` (via `pytest-xdist` plugin)
- Use `AIIDA_TEST_PROFILE=<profile>` to run against a specific test profile
- Test markers:
  - `presto` - fast tests without external services
  - `requires_rmq` - requires RabbitMQ
  - `requires_psql` - requires PostgreSQL
  - `nightly` - long-running tests (CI only)

Test types:
| Type | Location | Description |
|------|----------|-------------|
| Unit/Integration | `tests/` | Main test suite, runs on every PR |
| Benchmark | `tests/benchmark/` | Performance tests, runs on `main`, results tracked via `gh-pages` |
| System | `.github/system_tests/` | Infrastructure tests (daemon, remote) |

## Standard test philosophy items (condensed to 1 line in `AGENTS.md`: standard software engineering advice)

- **Test isolation**: Each test must be independent &mdash; never rely on execution order or state left by other tests.
- **One behavior per test**: A test should verify a single logical behavior. If a test name needs "and", it's likely testing too much.
- **Test edge cases and failure paths**: Don't just test the happy path. Test boundary values, empty inputs, invalid arguments, and expected exceptions.
- **Deterministic tests**: Tests must not depend on timing, randomness, or external state. Flaky tests erode trust in the suite.
- **Don't test framework behavior**: Don't write tests that just verify that Python, SQLAlchemy, or Click work correctly. Only test your own logic.

## Standard development commands (kept in `AGENTS.md` in condensed form: without them Claude tries bare `python`/`pip` and fails; kept as compact command block)

```bash
# Install development dependencies (uses uv.lock)
uv sync

# Run all tests
uv run pytest

# Run quick tests only (no RabbitMQ/PostgreSQL required)
uv run pytest -m presto

# Run tests for a specific module
uv run pytest tests/orm/

# Run a specific test
uv run pytest tests/orm/test_nodes.py::test_node_label

# Run with coverage
uv run pytest --cov aiida

# Run tests in parallel
uv run pytest -n auto

# Pre-commit: staged files only
uv run pre-commit run

# Pre-commit: run specific hook (e.g., mypy, ruff)
uv run pre-commit run mypy
uv run pre-commit run ruff

# Pre-commit: all changes since branching off main
uv run pre-commit run --from-ref main --to-ref HEAD

# Pre-commit: all files (rarely needed)
uv run pre-commit run --all-files

# Build documentation
uv run sphinx-build -b html docs/source docs/build/html

# Interactive shell with AiiDA environment
verdi shell

# Service management
verdi status                    # Check status of services (daemon, PostgreSQL, RabbitMQ)
verdi daemon start/stop/restart # Manage the daemon
```

## Standard code quality advice (partially condensed in `AGENTS.md`: pure functions kept as one-liner; type annotations and docstrings kept as one-liners under Code style; testing advice covered in Testing section)

- **Type annotations**: Add type hints to new function signatures &mdash; unannotated public API is harder to use correctly and harder to refactor safely.
  Note: `mypy` runs in pre-commit/CI but many files are currently excluded.
- **Docstrings**: Use Sphinx-style docstrings (`:param:`, `:return:`, `:raises:`).
  Types are not required in docstrings as they should be in type hints &mdash; keeping them only in annotations avoids duplication that goes stale.
- **Pure functions**: Where possible, write pure functions without side effects &mdash; they are easier to test in isolation, reason about, and parallelize.
- **Testing**: Write tests for all new functionality.
  Tests should mirror the source structure so it is easy to find the test for any given module.

## API design section (condensed to 1 line in `AGENTS.md`: standard Python advice)

- Prefer explicit keyword arguments over positional arguments, especially when a function takes multiple parameters of the same type &mdash; `node.set_attribute(key='x', value=1)` is unambiguous at the call site; `node.set_attribute('x', 1)` requires the reader to check the signature.
  Keyword-only arguments (after a bare `*`) also protect callers from silent breakage if parameter order ever changes.
- Minimize use of `*args` and `**kwargs` where possible &mdash; explicit parameters allow static type checkers to validate arguments, improve IDE autocompletion, and make the function contract readable without opening the implementation.

## Commit style rationale (removed entirely: trimmed to keep rules only, not explanations)

- 50 chars keeps `git log --oneline` output readable without truncation; imperative mood reads as an instruction applied to the codebase ("if applied, this commit will…")
- 72 chars matches the traditional terminal width for `git log` output

## PR etiquette and merge strategies (partially kept in `AGENTS.md`: merge strategies condensed to 1 line; PR etiquette removed as standard/discoverable)

PR etiquette:

- Open PR only when ready for review (each push triggers CI)
- Aim for reasonable number of LOC changed per PR for effective review

Merging (maintainers):

- **Squash and merge**: Single-issue PRs → one clean commit
- **Rebase and merge**: Multi-commit PRs with individually significant commits

## Database inspection (removed entirely: standard verdi shell / SQL usage)

```bash
verdi devel run-sql "SELECT ..."  # Run raw SQL against the profile database
verdi shell                       # Interactive IPython shell with AiiDA loaded
```

In the `verdi shell`, useful patterns:

```python
from aiida.orm import QueryBuilder, Node
# Find nodes by type
qb = QueryBuilder().append(Node, filters={'node_type': {'like': 'data.core.dict.%'}})

# Inspect a node's attributes
node = load_node(<PK>)
node.base.attributes.all
node.base.extras.all
node.base.repository.list_object_names()
```
