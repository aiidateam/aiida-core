---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.4
kernelspec:
  display_name: Python 3
  language: python
  name: python3
execution:
  timeout: 300
---

(tutorial:module3)=
# Module 3: Writing simple workflows

<!-- TODO: re-enable once the md->ipynb conversion script is verified
:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module3.ipynb` {octicon}`download`
:::
-->

:::{note}
This module reuses the tutorial profile and the `gsrd_code` object created in {ref}`Module 1 <tutorial:module1>`.
If you are following along locally, run that module first.
To use your own profile instead, replace the setup cell at the top of the downloaded notebook with:

```python
from aiida import load_profile

load_profile()
```
:::

## What you will learn

After this module, you will be able to:

- Build a reusable workflow from your existing calcfunctions and CalcJob
- Connect tasks by passing one task's output socket as another task's input, so the whole pipeline is tracked as a single named process you can query and restart
- Run a workflow over multiple input sets in parallel to replace plain Python `for`-loops with tracked, fan-out execution

```{code-cell} ipython3
# Set up the tutorial's isolated sandbox profile (same as Module 1).
# `%load_ext aiida` enables the `%verdi` magic; `%run` creates or loads the
# shared `tutorial-<hash>` profile, so data from earlier modules is available.
%load_ext aiida
%run -i include/setup_tutorial.py
```

## Why workflows?

In {ref}`Module 2 <tutorial:module2>`, you built a three-step pipeline (`prepare_input` &rarr; `ShellJob` &rarr; `parse_output`) and ran it in a Python `for` loop.
The loop produces results, but AiiDA only ever sees the individual processes inside it; the pipeline itself is invisible.
That leaves several gaps:

- **No single pipeline object**: the data links between `prepare_input`, the `ShellJob`, and `parse_output` are already in the provenance graph (AiiDA chained them automatically as data flowed through). What is missing is a single *workflow node* that owns the three steps as one unit, that you can query, restart, or hand to a colleague as "the pipeline".
- **No CALL hierarchy**: the existing links are data links between siblings. There is no orchestrator above them with `CALL_CALC` links pointing down, so listing "everything that belongs to this run of the pipeline" requires reconstructing the chain by hand from the data links.
- **Sequential by construction**: the Python loop blocks until each iteration finishes, whereas a workflow submitted to the AiiDA daemon can run independent iterations in parallel.
- **No single entry point**: you can't re-run "the same workflow" with different parameters as one operation.

A **workflow** solves all of these.
You define the steps and their connections once, and AiiDA handles execution, data passing, and provenance tracking, with the whole pipeline recorded under a single workflow node.

:::{note}
AiiDA offers two workflow systems.
**WorkChain** (imperative, class-based) is the classical, long-standing API for defining workflows in AiiDA.
**WorkGraph** (declarative, graph-based) was added more recently as a simplified API for composing tasks, and is what this tutorial uses; it is more intuitive for composing tasks and scales naturally to complex graphs.
:::

::::{dropdown} AiiDA core ↔ WorkGraph concept mapping
:icon: table

If you encounter AiiDA core terminology in other documentation or plugins, here is how it maps to the WorkGraph abstractions this tutorial uses:

| AiiDA core concept | WorkGraph equivalent | Notes |
|---|---|---|
| `CalcJob` | `task` wrapping a `CalcJob` | `shelljob()` is a convenience for `ShellJob` CalcJobs |
| `calcfunction` | `@task` / `@task.graph` | `@task` wraps any callable (calcfunctions, plain Python functions, CalcJobs) and turns it into a graph task |
| `WorkChain` | `WorkGraph` | Both are workflow-level process nodes |
| `WorkChain.define()` outline | Graph definition (linking tasks) | WorkGraph replaces the imperative outline with a declarative graph |
| `spec.input` / `spec.output` | Input/output sockets | `spec.input(...)` and `spec.output(...)` in `@task.graph` |
| Process node | Process node | Both systems produce the same provenance nodes |
| `engine.submit(...)` / `engine.run(...)` | `wg.submit()` / `wg.run()` | Identical semantics; ergonomics aside, both hand the process to the daemon (`submit`) or block in-process (`run`) |
| `ToContext` / `self.ctx` | Sockets for data flow, `wg.ctx` for shared state | Most data passes via socket connections (links between tasks). For shared state that does not fit naturally on a socket, WorkGraph exposes a `wg.ctx` analogue covered in {ref}`Module 6 <tutorial:module6>` |

::::

## The WorkGraph mental model

Before we write any code, it helps to have a mental picture of the four main objects WorkGraph is built from:

- **WorkGraph**: the container. A directed graph of tasks that AiiDA runs as a single workflow process. Every WorkGraph run becomes one top-level process node in the provenance graph.
- **Task**: a unit of work inside the graph. Each task wraps an *executor*: a Python function, a `calcfunction`, a `CalcJob`, or even another WorkGraph. Tasks are created by calling task-wrapped functions (like `prepare_input(...)` below) inside a graph context.
- **Socket**: a typed input or output port on a task. When you write `prepare_input(parameters=...).result`, `parameters` is an input socket and `.result` is an output socket.
- **Link**: a directed connection between an output socket of one task and an input socket of another. Links are created automatically when you pass one task's output socket as an argument to another task.

:::{important}
**Building the graph and running the graph are two completely separate steps.**

Inside a WorkGraph definition, calling a task function does not execute it.
It creates a task node in the graph and returns a handle whose attributes are **output sockets**: placeholders for values that don't exist yet.
You are not handling AiiDA `Float` / `Dict` / `SinglefileData` *values* yet; you are handling *sockets*, which the engine will fill in at execution time.

Actual execution only happens later, when you call `wg.run()` (or `wg.submit()`).
That separation is why a comparison like `parsed.variance_V > threshold` produces a new socket (a comparison task) rather than a Python `bool`, and why iterating a socket with a Python `for` or branching on it with a plain `if` does not work the way you might expect.
It is the single most important mental shift when moving from plain Python control flow to WorkGraph.
:::

## Composing the pipeline as a workflow

With the mental model in place, we can assemble the three-step pipeline as a reusable workflow.
The imports below cover everything we will use across this module; each helper is introduced when it first comes up.

```{code-cell} ipython3
from aiida import orm

from aiida_workgraph import Map, WorkGraph, task, shelljob, dynamic, namespace

from include.constants import BASE_PARAMS, F_VALUES
from include.tasks import prepare_input, parse_output
```

We reuse the `prepare_input` and `parse_output` calcfunctions from {ref}`Module 2 <tutorial:module2>` ({download}`include/tasks.py`).
A calcfunction is already an AiiDA process, but to compose it inside a graph we wrap it with `task()`.
The wrapped version adds a task to the current graph when called and returns a handle exposing its input and output sockets, which you can then pass to downstream tasks.

WorkGraph infers a task's sockets directly from the wrapped function's signature:

- **Input sockets** come from the function's positional and keyword arguments. Each argument name becomes an input socket of the same name.
- **Output sockets** come from the return annotation. A single annotated return type produces one output socket (named `.result` by default), while a `TypedDict`, dataclass, or Pydantic model produces one named socket per field.

Concretely:

- `prepare_input(parameters: orm.Dict) -> orm.SinglefileData` exposes one input socket `parameters` and the default output socket `.result`.
- `parse_output(stdout: orm.SinglefileData) -> ParseOutputs` exposes one input socket `stdout` and two output sockets `.variance_V` and `.mean_V` (the keys of the `ParseOutputs` TypedDict).

The default-output convention is the same as for the plain calcfunctions in {ref}`Module 2 <tutorial:module2>`: when a wrapped function returns a single (unnamed) value, WorkGraph exposes it via the `.result` socket on the task handle, mirroring how `node.outputs.result` worked there.
A structured-typed return (TypedDict, dataclass, Pydantic model) creates one named socket per field instead.

`@task()` is a decorator; for functions defined elsewhere (like ours in `include/tasks.py`) we apply it explicitly:

```{code-cell} ipython3
# `*_task` = WorkGraph-wrapped variants; the originals stay usable under
# their plain names. `task()(fn)` is the explicit decorator-application form,
# equivalent to writing `@task()` above the definition.
prepare_input_task = task()(prepare_input)
parse_output_task = task()(parse_output)
```

:::{note}
WorkGraph infers output sockets from the function's return annotation.
When that's a TypedDict (as above), a dataclass, a Pydantic model, or a single AiiDA data type, plain `task(fn)` is enough.
For dynamic-namespace *inputs* (open-ended runtime-keyed dicts), annotate the argument with `Annotated[dict, dynamic(<type>)]`.
For *outputs* that mix fixed and dynamic fields, write the return annotation as `namespace(field_a=<type>, field_b=dynamic(<type>))`. We'll use both patterns further down.
If WorkGraph can't infer the shape at all (e.g., a function you don't control that returns a plain `dict`), pass an explicit spec via `task(outputs=...)`.
:::

With the tasks wrapped, we can write the workflow itself: a Python function decorated with `@task.graph()`.
Its body reads like ordinary Python, but as the callouts above already noted, the calls inside register tasks and links rather than executing right away.
The function signature becomes the graph's inputs and the return statement its outputs.

The canonical definition lives in `include/workflows.py` so later modules (and other notebooks) can import the same pipeline rather than redefining it.
The file declares one extra output socket on top of what we strictly need here, `results_npz`, so Module 6 can read the V-field for follow-on analyses.

```{literalinclude} include/workflows.py
:language: python
:pyobject: gray_scott_pipeline
```

We bring it into the current namespace with a plain import:

```{code-cell} ipython3
from include.workflows import gray_scott_pipeline
```

**Line by line**:

```python
prepared = prepare_input_task(parameters=parameters)
```

Adds the `prepare_input` task to the graph.
The returned handle's attributes are output sockets, references to future values that don't exist as AiiDA nodes until the graph runs.

```python
simulation = shelljob(..., nodes={'input': prepared.result}, ...)
```

Adds a `ShellJob` task.
`prepared.result` is the default output socket of `prepare_input` (since it returns a single value); passing a socket as one of the `nodes` automatically creates the link `prepared.result` &rarr; `simulation.nodes.input` in the graph.

```python
parsed = parse_output_task(stdout=simulation.stdout)
```

Adds the `parse_output` task.
`simulation.stdout` is the ShellJob's auto-captured stdout socket; that is where `gsrd` prints the headline scalars our parser regexes out.

```python
return {
    'variance_V': parsed.variance_V,
    'mean_V': parsed.mean_V,
    'results_npz': simulation.results_npz,
}
```

Wires the named outputs to the graph's own outputs.
`parsed.variance_V` and `parsed.mean_V` are the two scalar diagnostics parsed from stdout; `simulation.results_npz` is the file output declared on the `ShellJob` (`outputs=['results.npz']`), kept around so later modules can read the V and U fields directly.

Before running anything, it helps to convince yourself that the function body above really is just a *specification*.
`.build(...)` returns a `WorkGraph` object whose tasks and sockets we can inspect without running any simulation:

```{code-cell} ipython3
wg_preview = gray_scott_pipeline.build(
    parameters=orm.Dict(BASE_PARAMS),
    command=gsrd_code,
)

print('Graph inputs (bound from .build()):')
for name in wg_preview.inputs._get_keys():
    if name == 'metadata':
        continue
    bound = getattr(wg_preview.inputs, name).value
    print(f'  - {name:<11} = {bound.__class__.__name__}')

print('\nGraph outputs:')
for name in wg_preview.outputs._get_keys():
    print(f'  - {name}')

print('\nTasks in the graph:')
for t in wg_preview.tasks:
    print(f'  - {t.name:<20} ({t.task_type})')
```

Two things to notice:

- Task inputs accept **both plain Python values and sockets**. Above we passed `parameters` (a wrapped `Dict`), `command` (a real `InstalledCode` node), and `prepared.result` (a socket from the `prepare_input` task, wired through the `nodes` dict of the `shelljob` call). For socket arguments WorkGraph creates a link from the producing task to this one; for plain values it stores them directly as the task's input data. The graph definition does not care which kind you pass; only at execution time does the engine resolve sockets to the values flowing through them.
- The task list includes a handful of **built-ins** that WorkGraph adds to every graph: `graph_inputs` and `graph_outputs` expose the graph's own I/O as pseudo-tasks so that links into and out of the graph look like ordinary task-to-task links, and `graph_ctx` is a shared key-value store (the WorkGraph analogue of the WorkChain `ctx`) reachable via `wg.ctx.foo`, covered in {ref}`Module 6 <tutorial:module6>`.

WorkGraph also exposes the same structure as an **interactive graph viewer**. Click around the nodes to see the sockets and links; the flow is `graph_inputs` &rarr; `prepare_input` &rarr; `ShellJob` &rarr; `parse_output` &rarr; `graph_outputs`.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg_preview
```

So, `gray_scott_pipeline` is now a **factory**: call `.build(...)` to get a standalone `WorkGraph` you can `run()` or `submit()` directly, or call it inside a parent graph to embed it as a sub-task.
For now, let's exercise the standalone form: build the workflow with a single set of parameters and run it.

```{code-cell} ipython3
wg = gray_scott_pipeline.build(
    parameters=orm.Dict(BASE_PARAMS),
    command=gsrd_code,
)
```

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg.run()
```

Expanding the cell above shows the workflow's progress log and, at the very end, a dict of the resolved output values: `variance_V`, `mean_V`, and `results_npz` as concrete `Float` / `SinglefileData` nodes, the return value of `wg.run()`.

`wg` itself stays a Python-side container around the graph definition. The actual AiiDA process node that records the execution lives on `wg.process` and is a `WorkGraphNode` (a subclass of `WorkChainNode`, so anything that works on a WorkChain process node works on this one too):

```{code-cell} ipython3
print(f"wg.process type: {type(wg.process).__name__}")
print(f"WorkGraph PK:    {wg.process.pk}")
print(f"State:           {wg.state}")
```

The three steps are now bundled under that single workflow node.
Let's inspect the hierarchy:

```{code-cell} ipython3

# Show the hierarchical process tree of the workflow.
%verdi process status {wg.process.pk}
```

We can again use the familiar `verdi process show` command here to get a full overview of the workflow.
It shows the individual steps as well as the graph-level inputs and outputs we declared (folded by default since the table is long):

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi process show {wg.process.pk}
```

Each child step still has its own identity as an AiiDA process node.
You can drill down to it directly and see its `caller` link pointing back to the workflow.
For example, the inner `ShellJob`:

```{code-cell} ipython3
# Pick the ShellJob child of the workflow.
shelljob_node = next(c for c in wg.process.called if isinstance(c, orm.CalcJobNode))

print(f'ShellJob PK:    {shelljob_node.pk}')
print(f'process_label:  {shelljob_node.process_label}')
print(f'caller PK:      {shelljob_node.caller.pk}  ({type(shelljob_node.caller).__name__})')
```

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi process show {shelljob_node.pk}
```

And the same hierarchy visualised as a provenance graph:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
# Visualize the hierarchical provenance graph of the workflow.
from include.plotting import plot_provenance

plot_provenance(wg.process)
```

Compare this to Module 2's flat provenance: the three process nodes are the same (`prepare_input`, the `ShellJob`, `parse_output`), but they are now *children* of a `WorkGraph<gray_scott_pipeline>` orchestrator node.
The orchestrator owns `CALL_CALC` links pointing to each child step and `RETURN` links back from the exposed outputs, so the **whole pipeline is one queryable, inspectable unit in the database**.

## Integrating the for-loop into the workflow

In Module 2, the parameter sweep was a Python `for` loop calling the pipeline for each `F` value.
But a `for` loop is not an AiiDA process: it doesn't show up in the provenance, can't be inspected with `verdi`, and can't recover from failures.

WorkGraph's {class}`~aiida_workgraph.Map` lets you run the same sub-workflow over multiple input values, like a parallel `for` loop, but as a single AiiDA workflow with full provenance.
In WorkGraph terminology, a `Map` is a **zone**: a region of the graph that controls how the tasks inside it are scheduled.

:::{important}
Conceptually, a `Map` zone does three things:

1. It takes a **source collection** of the form `{key: value}` and runs the tasks inside the zone once per entry.
2. Inside the zone, it exposes the current key/value via `map_zone.item.key` and `map_zone.item.value`. These are sockets, so you can wire them into tasks just like any other output.
3. At the end of the zone, `map_zone.gather({...})` declares which per-iteration outputs to collect. The gathered outputs become accessible on `map_zone.outputs.<name>` as a namespace keyed by the original source keys.
:::

`Map` is imported alongside the rest of the WorkGraph helpers; its signature and docstring are visible via `help(Map)`:

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show `Map` signature and docstring'
:    code_prompt_hide: 'Hide signature'

help(Map)
```

To close the loop, we add a final **reduction step** to the workflow: a calcfunction `make_transition_plot` ({download}`include/tasks.py`) that takes the gathered `variance_V` `Float` nodes and renders the transition curve as a `SinglefileData` PNG.
The workflow's primary output is then that single artifact: the per-iteration variances "fork out" via `Map`, and the plotting task "joins" them back together.

:::{tip}
The sweep is wrapped as a `@task.graph()` with two inputs: `param_sweep` and the `Code` to run on.
The blueprint is parameter-agnostic: change the contents of `param_sweep` and you can scan a different parameter (or several at once) without touching the workflow.
:::

The signature of `gray_scott_sweep` uses two helpers from the WorkGraph type system (both already imported at the top of this module):

- `dynamic(dict)` on the input tells WorkGraph that `param_sweep` is a dict whose keys are not known until runtime. Each value is itself a dict (the parameter set for one iteration).
- `namespace(...)` on the return type declares multiple named outputs. Some are fixed (`transition_plot`), others are `dynamic(float)`, meaning the engine will create one output per Map iteration under that name.

```{code-cell} ipython3
from typing import Annotated

from include.tasks import make_transition_plot


@task.graph()
def gray_scott_sweep(
    param_sweep: Annotated[dict, dynamic(dict)],
    command: orm.AbstractCode,
) -> namespace(
    transition_plot=orm.SinglefileData,
    variance_V=dynamic(float),
    mean_V=dynamic(float),
):
    """Sweep gray_scott_pipeline over param_sweep and reduce to a transition plot."""
    with Map(param_sweep) as map_zone:
        result = gray_scott_pipeline(
            parameters=map_zone.item.value,
            command=command,
        )
        map_zone.gather({
            'variance_V': result.variance_V,
            'mean_V': result.mean_V,
        })

    plotted = make_transition_plot(variances=map_zone.outputs.variance_V)

    return {
        'transition_plot': plotted.result,
        'variance_V': map_zone.outputs.variance_V,
        'mean_V': map_zone.outputs.mean_V,
    }
```

:::{important}
A few things to keep in mind about `Map`:

- The source must be a mapping (a `dict` or a socket of a dynamic namespace). Iterating over a plain list is not supported directly. Wrap it into a dict first, using meaningful keys like `F_0_040` rather than integer indices, because those keys will show up in the provenance graph and as the names of the gathered outputs. **Avoid dots in keys**: WorkGraph treats dots as namespace separators, which will silently collapse your entries.
- `map_zone.item.value` is the value for the current iteration, `map_zone.item.key` is its key. Both are sockets, so you can pass them as task inputs, but you cannot use them as ordinary Python values inside the graph function (no `if` on them, no string concatenation).
- After the `with` block, `map_zone.outputs.<name>` gives you a namespace that behaves like a dict of AiiDA nodes, keyed by the original source keys.
:::

That's the blueprint; no execution yet.
We need a `param_sweep` dict with one entry per iteration.
The folded cell below constructs it; the visible cell prints what's about to flow in:

```{code-cell} ipython3
:tags: ["hide-cell"]

# {label: parameters} for Map to iterate over. Keys become the names of
# each map iteration in the provenance graph.
param_sweep = {}
for f_val in F_VALUES:
    key = f'F_{f_val:.3f}'.replace('.', '_')  # WorkGraph treats `.` as namespace separator, so use `_`
    param_sweep[key] = BASE_PARAMS | {'F': f_val}
```

```{code-cell} ipython3
# Show what's flowing into the Map.
print(f'{len(param_sweep)} parameter sets (only F varies):')
for key, val in param_sweep.items():
    print(f'  {key:<10}  ->  F = {val["F"]}')
```

Now `.build(...)` with concrete inputs:

```{code-cell} ipython3
wg_sweep = gray_scott_sweep.build(
    param_sweep=param_sweep,
    command=gsrd_code,
)
```

The sweep graph contains the same `gray_scott_pipeline` sub-graph as before, now wrapped in a single `map_zone`. Even though we are about to run `gsrd` many times, the **build-time graph stays compact**: `Map` declares "run these tasks once per item in `param_sweep`", but the engine only creates the per-iteration sub-workflows when the graph actually runs.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg_sweep
```

`.run()` to launch the sweep:

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg_sweep.run()
```

:::{note}
We called `.run()`, which blocks your Python session until the whole graph has finished.
The alternative, `.submit()`, hands the workflow to the AiiDA daemon and returns immediately, freeing your session while the daemon drives execution in the background.
In both cases the sub-workflows inside the `Map` zone run concurrently (the engine schedules them as independent processes); the only difference is whether *your session* waits for the result or not.
For a tutorial `.run()` is convenient because the outputs are available right away.
:::

The per-iteration variances are now reachable directly on the workflow's outputs:

```{code-cell} ipython3
# Access per-iteration variances via the workflow output namespace.
# `._value` unwraps the namespace into a plain dict; this is the current
# WorkGraph API for accessing gathered outputs (may become public in future).
variances = wg_sweep.outputs.variance_V._value

for key in sorted(variances):
    print(f"  {key}: variance(V) = {float(variances[key].value):.4e}")
```

The numbers are the same as Module 2's sweep (same simulation, same parameters).
What changed is the *shape* of the provenance: instead of a long flat list of disconnected processes, the sweep is one workflow node that fans out into per-`F` sub-workflows and fans back in through `make_transition_plot`:

```{code-cell} ipython3
print(f"Sweep WorkGraph PK: {wg_sweep.process.pk}")
%verdi process status {wg_sweep.process.pk}
```

🔭 Time to bring out the binoculars.
Here's the same hierarchy rendered as a provenance graph:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
plot_provenance(wg_sweep.process)
```

It's deliberately busy: every input, output, and linked sub-process is represented.
The point is not to read it in detail (you can't, it's tiny in the rendered docs) but to see how rich the provenance becomes *for free* as workflows nest.
For a zoomable view, right-click the image and open it in a new tab, or run `verdi node graph generate <PK>` from the command line to get a standalone SVG.

And finally, the workflow's *real* output: the transition curve PNG produced by the reduction step inside the workflow itself, loaded from the database via its process node:

```{code-cell} ipython3
from IPython.display import Image

# Load the transition plot from the stored process node, not the live Python object.
sweep_node = orm.load_node(wg_sweep.process.pk)
with sweep_node.outputs.transition_plot.open(mode='rb') as fh:
    img_bytes = fh.read()

Image(img_bytes)
```

`verdi process show` works on the sweep workflow node too, but its per-node table is long, so its output is folded here:

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi process show {wg_sweep.process.pk}
```

## A 2D scan: feed rate &times; kill rate

So far the sweep has varied only `F`. The classic Gray-Scott phase diagram is two-dimensional, though: the pattern type depends on both the feed rate `F` and the kill rate `k`.
The point of wrapping the sweep as a `@task.graph()` was that it is parameter-agnostic; we can scan a 2D grid by changing nothing but the contents of `param_sweep`.

We use a 5&times;5 grid that straddles the **boundary** of the pattern-forming region.
Inside the band, `variance(V)` is of order `1e-2`; near the edge it drops by an order of magnitude as the V field starts decaying toward a trivial steady state.
The grid is chosen so that every (F, k) combination still produces a `results.npz` file; points that land fully outside the band cause `gsrd` to skip the output file entirely, which would make the `ShellJob` fail for those iterations.

```{code-cell} ipython3
F_GRID = [0.040, 0.045, 0.050, 0.055, 0.060]
K_GRID = [0.061, 0.062, 0.063, 0.064, 0.065]

param_sweep_2d = {}
for f in F_GRID:
    for k in K_GRID:
        # Map keys must be valid identifiers (letters, digits, underscores
        # only); encode both 'F = 0.040' and 'k = 0.060' as `F_0_040_k_0_060`.
        f_key = f'F_{f:.3f}'.replace('.', '_')
        k_key = f'k_{k:.3f}'.replace('.', '_')
        key = f'{f_key}_{k_key}'
        param_sweep_2d[key] = {**BASE_PARAMS, 'F': f, 'k': k}

print(f'{len(param_sweep_2d)} parameter sets ({len(F_GRID)} F values x {len(K_GRID)} k values)')
```

The same `gray_scott_sweep` graph drives both the 1D and 2D scans; only the input dict changes.
The `make_transition_plot` reduction still runs and produces its 1D transition curve, but for the 2D case we use the gathered `variance_V` outputs directly and reshape them into a 5&times;5 matrix for the heatmap.

```{code-cell} ipython3
wg_2d = gray_scott_sweep.build(
    param_sweep=param_sweep_2d,
    command=gsrd_code,
)
```

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg_2d
```

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg_2d.run()
```

Render the gathered variances as a heatmap. The plotting helper lives in {download}`include/plotting.py`; it does the bookkeeping (map keys back to `(F, k)`, floor non-positive entries for the log-norm, build the figure) so the cell stays a one-liner:

```{code-cell} ipython3
from include.plotting import plot_2d_variance_heatmap

plot_2d_variance_heatmap(
    variances=wg_2d.outputs.variance_V._value,
    param_sweep=param_sweep_2d,
    f_grid=F_GRID,
    k_grid=K_GRID,
)
```

The heatmap shows the edge of the **pattern-forming region** of the classic Gray-Scott phase diagram. High-variance cells (bright) develop the spots, stripes, and labyrinths the system is famous for; toward the upper-right corner, `variance(V)` drops by an order of magnitude as the V field begins decaying toward a trivial steady state.
Twenty-five simulations, one workflow node, full provenance attached.

## Next steps

You now have the core building blocks: tracked external codes, structured data, calcfunctions, and reusable workflows.
The remaining modules can be tackled in whatever order matches your needs, since they each pick up an independent thread:

- {ref}`Module 4 <tutorial:module4>`: running on remote HPC clusters
- {ref}`Module 5 <tutorial:module5>`: querying the database with the `QueryBuilder`
- {ref}`Module 6 <tutorial:module6>`: more advanced workflow patterns (conditionals, dynamic graphs, sub-workflow composition)
- {ref}`Module 7 <tutorial:module7>`: handling failures and recovering from them

## Further reading

- AiiDA's workflow concepts in depth: {ref}`topics:workflows`
- CalcJob concept (for `ShellJob` background): {ref}`topics:calculations:concepts:calcjobs`
- Calcfunctions refresher: {ref}`topics:processes:functions`
- Control flow (`If`, `While`, dynamic graph construction): {ref}`Module 6 <tutorial:module6>`
- WorkGraph imperative form (`with WorkGraph() as wg:`) and `spec` helpers: [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io)
- Running versus submitting processes: {ref}`topics:processes:usage:launching`
- The AiiDA daemon (architecture and management): {ref}`topics:daemon`, {ref}`how-to:manage-daemon`
