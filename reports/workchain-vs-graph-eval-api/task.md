# Bounded adaptive relaxation workflow

Implement a small but realistic iterative scientific workflow: repeatedly submit a trial child workflow until an integer state reaches a target, or the trial budget runs out, then select success/failure postprocessing. Use real AiiDA processes and preserve provenance.

## Fixed collaborators and interface

Read `tests/engine/processes/workflow_eval/collaborators.py`. The provided `TrialWorkChain` takes `value`, `target`, `stride` (all Int) and returns `value` (Int), moving towards target by at most stride. `FinalizeWorkChain` takes `value`, `target`, `attempts` (Int), `mode` (Str) and returns `result` (Dict). Do not modify these collaborators.

Create `tests/engine/processes/workflow_eval/solution.py` exporting `workflow` (the runnable process/graph), with inputs named `initial`, `target`, `max_steps`, `fast`. Valid inputs are arbitrary integer initial/target, a nonnegative integer max_steps and a boolean fast. No validation of invalid inputs is required. A regular WorkChain may use Int/Bool ports, while a graph may use primitive annotations. Both are launched with `run_get_node(workflow, initial=Int(...), target=Int(...), max_steps=Int(...), fast=Bool(...))`.

1. Select stride 2 for fast=True, otherwise stride 1, in the root orchestration.
2. Start from initial, attempts=0. If already at target, submit no trials.
3. While state != target and attempts < max_steps, submit exactly one TrialWorkChain, wait for it, use its returned value as the next state, increment attempts. Never overshoot, never run extra trials.
4. After the loop, branch in root orchestration: mode='square' if converged, mode='unfinished' otherwise.
5. Submit exactly one FinalizeWorkChain with final state, target, attempts and selected mode. Publish its existing Dict under root output `result`; do not create or copy that result in the root.
6. Exhaustion is a normal finished-ok workflow, with a report saying converged=False. Do not invent a failure exit status for it. Assume provided children succeed.

The report contains exactly value, target, attempts, converged, mode, score. FinalizeWorkChain computes score=value**2 for square mode, otherwise -1.

## Deliverables and constraints

- Implement only the assigned orchestration style below. Do not place the orchestration in a task, calcfunction, collaborator, external function, workfunction, or a second hidden WorkChain.
- All numeric scientific updates happen in TrialWorkChain, not in the root. Root counters, comparisons, and branches are orchestration state, not scientific calculation nodes.
- Add your own focused tests in `tests/engine/processes/workflow_eval/test_solution.py`, including convergence, exhaustion, initially converged, descending/negative values, both fast settings, and returned-node identity/provenance.
- Do not modify existing source, shared collaborators, acceptance tests, or infrastructure to make your solution pass.
- Use `uv run --no-sync pytest --broker-backend=none -q tests/engine/processes/workflow_eval` (environment is already installed). Use uv run for all Python/tool commands.
- Inspect source/docs as needed. Do not read any other workspace, previous reports, session histories, or other agent output; remain within this workspace. You start with a fresh session, no prior conversation. Do not delegate or launch another agent.
- Finish with a concise description of implementation, exact test command/results, and any blockers. Time limit: 15 minutes.
