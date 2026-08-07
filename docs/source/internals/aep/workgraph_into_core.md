# Move the WorkGraph engine and framework into aiida-core

| | |
|---|---|
| **AEP number** | to be assigned |
| **Authors** | Julian Geiger ([@GeigerJ2](https://github.com/GeigerJ2)) |
| **Status** | draft |
| **Type** | Standard |
| **Created** | 2026-08-06 |
| **Targets** | AiiDA v3 ([#7406](https://github.com/aiidateam/aiida-core/issues/7406)) |
| **Discussion** | [#7479](https://github.com/aiidateam/aiida-core/issues/7479), [#7533](https://github.com/aiidateam/aiida-core/pull/7533) |

## Scope

Bringing aiida-core's workflow ecosystem in-house splits into **three independent tracks**, each its own AEP:

1. **WorkGraph engine + framework → core** (this AEP): the native DAG workflow model on a shared `Workflow` process base, the shared serializer foundation it uses, and the entry points, so aiida-workgraph becomes an archivable shim.
2. **aiida-shell + aiida-pythonjob → core**: `ShellJob` and `PythonJob`/`PyFunction` as first-class CalcJobs in `aiida/calculations/`, consuming track 1's serializer.
3. **node-graph → core**: vendor the generic graph / task / socket spec as ABCs, then archive the package.

This AEP covers **track 1**. The dependencies between tracks: track 1 keeps node-graph as an external hard dependency (the way it depends on plumpy) until track 3 vendors it in, and it lands the serializer foundation (`general_serializer`, the datetime / function data types, the deserializer) that track 2 builds on. Landing the whole serializer in track 1 keeps core's serialize/deserialize stack in one place and lets aiida-pythonjob drop its copy immediately, even though only `general_serializer` + `serialize_ports` are exercised by the WorkGraph engine itself.

Further, later work (each its own design): the optional **semantic / knowledge-graph layer** (`[semantics]` extra, node-graph's `knowledge` module, part of track 3) and a pluggable **execution-backend ABC**.

## Motivation

- **One source of truth.** aiida-workgraph and its satellites reimplement things core already has: their own `JsonableData`, a `builtin_serializers` table duplicating `to_aiida_type`, `PickledData`, `NoneData`, their own graph engine. node-graph was in fact *extracted out of* aiida-workgraph (same author, one month apart in 2023) and never fully separated, so much of the cross-package duplication is unfinished-extraction residue rather than a designed boundary.
- **A package that cannot be built on the public API is already core in practice.** WorkGraph is the only package (of ~40 audited in [#7410](https://github.com/aiidateam/aiida-core/issues/7410)) that reaches into engine / daemon / config internals no third-party plugin uses.
- **Keep the recommended authoring API in core**, not in a separate external package (not even under `aiidateam`), and drop the dependency-inversion gymnastics the split forces (registry / entry-point indirection so core never imports downstream).
- **Raise code quality:** fold loosely-gated plugin code under core's strict mypy + test bar.

Guiding principle throughout: *generalize / extend aiida-core and drop the plugins' hand-written duplicates.* Backwards-compatible extension (additive accessors, more-permissive validation) is preferred; since this targets v3, incompatible changes are acceptable where genuinely required.

## Why a graph engine belongs in core

Core's only execution model is the plumpy **outline stepper**: a lexically-ordered sequence, static and sealed at first instantiation (grepping `topological` / `networkx` / DAG across `aiida/` turns up only SQLAlchemy's `declarative_base`). It expresses neither data-dependency scheduling nor sub-step concurrency, which is what a research workflow usually wants.

```python
# WorkChain: the outline is a chain of hard barriers.
spec.outline(cls.submit_a, cls.submit_b, cls.combine)
# submit_b runs only after EVERY child launched in submit_a has finished.

# WorkGraph: each task wakes when its own inputs are ready; siblings stream.
wg = WorkGraph()
a = wg.add_task(calc, x=1)
b = wg.add_task(calc, x=a.outputs.result)   # starts the moment `a` is done
wg.run()
```

Concretely, the outline stepper cannot:

- **Order by data dependency** (outline order is lexical; nothing declares "B consumes A's output").
- **Run sub-steps concurrently** (the core gap): `_do_step` clears awaitables at every step boundary and resumes only when *all* are done. WorkGraph wakes each task on its own deps.
- **Map / fan-out at runtime** (`Map`/`GatherItem`); outline vocabulary is only `while_`/`if_`/`return_`.
- **Mutate the graph mid-run**, or run **parameterised steps that return data** (an outline step takes only `self`; data flows through untyped `self.ctx`).
- **Treat the workflow as data**: WorkGraph stores the whole graph on the node and rebuilds it on restore (inspect, diff, restart-with-modification, GUI). A WorkChain checkpoint only restores a position in an outline rebuilt from the class.

## The enabling refactor: a shared `Workflow` base

WorkGraph was an external fork because `WorkChain` hard-binds execution to the outline stepper and seals `run`/`on_run`/`to_context`/`on_exiting`/`on_wait` with `@Protect.final`. Swapping the scheduler meant going around `WorkChain` and re-copying its awaitable/context/checkpoint machinery, and that copy is the root of the duplication.

The fix extracts the shared machinery into a new `Workflow(Process)` base; `WorkChain` and `WorkGraphProcess` become siblings, each supplying only its own stepper.

```{mermaid}
classDiagram
    Process <|-- CalcJob
    Process <|-- FunctionProcess
    Process <|-- Workflow
    Workflow <|-- WorkChain
    Workflow <|-- WorkGraphProcess
    note for Workflow "stepper seam + awaitables + ctx + step lifecycle"
    note for WorkChain "outline stepper"
    note for WorkGraphProcess "DagStepper (streams; awaitable_barrier=False)"
```

```python
class Workflow(Process, metaclass=Protect):
    """Shared base: stepper seam, awaitable-based waiting, ctx, step lifecycle + checkpointing."""
    def _create_stepper(self) -> Stepper:   # abstract: the subclass picks the strategy
        raise NotImplementedError

class WorkChain(Workflow):                   # walks a static outline
    def _create_stepper(self):
        return self.spec().get_outline().create_stepper(self)

class WorkGraphProcess(Workflow):            # schedules by data dependencies
    def _create_stepper(self):
        return DagStepper(self)              # sets awaitable_barrier = False to stream
```

- The `_create_stepper`/`_recreate_stepper` seam is abstract and left overridable, unlike the `@Protect.final` lifecycle methods around it.
- The awaitable-clearing barrier belongs to the stepping strategy, so it lives on the base and reads from the stepper: `awaitable_barrier = False` streams (launch when a task's inputs are terminal, resume on the *first* child to finish); the outline default barriers. WorkChain carries no WorkGraph concept. A falsification-checked test guards it: flip the flag and a ready task waits for its slow sibling, so the test fails.
- WorkGraph's copied `AwaitableManager` + `ContextManager` are deleted; both siblings use the base's.
- The extraction also fixes `Protect`: it now scans each base's full MRO, so a `@final` method reached through an intermediate class (e.g. `run`, now on `Workflow`) stays protected.

The first prototype had `WorkGraphProcess` subclass `WorkChain`; review ([#7479](https://github.com/aiidateam/aiida-core/issues/7479)) flagged that it bolts WorkGraph's barrier policy onto `WorkChain` and couples the two execution models, hence the sibling split.

Two boundaries the refactor keeps deliberate:

- **`TaskState` stays its own enum.** It tracks a DAG slot (`PLANNED`/`SKIPPED`/`MAPPED`, states a task may hold without ever becoming a process); `ProcessState` is the lifecycle of one live process. The overlapping names (`RUNNING`, ...) roll up a child's real state.
- **No `CalculationProcess` base** for symmetry with `CalculationNode`. A base is introduced only where there is shared implementation. `CalcJob` and a calcfunction share almost none, and one `FunctionProcess` already backs both `@calcfunction` (a `CalculationNode`) and `@workfunction` (a `WorkflowNode`), differing only in `_node_class`. The calculation/workflow split stays enforced on the nodes and in the engine's link rules.

`TaskState`'s members make the first boundary concrete:

```python
class TaskState(str, Enum):    # a DAG slot, separate from plumpy's ProcessState
    PLANNED = 'PLANNED'        # a task may sit here and never become a live
    READY = 'READY'           # process; PLANNED / SKIPPED / MAPPED have no
    CREATED = 'CREATED'       # ProcessState analogue
    RUNNING = 'RUNNING'       # RUNNING / FINISHED / FAILED share the name but
    FINISHED = 'FINISHED'     # only roll up the child process's real state
    FAILED = 'FAILED'
    SKIPPED = 'SKIPPED'
    MAPPED = 'MAPPED'
```

## Serialization onto core's machinery

The moved serializer is rebuilt on core, so no `JsonableData`/`to_aiida_type` copy is carried:

- `general_serializer` (`aiida/orm/nodes/data/serializer.py`) dispatches value types through core's `to_aiida_type`, foreign types through an `aiida.data` entry-point registry, and JSON-able fallbacks to `JsonableData`; `serialize_to_aiida_nodes` maps it over a dict. Core's `to_aiida_type` already subsumes the plugin's `builtin_serializers` table (the scalars, list, dict, numpy, enum, `None`), so no value-type mapping is copied. The registry is lazy/cached; custom serializers come from a `serializers=` argument (the `pythonjob.json` config is dropped).
- New core data nodes `DateTimeData` and `FunctionData`, each registered with `to_aiida_type`; `deserialize_to_raw_python_data` is the inverse. Core's `JsonableData` gains a `.value` alias rather than a duplicate.
- `serialize_ports` (`aiida/workgraph/serialization.py`) walks a node-graph `SocketSpec` and serializes each leaf through `general_serializer`. It sits in the subsystem because it imports node-graph; `aiida.orm` and a plain `import aiida` stay node-graph-free.

```python
from aiida.orm import general_serializer
general_serializer(3.14)                 # Float          via to_aiida_type
general_serializer({'a': [1, 2]})        # Dict           via to_aiida_type
general_serializer(datetime.now())       # DateTimeData   via to_aiida_type
general_serializer(MyDataclass(x=1))     # JsonableData   JSON-able fallback
general_serializer(open('f'))            # ValueError with guidance (no serializer, not JSON-able)
```

`PickledData` stays in the plugins: aiida-shell already registers `core.pickled`, so core claiming it collides until the track-2 fold consolidates both onto one type (with a `cloudpickle` dependency).

## Core imports no plugin

WorkGraph has to recognise plugin processes (`PythonJob`/`ShellJob`/...) as task types. Each plugin process declares a marker and core reads it with `getattr`, so `aiida.workgraph` recognises them while importing no downstream package (GRASP: the process is the information expert). The earlier version imported each plugin class to compare against, which coupled core to its own plugins.

```python
# in the plugin (aiida-pythonjob), one class attribute:
class PythonJob(CalcJob):
    _workgraph_task_type = 'PYTHONJOB'

# in core, importing nothing from the plugins:
def inspect_aiida_component_type(executor):
    declared = getattr(executor, '_workgraph_task_type', None)
    return declared or _core_fallback(executor)   # CalcJob / WorkChain / process function
```

## Where things land

Layered, batteries-included-but-extensible, the pattern core already uses for `Data` / `Transport` / `Scheduler` / `StorageBackend`:

| Component | Home | Note |
|---|---|---|
| Graph spec (graph/task/socket/link/registry ABCs) | vendored from node-graph | track 3; external dep for now |
| AiiDA dialect (`Task`/socket subclasses, `WorkGraph` authoring, decorator, registry) | `aiida/workgraph/` | subclass core's spec |
| Execution (`WorkGraphProcess` + `DagStepper`) | `aiida/workgraph/engine/` | sibling of `WorkChain` |
| Serialization (`general_serializer`, deserializer, `serialize_ports`) | `aiida/orm/nodes/data/` + `aiida/workgraph/` | on `to_aiida_type` |
| Data types (`DateTimeData`/`FunctionData`/extended `JsonableData`) | `aiida/orm/nodes/data/` | |
| Calc jobs (`ShellJob`, `PythonJob`/`PyFunction`) | `aiida/calculations/` | track 2 |
| Duplicated scaffolding (zones, `*_pool.py`, forked helpers, dead `validate()` overrides) | delete | replace with imports/thin subclasses |
| Optional extras (semantics/rdflib, viz widget, ASE, cloudpickle) | `[extras]` | keep core lean |

Control-flow constructs (`Map`/`Select`/`SetContext`/...) are each two-part: a declaration and a runtime half. Route both halves together to their homes (declaration to the spec/dialect, semantics to the engine) so a construct is never split across the move.

Two of the scaffolding forks already drifted into real bugs (a lost `ContextVar` isolation in the copied context manager, a bypassed validation adapter), the usual failure mode of copied code and the reason to delete rather than re-fork. The one seam worth preserving is the plumpy `Port` → node-graph `SocketSpec` bridge, the real boundary between the two type systems.

## Alternatives considered

- **Keep WorkGraph a plugin.** Viable once the stepper seam exists, but it leaves the duplication in place and the "cannot be built on the public API" problem unsolved; [#7410](https://github.com/aiidateam/aiida-core/issues/7410) already assumes absorption.
- **Make WorkGraph subclass `WorkChain`** (the first prototype). Rejected: it bolts WorkGraph's barrier policy onto `WorkChain` and couples the two execution models. The shared `Workflow` base keeps them independent.
- **Keep node-graph external, or move it to `aiidateam` without folding** (track 3's question). Rejected: either leaves core's recommended authoring API in a separate package and keeps the dependency-inversion indirection; the genericity that would justify a standalone package never materialised (its one real second consumer, the multi-engine POC, is itself AiiDA-fused).

## Roadmap

Track 1, leaves-first; each a reviewable slice, no boil-the-ocean branch.

1. Extract `Workflow(Process)`; re-parent `WorkChain`.
2. `WorkGraphProcess(Workflow)` + `DagStepper`, sibling of `WorkChain`; drop the copied managers.
3. The serializer foundation (`general_serializer`, datetime / function data, deserializer, `serialize_ports`) onto `to_aiida_type`/`JsonableData`; repoint aiida-pythonjob and the engine.
4. Relocate the WorkGraph subsystem into `aiida/workgraph/`; marker-based task detection; entry points in core.
5. AiiDA `Task` base + sockets subclass core's own spec; de-pluginise the `Task.__call__` guard.
6. Reduce aiida-workgraph to a shim, then archive.

Steps 1 to 4 are landing now (see Implementation status). The engine may instead go to `aiida/engine/processes/workgraphs/` mirroring `workchains/`, a relocation either way.

The other two tracks are separate AEPs. **Track 2:** fold `ShellJob`, then `PythonJob`/`PyFunction`, into `aiida/calculations/` (resolve the `core.pickled`/`cloudpickle` collision, `ase` behind an extra); archive both plugins. **Track 3:** vendor node-graph's spec into core as ABCs, move the `Map`/`Select`/ctx control-flow constructs into it, add the `[semantics]` extra, archive node-graph.

## Governance and record

- **Author on board.** node-graph's / aiida-workgraph's author approved consuming the scinode repos into core. He has since left the team, but the team is in direct contact with him, so there is no handover concern. Confirm no external dependents on node-graph before archiving.
- **Prior record:** the v3 public/private-API AEP [#7410](https://github.com/aiidateam/aiida-core/issues/7410) already states WorkGraph is "slated to move into core"; the v3 parent [#7406](https://github.com/aiidateam/aiida-core/issues/7406) invites AEP sub-issues and has none on workflows; the shell capability has a standing request [#5287](https://github.com/aiidateam/aiida-core/issues/5287).
- **`process_type` data break** (cumulative, from ORM entry-point + class-path moves) is kept soft by [#7386](https://github.com/aiidateam/aiida-core/issues/7386) (unknown types fall back to `ProcessNode`); note once in v3 release notes.
- **On a standalone aiida-workgraph 1.0:** it mostly buys a backwards-compat obligation for a package meant to dissolve; prefer targeting core v3 directly.

## Open questions

- node-graph external users: confirm none depend on it as a standalone SDK before archiving.
- Release cadence: folding couples shell/pythonjob/node-graph to core's slower cadence.
- Extras policy: `ase`, `cloudpickle`/`PickledData`, `rdflib`/semantics, the widget.
- Control-flow ownership: which layer defines `If`/`While`/`Map` and their meaning (interacts with aiida-workgraph [#601](https://github.com/aiidateam/aiida-workgraph/issues/601)).
- Core API gaps the fork exposed, each a small core PR: no public `deserialize_safe`; no supported process-control RPC / extensible `Intent`; no per-plugin mutable-state slot on `ProcessNode`; private `instantiate_process`; hardcoded `WorkChainNode` logger name.

## Implementation status

Landing in PR [#7533](https://github.com/aiidateam/aiida-core/pull/7533) (`refactor/workgraph-into-core`), targeting v3, as a chain of self-contained, individually-verified commits (leaves-first, so each reviews on its own):

1. `general_serializer` / `serialize_to_aiida_nodes` on `to_aiida_type` + `JsonableData` (the generic serializer, no copied value-type table).
2. node-graph as a hard dependency + `serialize_ports` over `SocketSpec` (its node-graph-coupled half, kept out of `aiida.orm`).
3. `DateTimeData` / `FunctionData` + `deserialize_to_raw_python_data` (the data nodes and the inverse).
4. `JsonableData.value` alias (a backwards-compatible accessor, so aiida-pythonjob can repoint at core's `JsonableData`).
5. pre-commit / mypy / ruff exemptions for `aiida/workgraph/` (pure tooling, so the relocation commit stays code-only).
6. extract `Workflow(Process)`, re-parent `WorkChain`, fix `Protect`'s MRO scan (core-only; WorkChain behaviour unchanged).
7. lift-and-shift the subsystem into `aiida/workgraph/` (49 modules as one unit, imports repointed, no logic change).
8. `WorkGraphProcess(Workflow)`, sibling of `WorkChain` (drops the inherit-WorkChain coupling review flagged).
9. rename the base to `Workflow`, relocate it to `aiida/engine/processes/workflow.py`.
10. marker-based task detection (core imports no plugin).
11. entry points registered in core.

Why the split: the serializer reconcile (1 to 4) lands and tests bottom-up before anything consumes it; the tooling prep (5) is isolated so the big move is code-only; the enabling `Workflow` refactor (6) carries zero WorkGraph code, so it reads as a pure aiida-core change against WorkChain's own suite; the relocation (7) is mechanical with no behaviour change; re-parenting (8), naming (9), dependency inversion (10) and registration (11) each move exactly one thing. Every non-docs commit is verified against the WorkGraph suite at 181 passed / 11 pre-existing environmental failures, zero regressions.

After (11), aiida-workgraph is a forwarding shim, archivable:

```python
# aiida_workgraph/__init__.py, the whole package after the move
import aiida.workgraph as _core
from aiida.workgraph import *     # forward every symbol
task = _core.task                 # rebind the decorator past the `task` submodule
# entry points now register `aiida.workgraph.*`, so nothing here needs to exist
```

node-graph is still a hard dependency (not yet vendored).
