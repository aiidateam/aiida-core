---
name: architecture-overview
description: Use when exploring the aiida-core codebase structure, looking for key files, or understanding how packages relate to each other. Contains the source layout table, key entry points, abstract base classes, and database/storage architecture.
---

# AiiDA Core Architecture

## Source layout

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

## Key entry points

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

## Database and file storage

- ORM: SQLAlchemy. File storage: disk-objectstore. Migrations: Alembic (under `src/aiida/storage/psql_dos/migrations/`).
- Main backend: `psql_dos` (PostgreSQL + disk-objectstore). Lightweight: `sqlite_dos` (SQLite + disk-objectstore).

## Abstract base classes (ABCs)

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

## Project configuration

`pyproject.toml` (dependencies, entry points, ruff/mypy config), `uv.lock`, `.pre-commit-config.yaml`, `.readthedocs.yml`, `.github/workflows/`, `.docker/`.
