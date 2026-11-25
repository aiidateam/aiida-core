# Common task — restart wrapper for the flaky child (both arms)

You are implementing a **restart wrapper** around the flaky collaborator
`FlakyChild` (provided as `fixtures/flaky_child.py`, do NOT modify it).

## Collaborator behaviour (fixed)

`FlakyChild` takes inputs `attempt: Int`, `fail_until: Int = 2`,
`fatal: Bool = False` and, per attempt:

- `fatal == True` → finishes with exit code **420** (`ERROR_FATAL`, permanent);
- `attempt <= fail_until` → finishes with exit code **410** (`ERROR_TRANSIENT`);
- otherwise → exit status 0 and exposes `result: Int == attempt * 10`.

It always exposes `next_attempt: Int == attempt + 1`.

## Required wrapper behaviour (black box)

Your wrapper MUST accept inputs `fail_until: Int = 2` and `fatal: Bool = False`,
start the attempt counter at 1, and expose output `result: Int` on success:

1. **Transient failure then success** (`fail_until=2, fatal=False`): retry with
   an incremented attempt counter until the child succeeds. Expect 3 child runs
   and `result == 30`.
2. **Retry cap** (`fail_until=10, fatal=False`): stop after exactly **5** child
   runs (`MAX_ITERATIONS = 5`) and finish **unsuccessfully** (non-zero exit
   status). No 6th run.
3. **Permanent failure** (`fatal=True`): stop after exactly **1** child run and
   finish **unsuccessfully**. Never retry a 420.
4. **Output / provenance validation**: on success, `result` must be the value
   produced by the successful child run (30 for the default case), passed
   through as a linked output — not recomputed or synthesized by the wrapper.
   The child's outputs are stored nodes created by a `calcfunction` and
   RETURN-linked; your wrapper must link those very same nodes (same pk).

## Solution layout (mandatory for automated verification)

- Put your solution in `<scratch>/restart_solution/` as an importable package
  with `restart_solution/__init__.py` exposing:
  - `run_restart(fail_until: int = 2, fatal: bool = False) -> ProcessNode`
    which launches the wrapper with AiiDA-native inputs and returns the
    **wrapper process node** (use `run_get_node`-style launch, in-process —
    no daemon or broker setup may be required of the grader).
- `MAX_ITERATIONS` is 5. Do not change it.
- You may create a scratch AiiDA profile for your own manual checks, but the
  final solution must run under the grader's profile fixtures without extra
  setup.

## Isolation rules (violations invalidate the run)

- Work ONLY inside your scratch directory. You may READ repository sources
  outside the scratch for reference (e.g. `src/aiida/...`,
  `tests/engine/processes/graphs/...`), but NEVER write outside it.
- FORBIDDEN to read, list, glob, or grep: any other `eval-scratch-*`
  directory, any `ARM_*.md` file other than the one in your scratch,
  any `reports/` directory, any `*.jsonl` transcript/metrics/session file,
  any `tests_hidden/` path or file with `hidden`/`verify` in its name.
- FORBIDDEN to inspect git history or other checkouts: no
  `git log/show/diff/blame`, no other worktrees or branches.
- This is a fresh session with no prior conversation. Do NOT attempt to
  discover the hidden acceptance tests.

## Arm-specific rules

See the arm file (`ARM_A_BRWC.md` or `ARM_B_GRAPHIR.md`) for the implementation
method you MUST use. Using the other arm's method disqualifies the run.
Do not copy any existing restart example; write the wrapper yourself.

## Environment

- Work only inside your scratch directory. `uv run` for all Python execution.
- Tools available: `read, bash, edit, write, codemode`.
- Relevant sources: `src/aiida/engine/processes/workchains/restart.py`,
  `src/aiida/engine/processes/graphs/{ir,run,process,tasks}.py`,
  `tests/engine/processes/graphs/programs/{loops,branches,tasks}.py`.
