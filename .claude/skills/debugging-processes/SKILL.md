---
name: debugging-processes
description: Use for failed, stuck, or misbehaving AiiDA processes and daemon workers.
---

# Debugging processes

## Process inspection

```bash
verdi process status <PK>  # call stack and stopped execution
verdi process report <PK>  # execution logs
verdi process show <PK>    # inputs, outputs, exit code
verdi node show <PK>       # node summary and provenance
verdi node attributes <PK> # attributes
verdi node extras <PK>     # extras
verdi process dump <PK>    # provenance, including input/output files
verdi calcjob gotocomputer <PK>  # remote working directory; requires SSH
```

## Daemon inspection

```bash
verdi status          # storage, daemon, broker if configured
verdi daemon logshow  # live logs; one worker avoids interleaved output
verdi process repair  # requeue; stop daemon first
```

* Stuck `waiting` after crash/restart: daemon may have lost the process; use the repair sequence above.
* Inconsistent state: check `seal()`; stored `ProcessNode` updates are limited to `_updatable_attributes` before sealing.
* `presto` failures: no external services; inspect code first.
* Daemon subprocesses: `start_new_session=True` for signal isolation during shutdown.

## Interactive inspection

```bash
verdi shell                     # IPython with AiiDA loaded
verdi devel run-sql "SELECT ..." # PostgreSQL only; use with caution
```

```python
from aiida.orm import Node, QueryBuilder, load_node

qb = QueryBuilder().append(Node, filters={'node_type': {'like': 'data.core.dict.%'}})
node = load_node(123)  # replace with the node PK
node.base.attributes.all
node.base.extras.all  # mutable after storing
node.base.repository.list_object_names()
```

## Source

* Runner: `src/aiida/engine/runners.py`
* Daemon: `src/aiida/engine/daemon/client.py`
* File/job operations: `src/aiida/engine/daemon/execmanager.py`
* Transport tasks: `src/aiida/engine/processes/calcjobs/tasks.py`
