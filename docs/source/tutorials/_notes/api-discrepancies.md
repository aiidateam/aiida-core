# AiiDA-Core vs AiiDA-WorkGraph: API Discrepancies for Tutorial Writing

## Summary

This document catalogues the differences between aiida-core's native workflow
system (calcfunction, WorkChain) and aiida-workgraph that are relevant for
writing tutorial text. Each entry notes **which module(s)** the discrepancy
surfaces in, its **criticality**, and what (if anything) we need to address.

> **Context**: There is an open PR to aiida-core that enables `engine.run()` /
> `engine.submit()` for WorkGraph instances, which unifies the run/submit API.
> There is also a PR (#7196) to support `verdi process dump` for WorkGraphs.

---

## Resolved / non-issues

These were initially flagged as potential problems but turn out to work already.

### ~~Decorator interop~~ — works today

A bare `@calcfunction` **can** be passed directly to `wg.add_task()`.
WorkGraph's `build_task_from_callable()` detects the `node_class` attribute
that `@calcfunction` adds and auto-wraps it as a task. Confirmed by
`tests/test_build_task.py::test_calcfunction` in the workgraph repo.

**Tutorial impact**: Users can define `@calcfunction` in Module 1 and reuse it
in Module 4 (WorkGraph) without any changes. No friction.

### ~~Auto-serialization~~ — works in aiida-core too

aiida-core's `@calcfunction` already registers `to_aiida_type` as a serializer
on every input port (`functions.py:404`). Plain Python types are auto-converted:

```python
@calcfunction
def add(x, y):
    return x + y

result = add(5, 3)  # plain ints — works, auto-serialized to orm.Int
```

Supported: `int` → `orm.Int`, `float` → `orm.Float`, `str` → `orm.Str`,
`dict` → `orm.Dict`, `list` → `orm.List`, `bool` → `orm.Bool`.

**Tutorial impact**: We can use plain Python types from Module 1 onward if we
choose. The wrapping with `orm.Dict(params)` is only needed when storing data
nodes explicitly (outside a process). Needs a clear note.

### ~~verdi commands~~ — work for WorkGraph

`WorkGraphNode` subclasses `WorkChainNode`, so all standard `verdi process`
commands work via inheritance:

- ✅ `verdi process list`
- ✅ `verdi process show`
- ✅ `verdi process status`
- ✅ `verdi process report` (uses WorkChain code path via isinstance)
- ⚠️ `verdi process dump` — needs PR #7196

WorkGraph also has its own task-level CLI (`workgraph task pause/play/kill/list`)
for fine-grained control.

---

## Must be unified (PRs needed/open)

### 1. Run/submit API

| Current state | Target |
|---|---|
| WorkChain: `engine.run(MyWorkChain, **inputs)` | Same |
| WorkGraph: `wg.run()` / `wg.submit()` (instance methods) | `engine.run(wg)` / `engine.submit(wg)` |

**PR status**: Open — enables `engine.run()` / `engine.submit()` for WorkGraph.

**Criticality**: High. This is the single most visible API difference for users.
Every tutorial example that runs a workflow will use one of these.

**Where it appears**: Module 4 (WorkGraph), Module 6 (parameter sweeps),
Module 7 (WorkChain). With the PR merged, all three use the same pattern.

### 2. Process dump for WorkGraphs

`verdi process dump` currently does not support WorkGraph processes.

**PR status**: #7196 open.

**Criticality**: Medium. Not a teaching blocker, but `verdi process dump` is
shown in Module 3 and expected to work on any process type.

---

## Acceptable differences (workflow authoring — expected to differ)

These are the *raison d'être* of WorkGraph. Different syntax is fine — the
tutorial should present them as two approaches to the same goal.

### 3. Declarative graph vs imperative outline

**WorkGraph** — declarative:
```python
wg = WorkGraph('my_workflow')
t1 = wg.add_task(calculate, x=input_value)
t2 = wg.add_task(analyze, data=t1.outputs.result)
```

**WorkChain** — imperative:
```python
class MyWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.outline(cls.step1, cls.step2)

    def step1(self):
        future = self.submit(SomeCalc, x=self.inputs.x)
        self.to_context(calc=future)

    def step2(self):
        self.out('result', self.ctx.calc.outputs.result)
```

**Where it appears**: Module 4 (WorkGraph) vs Module 7 (WorkChain).

**Tutorial approach**: Present WorkGraph first (Module 4) as the recommended
modern approach. Frame WorkChain (Module 7) as the traditional/advanced
alternative. Side-by-side comparison in Module 7.

### 4. Error handler registration

| WorkChain (BaseRestartWorkChain) | WorkGraph |
|---|---|
| `@process_handler(priority=100, exit_codes=[...])` | `ErrorHandlerSpec(exit_codes=[...], max_retries=3)` |
| Handler is a **method** on the class | Handler is an **external function** |
| Signature: `def handle(self, node)` | Signature: `def handle(task, **kwargs)` |
| Returns `ProcessHandlerReport` | Modifies task state directly |
| Handlers auto-discovered on the class | Handlers passed explicitly in decorator |

**Where it appears**: Module 5 (error handling).

**Decision needed**: Teach WorkGraph error handlers in Module 5 (simpler API),
WorkChain error handlers in Module 7? Or both in Module 5?

### 5. Conditional logic and loops

| WorkChain | WorkGraph |
|---|---|
| `if_(cls.check)(cls.step)` in outline | `If` / `While` zone tasks |
| `while_(cls.check)(cls.step)` | `Map` context manager for sweeps |
| Conditions are methods returning bool | Conditions are task outputs |

**Where it appears**: Module 6 (parameter sweeps with `Map`),
Module 7 (WorkChain `while_()` for restarts).

### 6. Nesting / sub-workflows

| WorkChain | WorkGraph |
|---|---|
| `self.submit(ChildWorkChain, **inputs)` | `@task.graph()` decorator |
| Explicit child process submission | Sub-graphs are composed like tasks |

**Where it appears**: Module 4 (if multi-step), Module 7.

---

## Module-by-module impact summary

| Module | Discrepancies | Notes |
|---|---|---|
| 1 (Running a simulation) | None | Uses `@calcfunction` only |
| 2 (External codes) | None | Uses `launch_shell_job` only |
| 3 (Working with data) | None | QueryBuilder, Groups |
| 4 (Building workflows) | **1, 3** | First WorkGraph module; run/submit API + declarative wiring |
| 5 (Error handling) | **4** | Error handler API differs |
| 6 (Parameter sweeps) | **5** | `Map` vs `while_()` |
| 7 (Advanced / WorkChain) | **1, 3, 4, 5, 6** | First WorkChain module; compare with WorkGraph |

---

## Open questions for the meeting

1. **Run/submit PR**: Can we assume it's merged by the time the tutorial ships?
   If yes, the biggest discrepancy (item 1) is eliminated.
2. **Error handling module**: WorkGraph-only in Module 5, with WorkChain
   alternative in Module 7? Or both in Module 5?
3. **Side-by-side comparisons**: Do we want explicit "WorkGraph vs WorkChain"
   comparison boxes in Module 7, or keep them as separate narratives?
4. **Auto-serialization in Module 1**: Do we teach `orm.Dict(params)` wrapping
   (explicit, educational) or plain dicts (simpler)? The wrapping is still
   needed for `parameters.store()` outside a process context.
