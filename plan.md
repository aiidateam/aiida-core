# PostgreSQL Disconnect Resilience Plan

## Goal

Improve AiiDA Core's resilience to PostgreSQL connection loss (including TLS EOFs) so that:

- stale pooled connections are replaced before use where possible;
- a disconnect does not poison unrelated daemon processes;
- safe database reads and explicitly retryable transactions can recover;
- uncertain writes and external actions are reconciled instead of blindly replayed;
- prolonged database outages do not silently consume unfinished process tasks; and
- logging and shutdown remain useful when PostgreSQL is unavailable.

This plan does **not** promise exactly-once execution of arbitrary scheduler or plugin actions. If an action's outcome cannot be determined safely, AiiDA should expose an explicit recovery-required condition rather than silently repeat it.

## Evidence and scope

The report in [`postgres-tls-eof-investigation.md`](postgres-tls-eof-investigation.md) documents three distinct failure paths:

1. **Oct 20 and Oct 27, 2026 — continuation lookup:** `ProcessLauncher._continue()` fails in `load_node(pk=pid)` while QueryBuilder is establishing a SQLAlchemy SAVEPOINT, before process reconstruction or checkpoint handling. QueryBuilder cleanup closes the shared session. The broker's ordinary exception path normally acknowledges the task.
2. **Oct 21, 2026 — cancellation:** a live process fails reading `db_dbnode.attributes`; ORM logging then fails on the unusable SQLAlchemy transaction and masks the intended cancellation error handling.
3. **Shutdown:** EOF occurs during rollback/resource cleanup, after shutdown has begun; these traces do not identify the trigger for shutdown.

The daemon uses a thread-scoped SQLAlchemy session. Closing/removing or rolling back that session can affect other live processes in the same worker. A checkpoint-only retry does not cover the documented initial lookup failure. The investigation could not determine `DBAPIError.connection_invalidated`; matching the EOF message is not a sufficient retry classifier.

## Design principles

1. **Separate connection recovery from operation replay.** SQLAlchemy can invalidate and replace a broken connection, but an in-flight operation still fails. Retry is an application decision.
2. **Retry only classified disconnects.** Use SQLAlchemy's disconnect information, not text matching. Preserve the original exception and execution phase.
3. **Retry complete owned operations.** Never blindly retry `commit()`, an arbitrary statement, a shared transaction context, a whole process callback, or a whole CalcJob task.
4. **Isolate failure effects.** A failed recovery attempt must not close, commit, roll back, or detach another process's session work.
5. **Reconcile uncertainty.** A disconnect around commit or an external action can leave its outcome unknown. Query durable state or report a recovery-required condition; do not guess.
6. **Keep diagnostics independent of PostgreSQL.** A database logging failure must not replace the original exception or prevent cancellation and cleanup.
7. **Target the maintained AiiDA 2.9.x line.** This branch is based on upstream `support/2.9.x`, currently at the v2.9.4 tag. Do not base this work on current `main`, which contains the v3 migration and incompatible checkpoint changes.

## Target architecture

### A. Central storage disconnect policy

Add a small internal storage module that:

- classifies SQLAlchemy database failures as recognized disconnect, unknown commit outcome, exhausted recovery, or unrelated error;
- retains operation phase information (read, flush, commit, rollback/close) and original exception chaining;
- provides bounded retry/backoff primitives for operations that explicitly opt in;
- ensures resources owned by an attempt are released before any backoff; and
- leaves retry eligibility to the caller/domain operation rather than retrying all SQL transparently.

Do not perform retries or session resets from SQLAlchemy error event hooks. Avoid converting `PendingRollbackError` into a retry signal; it is a symptom that the transaction needs cleanup, not proof of the original cause.

### B. Pool checkout resilience

Use SQLAlchemy's supported pool options to detect stale idle connections before application work. Add a supported and validated profile configuration route for `pool_pre_ping`; consider enabling it by default after measuring checkout overhead and obtaining maintainer agreement. Keep `pool_recycle` optional and deployment-specific because there is no universal connection lifetime.

Document the ceiling clearly: pre-ping/recycle can handle stale connections at checkout, but cannot repair an in-flight query or transaction.

### C. Explicit storage-session ownership

The current thread-scoped ORM session is shared among process callbacks. General recovery requires clearer ownership.

Start with isolated storage operations:

- create a fresh session for retryable reads;
- return fully materialized scalar/DTO values, not live ORM models or streaming iterators;
- close only that attempt's session; and
- avoid moving detached ORM entities into the worker's shared session.

For daemon operations that need ORM entities, define a process/operation owner token and an explicit entity-transfer rule. Test propagation through async callbacks and greenback. Scope must also cover child/helper tasks, RPC cancellation, CLI, REST, notebooks, and synchronous workflows. Do not assume `asyncio.current_task()` or a bare `ContextVar` is sufficient without tracing propagation and model sharing.

Persistent entities crossing owners should normally cross by identifier and be reloaded in the receiving session. A later architectural stage may move more ORM work to owner-scoped sessions, but must not silently merge arbitrary live model objects.

### D. Retryable reads and transactions

**Reads:** retry complete, owned, materialized reads. A read retry must include all database-dependent preparation steps; a scalar preflight followed by the same vulnerable shared-session `load_node()` is not recovery. Do not restart streaming QueryBuilder iteration after yielding rows unless a separate resumable pagination contract is designed.

**Transactions:** add opt-in retries only for complete, owned database-only transactions. Each attempt must recreate its transaction and reload inputs. It must not span a broker await, greenback yield, scheduler/transport action, or unrelated process work. Audit QueryBuilder's streaming transaction behavior before changing it.

### E. Continuation preparation recovery

The first user-facing retry candidate is process continuation preparation, since the documented SAVEPOINT failure occurs before reconstruction/execution. The protected preparation must include every lookup/loading step needed to reconstruct process state, not just the first `load_node()` call.

The sequence should be:

1. Materialize required process metadata/checkpoint inputs in an isolated owned session.
2. On a classified transient disconnect, discard only the isolated attempt and retry with bounded backoff.
3. Reconstruct/attach process state exactly once after preparation succeeds.
4. Preserve existing missing-node, terminal-node, duplicate-subscriber, and exception handling semantics.

Do not retry the whole continuation after `super()._continue()` has started process execution.

Retry exhaustion is a separate broker-delivery decision. It must not be treated as an ordinary application exception that marks an unfinished node excepted or silently consumes the task.

### F. Conditional state and persistence writes

For process state, checkpoints, output references, and job IDs:

- make operations idempotent or guarded by expected version/generation;
- replay the complete owned transaction, never only `commit()`;
- avoid applying stale snapshots of whole JSON attributes over newer values;
- keep stable operation identifiers across attempts; and
- publish/broadcast state transitions only after durable writes succeed.

For unknown commit outcomes, atomically write a durable operation marker with the intended database mutation. On reconnect, check the marker/version: treat present as committed, absent as safe to reapply only if absence is established, otherwise defer.

Do not presume that all process-state/output/checkpoint mutations can be combined into one transaction; trace existing lifecycle ordering and its broadcast/parent-process invariants first.

### G. Broker settlement and long outages

For short outages, keep bounded local retries inside the task attempt and pause dependent work.

For persistent outages, introduce an explicit deferred-storage outcome understood by RabbitMQ and ZeroMQ adapters:

- retain/requeue delivery without acknowledging unfinished work;
- apply outage backoff and avoid hot requeue loops;
- stop or limit new work for an affected execution path;
- ensure the worker relinquishes execution before another worker may resume it; and
- respect broker acknowledgment, heartbeat, timeout, and delivery-lifetime semantics.

Before automatically redelivering work that may still be running, add distributed ownership with a generation/fencing token. Durable state writes must verify the current token so an old worker cannot overwrite a newer owner. Fencing cannot cancel an external action already in flight. Cover `nowait` background process tasks as well as request/response tasks.

### H. External-action reconciliation

Use operation-specific intent/result records and stable action identifiers around external effects:

```text
persist intent -> perform external action -> persist result -> advance process state
```

| Action | Recovery direction |
|---|---|
| Scheduler submission | Retain a returned job ID in memory and retry persistence without resubmitting. After worker loss, query by a stable token where supported. |
| Scheduler submission with unknown outcome | Do not submit again blindly. Reconcile by scheduler query/token; otherwise mark recovery required for user/operator resolution. |
| Scheduler cancellation | Read state through safe storage, request cancellation, then verify scheduler status before repeating an uncertain request. Account for job-ID reuse. |
| Upload/retrieval | Reconcile partial files and durable output links; preserve/use existing partial-transfer recovery, and avoid duplicate nodes/links. |
| Stashing/destructive cleanup | Require operation-specific completion evidence or explicit intervention. |
| Arbitrary plugin/WorkChain actions | Retry only when the plugin declares and implements idempotency/reconciliation. |

Maintain and test existing safeguards such as reusing a persisted scheduler job ID and skipping already persisted upload/retrieval outputs. They do not solve the “external action succeeded, result was not persisted” window.

Exactly-once behavior is not generally achievable for external systems that provide neither idempotency keys nor reliable lookup by a stable token.

### I. Logging and shutdown

**Logging:** ensure ORM database-log writes use appropriate owned storage; failures must not mask the triggering exception. Provide a non-recursive file/stderr fallback, avoid unbounded buffering/retry, and include sanitized worker/process/operation/phase/attempt/classification information.

**Shutdown:** stop accepting work, stop retries from starting new actions, quiesce/cancel tasks, settle broker deliveries according to policy, and attempt independent cleanup steps even if rollback/close fails. Keep cleanup diagnostics outside ORM logging. Do not reconnect to resume process execution during shutdown.

## Implementation sequence and PRs

Each PR should be independently testable, documented, and include an accurate `Unreleased` changelog entry when behavior/configuration changes.

### PR 1 — Fault-injection tests and diagnostics

- Add disposable PostgreSQL tests for classified disconnects and SQLAlchemy invalidation metadata.
- Add deterministic hooks for EOF/failure injection at SAVEPOINT, expired-field SELECT, flush, commit acknowledgment, rollback, and close.
- Record transaction phase and classification in sanitized non-DB test diagnostics.
- Capture baseline behavior for two simultaneous live process objects and pending writes.

### PR 2 — Logging and shutdown hardening

- Prevent ORM logging-handler errors from replacing the original operational exception.
- Add a non-recursive fallback logger.
- Make worker cleanup best-effort, preserving the original failure and attempting remaining cleanup.
- Test shutdown after a broken connection separately from active-operation EOF.

### PR 3 — Pool checkout resilience

- Expose and validate `pool_pre_ping` through supported profile configuration; decide default based on maintainer feedback and measured overhead.
- Document pre-ping/recycle scope and limitations.
- Test stale idle connection replacement.

### PR 4 — Owned reads and continuation preparation

- Implement fresh-session materialized reads.
- Cover full continuation preparation, not only its first lookup.
- Add bounded retry for classified transient disconnects before process execution starts.
- Verify another live process/session remains usable and process reconstruction occurs once.
- Decide exhausted-retry broker semantics before deployment.

### PR 5 — Session ownership pilot

- Specify owner-token propagation and entity-transfer rules.
- Pilot for daemon continuation/cancellation paths.
- Test greenback, nested/child processes, helper tasks, concurrent processes, pending ORM mutations, cancellation, and cleanup.
- Do not switch all storage contexts until the pilot shows safe lifecycle semantics.

### PR 6 — Conditional persistence and commit reconciliation

- Add operation/version IDs for selected process persistence operations.
- Implement complete owned-transaction retry and ambiguous-commit reconciliation.
- Test commit success with dropped acknowledgment and stale-generation writes.
- Keep database state changes and notifications ordered consistently.

### PR 7 — Deferred task settlement and distributed ownership

- Add explicit deferred storage failure semantics to RabbitMQ and ZeroMQ.
- Add bounded outage backoff and distributed process claim/fencing.
- Verify exhausted retries do not acknowledge unfinished work or create retry storms.
- Verify old owners cannot continue durable work after losing the claim.

### PR 8 — External-action reconciliation

- Add durable intent/result handling for scheduler actions first.
- Preserve existing job-ID replay guards; reconcile unknown submissions where backend capabilities allow.
- Extend individually to cancellation, upload, retrieval, and stash.
- Define plugin contract for safe retries; leave undeclared actions non-retryable.
- Provide recovery-required reporting/resolution for ambiguous external outcomes.

## Test matrix and acceptance gates

Every applicable stage should test:

- stale pooled connection replaced before use;
- SAVEPOINT failure during continuation preparation;
- expired ORM field SELECT failure during cancellation;
- connection loss during flush;
- transaction commit succeeds but acknowledgment is lost;
- rollback/close fails;
- another process has pending or flushed/uncommitted changes;
- two processes run concurrently in one worker;
- greenback/helper-task ownership propagation;
- scheduler accepts submission but persistence fails;
- cancellation during retry/backoff;
- retry exhaustion and broker settlement under RabbitMQ and ZeroMQ;
- shutdown while storage is unavailable; and
- ordinary SQL errors are not misclassified as disconnects.

Acceptance invariants:

1. No database error handler closes, commits, or rolls back unrelated process work.
2. No operation is retried unless its full attempt is owned and its replay safety is documented.
3. External actions are never blindly repeated after an unknown outcome.
4. Unfinished tasks are not acknowledged as successful or converted to application failure solely because storage is temporarily unavailable.
5. Original exceptions remain visible even when DB logging or cleanup fails.
6. Persistent outages terminate retries within a defined budget and produce actionable, sanitized diagnostics.

## Rollout and compatibility

1. Develop and test in an isolated worktree based on v2.9.4 / upstream `support/2.9.x`; preserve unrelated local modifications.
2. Run disposable local PostgreSQL tests, including real backend termination and deterministic fault injection.
3. Validate on a dedicated HPC test profile with proxy/network maintainers where possible.
4. Roll out to a limited workload and monitor EOF classification, retry success/exhaustion, session errors, pending delivery behavior, and duplicate external actions.
5. Keep this work on the 2.9.x support line. Do not move it to current `main` without separately resolving checkpoint compatibility and the v3 migration.

## Effort estimate

These are planning estimates, not commitments:

- Fault injection, diagnostics, logging/shutdown hardening, and pool settings: **about 1–2 weeks**.
- Owned reads and continuation retry/session pilot: **about 2–4 additional weeks**.
- Conditional persistence, broker deferral/fencing, and external-action reconciliation: **about 4–8+ additional weeks**, depending on maintainer feedback and scheduler capabilities.

The first useful milestone is: **an EOF during continuation preparation recovers without losing the task or detaching another live process, and error reporting does not further poison the worker.**
