# PostgreSQL Disconnect Resilience Checklist

Track progress against [`plan.md`](plan.md). Check items only when verified; record test commands/results and links to PRs in the relevant phase notes.

## Preparation

- [ ] Preserve existing local changes; develop in an isolated worktree.
- [ ] Confirm upstream `support/2.9.x` remains based on the v2.9.4 tag for this work.
- [ ] Confirm disposable PostgreSQL and test-profile setup.
- [ ] Review `postgres-tls-eof-investigation.md` and map report frames to v2.9.3/2.9.4 source.
- [ ] Agree initial scope and recovery semantics with aiida-core maintainers.

## PR 1 — Fault-injection tests and diagnostics

- [ ] Capture baseline SAVEPOINT/continuation failure.
- [ ] Capture expired-field SELECT/cancellation failure.
- [ ] Test disconnect classification and `connection_invalidated`.
- [ ] Add deterministic fault injection for SAVEPOINT, SELECT, flush, commit, rollback, and close.
- [ ] Test two processes and pending shared-session changes.
- [ ] Test dropped commit acknowledgment / ambiguous outcome.
- [ ] Sanitize diagnostics and avoid ORM logging in failure paths.

## PR 2 — Logging and shutdown hardening

- [ ] Prevent DB log-handler failures from masking original exceptions.
- [ ] Add non-recursive file/stderr fallback logging.
- [ ] Continue independent cleanup after rollback/close errors.
- [ ] Test cancellation and shutdown with unavailable PostgreSQL.
- [ ] Preserve cleanup errors without claiming they caused shutdown.

## PR 3 — Pool checkout resilience

- [ ] Add supported and validated `pool_pre_ping` configuration.
- [ ] Decide whether pre-ping is opt-in or default; measure overhead.
- [ ] Document pre-ping/recycle benefits and in-flight failure limitations.
- [ ] Test replacement of a stale idle connection.

## PR 4 — Owned reads and continuation preparation

- [ ] Implement fresh-session materialized-value read path.
- [ ] Cover all DB preparation needed before process reconstruction.
- [ ] Add bounded retry for classified disconnects only.
- [ ] Confirm retry ends before process execution and reconstruction happens once.
- [ ] Confirm another live process and its pending changes remain usable.
- [ ] Specify retry-exhaustion broker settlement before release.

## PR 5 — Session ownership pilot

- [ ] Define owner-token/session lifecycle and entity-transfer rules.
- [ ] Test greenback and async callback propagation.
- [ ] Test nested/child processes and helper tasks.
- [ ] Test cancellation/RPC access to the correct owner.
- [ ] Test CLI, REST, notebook, and synchronous execution compatibility.
- [ ] Verify no cross-owner detached or stale ORM objects are reused.

## PR 6 — Conditional persistence and commit reconciliation

- [ ] Identify first persistence operations suitable for owned complete-transaction retry.
- [ ] Add stable operation/version IDs and conditional updates.
- [ ] Reconcile already-committed operations after lost acknowledgment.
- [ ] Test stale generation cannot overwrite newer process state.
- [ ] Verify notifications occur only after durable state changes.

## PR 7 — Deferred settlement and distributed ownership

- [ ] Define deferred-storage outcome for RabbitMQ and ZeroMQ.
- [ ] Add bounded backoff without requeue hot loops.
- [ ] Ensure exhausted retry does not acknowledge unfinished work.
- [ ] Add process claim/generation/fencing semantics.
- [ ] Test worker loss, redelivery, and stale-owner rejection.
- [ ] Cover background `nowait` process execution.

## PR 8 — External-action reconciliation

- [ ] Scheduler: persist intent before submission.
- [ ] Scheduler: preserve job ID and retry persistence without resubmitting.
- [ ] Scheduler: reconcile unknown submission outcomes by stable token where supported.
- [ ] Surface ambiguous unsupported outcomes as recovery-required.
- [ ] Add cancellation reconciliation and account for job-ID reuse.
- [ ] Validate upload/retrieval partial-transfer and duplicate-output handling.
- [ ] Define stashing/destructive action reconciliation.
- [ ] Define plugin opt-in contract for idempotent/reconcilable operations.

## Release and rollout

- [ ] Run tests on an isolated v2.9.x worktree.
- [ ] Run disposable PostgreSQL fault-injection suite.
- [ ] Run multi-worker RabbitMQ and ZeroMQ tests.
- [ ] Validate on a dedicated HPC test profile.
- [ ] Add documentation and accurate `Unreleased` changelog entries.
- [ ] Keep the contribution on the 2.9.x support branch; do not merge it into v3 `main` without a separate port/review.
- [ ] Roll out to limited workloads and monitor retry/exhaustion/duplicate metrics.
- [ ] Document operator response for recovery-required cases.
