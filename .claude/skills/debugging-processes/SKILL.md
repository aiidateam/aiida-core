---
name: debugging-processes
description: Use when diagnosing failed, stuck, or misbehaving AiiDA processes or the daemon.
---

# Debugging processes and the daemon

## Inspecting a single process

```bash
verdi process status <PK>       # call stack and where execution stopped
verdi process report <PK>       # log messages emitted during execution
verdi process show <PK>         # inputs, outputs, exit code
verdi node show <PK>            # node attributes and extras
```

For a full provenance dump including input/output files:

```bash
verdi process dump <PK>         # dump a process and its provenance
```

For CalcJobs specifically, jump to the remote working directory on the HPC (requires SSH access, which may not be available for sandboxed agents):

```bash
verdi calcjob gotocomputer <PK>
```

## Inspecting the daemon

```bash
# storage (PostgreSQL or SQLite) + daemon & broker (RabbitMQ, if configured):
verdi status
# tail daemon logs in real-time
# best with a single daemon worker, multiple workers garble output:
verdi daemon logshow
# requeue processes stuck after a daemon crash (stop the daemon first):
verdi process repair
```

## Common failure modes

- **Process stuck in `waiting`** : usually means the daemon lost track of it after a crash or restart. Run `verdi process repair` to requeue.
- **Process state inconsistent with node attributes** : check whether `seal()` has been called; only `_updatable_attributes` can change on a stored `ProcessNode` before sealing.
- **`presto`-marked test failures** : these use an in-memory `SqliteTempBackend`, so the bug is in the code, not in service configuration.
- **Daemon subprocess killed on shutdown** : daemon-launched subprocesses must pass `start_new_session=True` or they inherit the daemon's signal handling and die with it.

## Interactive inspection

```bash
verdi shell                       # interactive IPython shell with AiiDA loaded
verdi devel run-sql "SELECT ..."  # run raw SQL against the profile database (USE WITH CAUTION)
```

Useful patterns inside `verdi shell`:

```python
from aiida.orm import QueryBuilder, Node, load_node

# Find nodes by type
qb = QueryBuilder().append(Node, filters={'node_type': {'like': 'data.core.dict.%'}})

# Inspect a specific node
node = load_node(<PK>)
node.base.attributes.all   # all stored attributes
node.base.extras.all        # all extras (mutable even after storing)
node.base.repository.list_object_names()  # files in the node's repository
```

## Related source

- Process runner: `src/aiida/engine/runners.py`
- Daemon client: `src/aiida/engine/daemon/client.py`
- CalcJob exec manager (file copying, job submission, retrieval): `src/aiida/engine/daemon/execmanager.py`
- Transport tasks (submit, update, retrieve): `src/aiida/engine/processes/calcjobs/tasks.py`
