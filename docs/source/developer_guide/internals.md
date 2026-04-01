# Architecture overview

This page provides a high-level overview of AiiDA's internal architecture for developers working on `aiida-core`.
For user-facing documentation, see the {doc}`topics </topics/index>` section.

## Package structure

The source code lives under `src/aiida/` with these main packages:

| Package | Purpose |
|---------|---------|
| `brokers/` | Message broker interface (RabbitMQ via [kiwipy](https://github.com/aiidateam/kiwipy)) |
| `calculations/` | Built-in calculation plugins |
| `cmdline/` | CLI (`verdi` command) built with [click](https://click.palletsprojects.com/) |
| `common/` | Shared utilities, exceptions, warnings, constants |
| `engine/` | Workflow engine: runner, daemon, persistence, transport tasks (with [plumpy](https://github.com/aiidateam/plumpy)) |
| `manage/` | Configuration and profile management, manager singleton |
| `orm/` | Object-relational mapping: nodes, groups, users, computers, querybuilder |
| `parsers/` | Built-in parser plugins |
| `plugins/` | Plugin entry point system |
| `repository/` | File repository abstraction layer |
| `schedulers/` | Built-in HPC scheduler plugins (SLURM, PBS, SGE, LSF, etc.) |
| `storage/` | Storage backends (`psql_dos` for PostgreSQL, `sqlite_dos` for SQLite, both with disk-objectstore) |
| `tools/` | Utility tools (graph visualization, archive operations, data dumping, etc.) |
| `transports/` | Built-in transport plugins (SSH, local) |
| `workflows/` | Built-in workflows |

## Key design concepts

### Provenance and immutability

All data and computations are tracked as nodes in a directed acyclic graph (DAG).
Nodes become **immutable once stored** — any attempt to modify attributes of a stored node raises an exception.
This guarantees reproducibility: the provenance graph is a permanent record of how data was produced.

For details on the provenance model, see {ref}`topics:provenance:concepts`.

#### Updatable attributes and sealing

{py:class}`~aiida.orm.nodes.process.process.ProcessNode` is a special case: it must be stored to be runnable, but its state (an attribute) changes as it executes.
The {py:class}`~aiida.orm.utils.mixins.Sealable` mixin solves this by defining `_updatable_attributes` — attributes that remain mutable even after the node is stored.
Once a process finishes, it is **sealed**, after which even updatable attributes become immutable.

### Process / node duality

Processes define *how* computations run; process nodes record *that* something ran.
Each process class has a corresponding node class:

| Process class | Node class | Input link | Output link |
|--------------|------------|------------|-------------|
| `CalcJob` | `CalcJobNode` | `INPUT_CALC` | `CREATE` |
| `WorkChain` | `WorkChainNode` | `INPUT_WORK` | `RETURN` / `CALL` |
| `@calcfunction` | `CalcFunctionNode` | `INPUT_CALC` | `CREATE` |
| `@workfunction` | `WorkFunctionNode` | `INPUT_WORK` | `RETURN` / `CALL` |

For details, see {ref}`topics:processes:concepts`.

### Plugin system

AiiDA is extensible via entry points (`pyproject.toml` `[project.entry-points]`).
Plugins can provide new calculation types, data types, schedulers, transports, and storage backends by implementing the corresponding abstract base class (ABC):

| ABC | Module | Entry point group |
|-----|--------|-------------------|
| `Transport` | `aiida.transports.transport` | `aiida.transports` |
| `Scheduler` | `aiida.schedulers.scheduler` | `aiida.schedulers` |
| `Parser` | `aiida.parsers.parser` | `aiida.parsers` |
| `StorageBackend` | `aiida.orm.implementation.storage_backend` | `aiida.storage` |

For details, see {ref}`topics:plugins`.

### Public API

Anything importable from a second-level package (e.g., `from aiida.orm import ...`, `from aiida.engine import ...`) is considered public API with deprecation guarantees.
Deeper internal modules may change without deprecation notices.
See {doc}`deprecations` for the deprecation policy.

## Class hierarchies

:::{tip}
The `AGENTS.md` file in the repository root contains detailed Mermaid class diagrams for the ORM entity/node hierarchy, the engine process hierarchy, and the storage/transport/scheduler hierarchy.
:::

### ORM: Entity and Node

All persistent objects inherit from {py:class}`~aiida.orm.entities.Entity`.
Nodes form the provenance graph:

- {py:class}`~aiida.orm.nodes.data.data.Data` — data nodes (inputs and outputs of processes)
- {py:class}`~aiida.orm.nodes.process.process.ProcessNode` — records of process execution
  - {py:class}`~aiida.orm.nodes.process.calculation.CalculationNode` — records of calculations
  - {py:class}`~aiida.orm.nodes.process.workflow.WorkflowNode` — records of workflows

### Storage backends

| Backend | Database | Use case |
|---------|----------|----------|
| `psql_dos` | PostgreSQL + disk-objectstore | Production |
| `sqlite_dos` | SQLite + disk-objectstore | Lightweight / development |
| `sqlite_temp` | SQLite in-memory | Testing |
| `sqlite_zip` | SQLite archive | Archive import/export |

## Daemon and signal handling

The daemon captures `SIGINT` and `SIGTERM` for graceful shutdown.
When writing code that creates subprocesses inside the daemon, use `start_new_session=True` to prevent the subprocess from being killed by signals intended for the daemon.
See {ref}`topics:daemon:signals` for details.
