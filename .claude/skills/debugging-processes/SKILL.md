---
name: debugging-processes
description: Use when diagnosing failed, stuck, or misbehaving AiiDA processes or the daemon. Covers `verdi process status/report/show`, daemon log inspection, `verdi process repair`, and common failure modes like processes stuck in `waiting`.
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

For CalcJobs specifically, jump to the remote working directory on the HPC:

```bash
verdi calcjob gotocomputer <PK>
```

## Inspecting the daemon

```bash
verdi status                    # daemon + PostgreSQL + RabbitMQ status
verdi daemon logshow            # tail daemon logs in real-time
verdi process repair            # requeue processes stuck after a daemon crash
```

## Common failure modes

- **Process stuck in `waiting`** &mdash; usually means the daemon lost track of it after a crash or restart. Run `verdi process repair` to requeue.
- **Process state inconsistent with node attributes** &mdash; check whether `seal()` has been called; only `_updatable_attributes` can change on a stored `ProcessNode` before sealing.
- **`presto`-marked test failures** &mdash; these use an in-memory `SqliteTempBackend`, so the bug is in the code, not in service configuration.
- **Daemon subprocess killed on shutdown** &mdash; daemon-launched subprocesses must pass `start_new_session=True` or they inherit the daemon's signal handling and die with it.

## Related source

- Process runner: `src/aiida/engine/runners.py`
- Daemon client: `src/aiida/engine/daemon/client.py`
- CalcJob exec manager (file copying, job submission, retrieval): `src/aiida/engine/daemon/execmanager.py`
