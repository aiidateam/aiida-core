# Arm A — implement with `BaseRestartWorkChain` ONLY

Follow `TASK_COMMON.md`. Additionally you MUST:

- Subclass `aiida.engine.BaseRestartWorkChain` as `RestartWrapper` with
  `_process_class = FlakyChild`.
- Define your own outline in `define` (the base ships none) driving bounded
  retries through the standard restart phases, leaving the retry limit at its
  default (`MAX_ITERATIONS = 5`).
- Retry the transient failure (exit code 410) with a real `@process_handler`
  method (using `ProcessHandlerReport`); leave the permanent failure (exit
  code 420) unhandled so it aborts without retry.
- Expose the child's outputs through your wrapper so the successful child's
  `result` is passed through as your `result` output (same node, not
  recomputed or synthesized).
- Do NOT use `GraphIR`, `@graph`, `GraphProcess`, or any
  `aiida.engine.processes.graphs` API in your solution.

`restart_solution/__init__.py` must expose `run_restart(...)` returning the
wrapper node.
