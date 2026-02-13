# AGENTS.md - AI Coding Assistant Guide for AiiDA Core

This file provides context for AI coding assistants (Claude Code, GitHub Copilot, etc.) working on the `aiida-core` codebase.

## Project overview

AiiDA is a workflow manager for computational science with a strong focus on provenance, performance, and extensibility.
It is written in Python (>=3.9) and uses PostgreSQL for storage and RabbitMQ for message brokering.

- **Repository:** https://github.com/aiidateam/aiida-core
- **Documentation:** https://aiida-core.readthedocs.io/
- **License:** MIT
- **Build system:** Flit (`flit_core.buildapi`)

## Architecture

### Source layout

The source code lives under `src/aiida/` with these main packages:

| Package | Purpose |
|---------|---------|
| `orm/` | Object-relational mapping: nodes, groups, querybuilder, users, computers |
| `engine/` | Workflow engine: process runner, daemon, persistence, transport tasks |
| `storage/` | Storage backends (primarily `psql_dos` for PostgreSQL + disk-objectstore) |
| `cmdline/` | CLI (`verdi` command) built with Click |
| `calculations/` | Built-in calculation plugins |
| `workflows/` | Built-in workflow plugins |
| `parsers/` | Built-in parser plugins |
| `schedulers/` | HPC scheduler plugins (SLURM, PBS, SGE, LSF, etc.) |
| `transports/` | Transport plugins (SSH, local) |
| `tools/` | Utility tools (graph visualization, archive operations, etc.) |
| `common/` | Shared utilities, exceptions, warnings, constants |
| `manage/` | Configuration management, manager singleton |
| `brokers/` | Message broker interface (RabbitMQ via kiwipy/plumpy) |
| `repository/` | File repository abstraction layer |
| `plugins/` | Plugin entry point system |
| `restapi/` | Flask-based REST API |

### Key design concepts

- **Provenance graph:** all data and computations are tracked as nodes in a directed acyclic graph (DAG). Nodes are immutable once stored.
- **Process/Node duality:** processes (CalcJob, WorkChain, calcfunction, workfunction) define *how* to run; process nodes record *that* something ran.
- **Plugin system:** entry points (`pyproject.toml` `[project.entry-points]`) allow extending AiiDA with new calculation types, data types, schedulers, transports, and storage backends.
- **Public API:** anything importable from a second-level package (e.g., `from aiida.orm import ...`, `from aiida.engine import ...`) is considered public API with deprecation guarantees.

### Database

- **ORM:** SQLAlchemy
- **Migrations:** Alembic (under `src/aiida/storage/psql_dos/migrations/`)
- **Primary storage backend:** `psql_dos` (PostgreSQL + disk-objectstore)

## Development conventions

### Code style

- PEP 8 + Google Python Style Guide
- Pre-commit hooks enforce formatting (`ruff`), type checking (`mypy`), and more
- Use f-strings (not `.format()` or `%`)
- Use `pathlib` (not `os.path`)
- Add type hints to new code
- Delay `aiida` imports to function level when possible (keeps `verdi` CLI responsive)

### Testing

- Framework: `pytest`
- Run: `pip install -e .[tests] && pytest`
- Quick subset: `pytest -m presto`
- Tests in `tests/` mirror the source structure
- Transport tests require passwordless SSH to localhost

### Branching

- All development happens on `main` through pull requests
- Branch naming: `issue_1234_short_description`
- The `main` branch uses a `.post0` version suffix

### Commit style

- Imperative mood, 72-char subject line
- One issue per commit, self-contained changes
- Reference GitHub issues in PR descriptions, not commit messages

## Key files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, tool configs, entry points |
| `src/aiida/__init__.py` | Package init, `__version__` attribute |
| `src/aiida/manage/manager.py` | Global manager singleton |
| `src/aiida/orm/querybuilder.py` | QueryBuilder for database queries |
| `src/aiida/engine/processes/` | Process base classes (CalcJob, WorkChain, etc.) |
| `src/aiida/cmdline/commands/` | `verdi` CLI command implementations |
| `src/aiida/storage/psql_dos/` | PostgreSQL storage backend + Alembic migrations |
| `tests/` | Test suite |
| `docs/` | Sphinx documentation |
| `.pre-commit-config.yaml` | Pre-commit hook configuration |

## Common tasks

### Adding a new `verdi` command

Commands are in `src/aiida/cmdline/commands/`. They use Click with custom parameter types from `src/aiida/cmdline/params/`.

### Adding a new data type

Subclass `aiida.orm.Data` in `src/aiida/orm/nodes/data/` and register an entry point in `pyproject.toml` under `[project.entry-points."aiida.data"]`.

### Modifying the database schema

Create an Alembic migration under `src/aiida/storage/psql_dos/migrations/`. Always provide both `upgrade()` and `downgrade()` functions. See the developer guide for details.
