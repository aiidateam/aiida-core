---
name: architecture-overview
description: Use for codebase navigation, key files, package relationships, and plugin interfaces.
---

# Architecture

## Packages under `src/aiida/`

* `brokers/`: messaging, including RabbitMQ support.
* `calculations/`, `parsers/`, `workflows/`: built-in plugins.
* `cmdline/`: Click-based `verdi` CLI.
* `common/`: utilities, exceptions, warnings, constants.
* `engine/`: runner, daemon, persistence, transport tasks.
* `manage/`: configuration and manager singleton.
* `orm/`: nodes, groups, users, computers, provenance queries.
* `plugins/`: entry points and factories.
* `repository/`: file repository abstraction.
* `restapi/`: Flask REST API; planned replacement is `aiida-restapi`.
* `schedulers/`: HPC schedulers (SLURM, PBS, SGE, LSF).
* `storage/`: PostgreSQL (`psql_dos`) and SQLite (`sqlite_dos`) backends.
* `tools/`: graphs, archives, data dumping, utilities.
* `transports/`: SSH and local transports.

## Key files relative to `src/aiida/`

* `engine/processes/process.py`: `Process`.
* `engine/processes/calcjobs/calcjob.py`: `CalcJob`.
* `engine/processes/workchains/workchain.py`: `WorkChain`.
* `engine/processes/builder.py`: `ProcessBuilder`.
* `engine/runners.py`: `Runner`.
* `engine/daemon/execmanager.py`: copying, submission, retrieval.
* `engine/daemon/client.py`: `DaemonClient`.
* `orm/nodes/node.py`: `Node`.
* `orm/querybuilder.py`: `QueryBuilder`.
* `orm/computers.py`: `Computer`.
* `plugins/factories.py`: `DataFactory`, `CalculationFactory`, other factories.
* `manage/configuration/{config,profile}.py`: `Config`, `Profile`.
* `manage/manager.py`: `Manager`.
* `storage/psql_dos/backend.py`: PostgreSQL backend.
* `brokers/rabbitmq/broker.py`: `RabbitmqBroker`.
* `repository/repository.py`: `Repository`.

## Storage and plugins

SQLAlchemy metadata; `disk-objectstore` files; Alembic migrations in `src/aiida/storage/psql_dos/migrations/`.
Plugins implement the ABC and register its entry point (module, entry-point group):

* `Transport`: `aiida.transports.transport`, `aiida.transports`; includes `BlockingTransport` and `AsyncTransport`.
* `Scheduler`: `aiida.schedulers.scheduler`, `aiida.schedulers`.
* `Parser`: `aiida.parsers.parser`, `aiida.parsers`.
* `StorageBackend`: `aiida.orm.implementation.storage_backend`, `aiida.storage`.
* `Code`: `aiida.orm.nodes.data.code`, `aiida.data`.
* `CalcJobImporter`: `aiida.engine.processes.calcjobs.importer`, `aiida.calculations.importers`.

## API stubs

Signatures, classes, annotations (`stubgen` ships with `mypy`, in the `pre-commit` extra; install with `uv sync --extra pre-commit`):

```bash
uv run stubgen -p aiida.orm -o /tmp/stubs
uv run stubgen -p aiida.orm -o /tmp/stubs --include-private
```


## Configuration

`pyproject.toml`: dependencies, entry points, Ruff/mypy.
Other configuration: `uv.lock`, `.pre-commit-config.yaml`, `.readthedocs.yml`, `.github/workflows/`, `.docker/`.
