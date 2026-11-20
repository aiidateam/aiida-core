# Implementation, delegation and verification

Implementation was delegated to the `worker` subagent in a clean dedicated Git worktree. A second fresh worker performed independent review without editing implementation. The parent independently ran tests, integrated the commits, reconciled the existing worktree edits, and ran the new paired evaluation.

## Separate commits on the requested branch

| Commit | Feature |
|---|---|
| ee1409281 | Scalar constant bindings as typed finite, checkpointed inline control values. |
| 38b4a2183 | Iteration-local bindings distinct from initialized loop-carried state. |
| 1342bbdfe | Typed, lazy short-circuit and/or via existing branch scopes. |
| 5287d3985 | Lazy conditional expressions; only the selected task/expression arm executes. |
| e9a0b717a | Prevent nested boolean combinations from reusing a generated wire alias. |
| 4d6baacc1 | Presence/member predicates as boolean values, including RHS operands, negation and direct while conditions. |

Each feature includes tests and documentation, plus an Unreleased breaking-change note for changed acceptance/rejection behavior. The alias correction is a separate small correctness commit. The feature worker's original commit IDs differ because the parent cherry-picked the clean commits into the requested branch.

## Preserved restrictions

No arbitrary Python execution/eval, side effects, arbitrary identity comparisons, dynamic indexing/comprehensions/formatting or general string arithmetic. Boolean operands must have boolean contracts, operations/constants must remain finite and serializable, and unselected branches/RHS tasks must not execute. Inline values remain ephemeral control state without Data nodes or CREATE links; root scientific results still require existing nodes with valid provenance. Zero-iteration loops cannot leak undefined locals, and each iteration has fresh local scope across checkpoint restores.

## Tests and review

- Independent parent verification of the initial four-feature branch: 850 graph tests passed.
- Worker verification after predicate composition follow-up: 912 graph tests passed in its clean worktree.
- Independent integrated verification, including the user's additional local graph examples: **937 passed**, 6 existing warnings, in 109.85 seconds. Command: `uv run --no-sync pytest --broker-backend=none -m presto -n 4 tests/engine/processes/graphs -q`; full output in graph-suite.log.
- `uv run --no-sync pre-commit run --files $(git diff --name-only d67ea7ac9..HEAD)` passes on the integrated changes; full output in pre-commit.log.
- Coverage includes real child execution, skipped-branch/task absence, guarded failing operations, strict type rejection, nonfinite constants/Data smuggling rejection, JSON IR roundtrips, zero/one/many iterations, local read-before-write/post-loop rejection, checkpoint restore and output node identity/creator checks.
- Independent review found no high-severity correctness/provenance bug. It identified generated alias reuse (fixed in e9a0b717a) and the predicate RHS asymmetry (removed in 4d6baacc1). Direct constant root returns fail at build; indirect computed scalar returns remain protected at the process output boundary. Uniform early diagnostics would be a separate improvement.

## Existing worktree edits

The original worktree had eight modified tracked files plus unrelated untracked reports/examples. Before integration these tracked edits were backed up as a binary patch and a named Git stash. They were reapplied after feature cherry-picks; the overlapping documentation conflict was resolved to keep both sets of examples. Stale claims that and/or or scalar bindings were unsupported were reconciled with the new behavior. Those prior edits remain uncommitted rather than being silently included in feature commits. The named backup stash is retained, not dropped; the original patch remains at /tmp/aiida-graph-authoring-preexisting.patch.
