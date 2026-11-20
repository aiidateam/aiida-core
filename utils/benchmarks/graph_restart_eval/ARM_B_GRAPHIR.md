# Arm B — implement with direct `GraphIR` construction ONLY

Follow `TASK_COMMON.md`. Additionally you MUST:

- Build the restart loop by constructing `GraphIR` **directly** with the IR
  task types (`ProcessTask` referencing `FlakyChild`, `LoopControl` with
  `condition_port` and `max_iterations=5`, and branch/control tasks as
  needed). Your module must contain a `build_restart_graph() -> GraphIR`
  function returning the declaration.
- The retry decision must be driven by the child's declared failure
  (exit 410, mapped via `errors=`/`Result` failure contracts — see
  `src/aiida/engine/processes/graphs/{tasks,results,run}.py`) or by a
  task-computed boolean condition; exit 420 must terminate the graph without
  further retries.
- Launch via the repository's standard GraphIR launch path
  (e.g. `run_get_node(declaration_or_GraphProcess, **inputs)` as used in
  `tests/engine/processes/graphs/test_graphs.py`).
- Do NOT use the `@graph` decorator sugar for the restart loop itself, and do
  NOT use `BaseRestartWorkChain`, `process_handler`, or
  `ProcessHandlerReport` anywhere in your solution. Plain `@task`
  calcfunctions as loop helpers are allowed.

`restart_solution/__init__.py` must expose `build_restart_graph()` and
`run_restart(...)` (returning the graph wrapper node).
