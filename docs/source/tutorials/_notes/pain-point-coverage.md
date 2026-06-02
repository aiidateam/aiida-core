# Module 0 pain-point coverage across modules 1–4

Development-only audit. Does every pain point raised in Module 0 get paid off in a later (written) module? Modules 5–7 are "coming soon", so anything deferred there is currently an unpaid promise.

Status legend: ✅ resolved & demonstrated · 🟡 partial / conceptual only · ❌ raised in M0, no payoff in written modules.

## Small-scale pain points (demonstrated firsthand in M0)

| # | M0 pain point | Where resolved | Status |
|---|---------------|----------------|--------|
| 1 | Inputs disconnected from outputs | M1: provenance graph links input.yaml → ShellJob → outputs | ✅ |
| 2 | Results scattered across stdout + `results.npz` (scalars only on stdout) | M1 captures stdout as a node (manual regex); M2 `parse_output` turns stdout → `Float` nodes | ✅ |
| 3 | Hardcoded output filename → silent overwrite | M1: each run is a separate immutable node; nothing overwrites | ✅ |
| 4 | Implicit working-dir restart (leftover files change results) | M1: AiiDA gives each calc its own isolated working dir — resolves it, but never explicitly called back | 🟡 (resolved, not narrated) |
| 5 | Input parameters not stored with output | M1 stores input.yaml; M2 stores `Dict` of params | ✅ |
| 6 | Editing input in place loses original params | M1/M2: every run keeps its own stored inputs | ✅ |
| 7 | No systematic record / organization of runs | M1 provenance gives traceability; explicit **Groups** still a TODO in M2 | 🟡 |
| 8 | Tolerant input parsers silently accept wrong keys | M2: note after `prepare_input` — structured `Dict` centralizes inputs; forward-pointer to real CalcJob plugins validating via process-spec ports | ✅ (note + forward-pointer) |
| 9 | Failures hard to detect (exit 0, terse stderr, no JOB DONE) | M1 "Handling failures" is an **unwritten TODO**; M7 is coming soon | ❌ |
| 10 | Failed runs leave no trace / no output file | same as #9 — failure story not yet written | ❌ |
| 11 | No `--help` / discoverability (positional arg, PDF manual) | not an AiiDA-resolvable pain; pure color | 🟡 (intentionally unpaid) |

## Scale pain points ("even worse at real-world scale" list)

| # | M0 pain point | Where resolved | Status |
|---|---------------|----------------|--------|
| 12 | Scattered data across clusters/filesystems | M4: remote Computer, `remote_folder`, `gotocomputer`, AiiDA owns the dirs | ✅ |
| 13 | Multi-step: which of 100 failed, why, re-run just those | M3 Map groups the sweep into one workflow node; the *failure-recovery* half is M7 (coming soon) | 🟡 |
| 14 | Unstructured output formats → fragile parsers | M2 `parse_output` as a tracked parsing step | ✅ |
| 15 | Code versions & environments | M4 registers Code + `prepend-text` (module load); no real version capture demoed | 🟡 |
| 16 | Post-processing at scale (one number from N files) | M2 QueryBuilder examples; full querying is M5 (coming soon) | 🟡 |
| 17 | Collaboration & handover (archive) | M1 `verdi process dump` (partial); AiiDA **archive** is M5 (coming soon) | 🟡 |

## The 5 "How AiiDA solves these problems" promises (end of M0)

| Promise | Payoff | Status |
|---------|--------|--------|
| Provenance tracking | M1 | ✅ |
| Workflow orchestration | M3 | ✅ |
| Structured output parsing | M2 | ✅ |
| Reproducibility & sharing (archive) | M5 (coming soon) | ❌ unpaid in written modules |
| Community knowledge (plugins) | conceptual; aiida-shell shown, no domain plugin | 🟡 |

## Headline gaps (raised loudly in M0, no payoff yet)

1. **Failures (#9, #10).** M0 dedicates an entire "Running into errors" section to exit-code-0 + no-trace failures. M1's "Handling failures" section is still a `<!-- TODO -->`; M7 is coming soon. Right now the single most-emphasized M0 pain point is unresolved everywhere. **Highest priority** — and it's already on the M1 TODO list.
2. ~~**Tolerant input parsers (#8).**~~ *Resolved 2026-05-22.* Added a 2-sentence note after `prepare_input` in M2: structured `Dict` centralizes inputs (vs. hand-edited YAML with silently-ignored typos), honest that `Dict` itself doesn't validate, forward-pointer to CalcJob plugin process-spec validation.
3. **Archive / reproducibility-sharing.** Promised in M0's solution list; deferred to M5 (planned: `.aiida` archives). `verdi process dump` (M1) only partially covers handover. Acceptable since M5 is flagged coming soon.

## Easy wins
- **#4 implicit restart**: AiiDA already resolves it (isolated per-calc working dirs). One callback sentence in M1's "What just happened?" would convert 🟡 → ✅.
- **#7 Groups**: already a TODO in M2; lands the "organization" half of the record-keeping pain.
