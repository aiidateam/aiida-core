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
  timeout: 120
---

(tutorial:module3)=
# Module 3: Writing simple workflows

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module3.ipynb` {octicon}`download`
:::

:::{note}
This module reuses the tutorial profile and the `python_code` object created in {ref}`Module 1 <tutorial:module1>`. If you are following along locally, run that module first. To use your own profile instead, replace the setup cell at the top of the downloaded notebook with:

```python
from aiida import load_profile

load_profile()
```
:::

## What you will learn

After this module, you will be able to:

- Build a reusable workflow from your existing calcfunctions and CalcJob
- Wire tasks together via data flow and track the whole pipeline as a single named process you can query and restart
- Map a workflow over a set of parameters to replace `for`-loops with tracked sweeps

```{code-cell} ipython3
:tags: ["remove-cell"]

# Auto-generated tutorial profile for docs build.
# If running locally with your own profile (e.g. from ``verdi presto``),
# replace this cell with:
#
#     from aiida import load_profile
#     load_profile()

%load_ext aiida
%run -i include/setup_tutorial.py
```

## Why workflows?

In {ref}`Module 2 <tutorial:module2>`, you built a three-step pipeline (`prepare_input` &rarr; `ShellJob` &rarr; `parse_output`) and ran it in a Python `for` loop.
The loop produces results, but AiiDA only ever sees the individual processes inside it; the pipeline itself is invisible.
That leaves several gaps:

- **No grouping**: each step is a separate process in AiiDA, with no single "simulation pipeline" object
- **No hierarchy**: the provenance graph is flat; you can't tell which steps belong together
- **Sequential by construction**: the Python loop blocks until each iteration finishes, whereas a workflow submitted to the AiiDA daemon can run independent iterations in parallel
- **No single entry point**: you can't re-run "the same workflow" with different parameters

A **workflow** solves all of these.
You define the steps and their connections once, and AiiDA handles execution, data passing, and provenance tracking, grouping everything under a single workflow node.

:::{note}
AiiDA offers two workflow systems. **WorkChain** (imperative, class-based) is the classical, long-standing API for defining workflows in AiiDA. **WorkGraph** (declarative, graph-based) was added more recently as a simplified API for composing tasks, and is what this tutorial uses; it is more intuitive for composing tasks and scales naturally to complex graphs.
:::

<!-- TODO: Add a comparison table between AiiDA core concepts and WorkGraph concepts:
     CalcJob / WorkChain ↔ WorkGraph task / graph, process nodes, etc.
     From meeting notes: "comparison table between core and WG, make analogous". -->

## The WorkGraph mental model

Before we write any code, it helps to have a mental picture of the four objects WorkGraph is built from:

- **WorkGraph**: the container. A directed graph of tasks that AiiDA runs as a single workflow process. Every WorkGraph run becomes one top-level process node in the provenance graph.
- **Task**: a unit of work inside the graph. Each task wraps an *executor*: a Python function, a `calcfunction`, a `CalcJob`, or even another WorkGraph. Tasks are created by calling task-wrapped functions (like `prepare_input(...)` below) inside a graph context.
- **Socket**: a typed input or output port on a task. When you write `prepare_input(parameters=...).result`, `parameters` is an input socket and `.result` is an output socket.
- **Link**: a directed connection between an output socket of one task and an input socket of another. Links are created automatically when you pass one task's output socket as an argument to another task.

:::{important}
Inside a WorkGraph definition, **calling a task function does not execute it**.
It creates a task node in the graph and returns a handle whose attributes are output sockets, references to future values. The actual execution only happens when you call `wg.run()` (or `wg.submit()`).
This is the single most important mental shift when moving from plain Python loops to WorkGraph.
:::

## Composing the pipeline as a workflow

With the mental model in place, we can assemble the three-step pipeline as a reusable workflow. We will use three more WorkGraph building blocks as we go:

- `@task.graph()`: a decorator that turns a Python function into a reusable graph task (a `WorkGraph` blueprint).
- `shelljob(...)`: the WorkGraph equivalent of `launch_shell_job` from {ref}`Module 1 <tutorial:module1>`; adds a `ShellJob` to the current graph.
- `dynamic(...)`: marks a socket as an *open-ended* namespace whose keys are determined at runtime (used later for the parameter sweep).

```{code-cell} ipython3
from aiida import orm

from aiida_workgraph import Map, WorkGraph, task, shelljob, dynamic, namespace

from include.constants import BASE_PARAMS, F_VALUES, SCRIPT_PATH
from include.tasks import ParseOutputs, prepare_input, parse_output
```

We reuse the `prepare_input` and `parse_output` calcfunctions from {ref}`Module 2 <tutorial:module2>` ({download}`include/tasks.py`). A calcfunction is already an AiiDA process, but to compose it inside a graph we wrap it with `task()`. The wrapped version adds a task to the current graph when called and returns a handle exposing its input and output sockets, which you can then pass to downstream tasks.

WorkGraph infers the output sockets from each function's return annotation:

- `prepare_input` returns a single `orm.SinglefileData`, so its output is wrapped under the default socket name `.result`.
- `parse_output` is annotated with the `ParseOutputs` TypedDict, so WorkGraph reads each key as its own named output socket (we'll access them below as `.variance_V` and `.mean_V`).

:::{important}
**The default output socket is named `.result`.** When a wrapped function returns a single (unnamed) value, WorkGraph exposes it via the `.result` attribute on the task handle. When the return is a structured type (TypedDict, dataclass, Pydantic model), each named field becomes its own attribute instead (e.g., `parsed.variance_V`). This is how you wire one task's output into another's input throughout a graph.
:::

In both cases the plain `task(fn)` form is enough:

```{code-cell} ipython3
# `*_task` = WorkGraph-wrapped variants; the originals stay usable under
# their plain names.
prepare_input_task = task(prepare_input)
parse_output_task = task(parse_output)

# Wrap once so all Map iterations of the sweep share this input node.
script_node = orm.SinglefileData(SCRIPT_PATH)
```

`shelljob` accepts a `Path`, `str`, or pre-wrapped `SinglefileData` in `nodes={...}` and auto-wraps the first two into a `SinglefileData` at execution time. We pre-wrap the script once here so that, when the pipeline is later run many times in a parameter sweep, all those iterations share a single `script` input node instead of producing N near-identical `SinglefileData` nodes in the provenance graph.

:::{note}
WorkGraph infers output sockets from the function's return annotation. When that's a TypedDict (as above), a dataclass, a Pydantic model, or a single AiiDA data type, plain `task(fn)` is enough. For dynamic-namespace *inputs* (open-ended runtime-keyed dicts), annotate the argument with `Annotated[dict, dynamic(<type>)]`. For *outputs* that mix fixed and dynamic fields, write the return annotation as `namespace(field_a=<type>, field_b=dynamic(<type>))` — we'll use both patterns further down. If WorkGraph can't infer the shape at all (e.g., a function you don't control that returns a plain `dict`), pass an explicit spec via `task(outputs=...)`.
:::

With the tasks wrapped, we can write the workflow itself: a Python function decorated with `@task.graph()`. Its body reads like ordinary Python, but as the callouts above warned, the calls inside register tasks and links rather than executing right away. The function signature becomes the graph's inputs and the return statement its outputs.

```{code-cell} ipython3

@task.graph()
def gray_scott_pipeline(
    parameters: orm.Dict,
    command: orm.AbstractCode,
    script: orm.SinglefileData,
) -> ParseOutputs:
    """Prepare input, run simulation, parse output."""
    prepared = prepare_input_task(parameters=parameters)
    simulation = shelljob(
        command=command,
        arguments=['{script}', '--input', '{input}', '--output', 'results.yaml'],
        nodes={'script': script, 'input': prepared.result},
        outputs=['results.yaml'],
    )
    parsed = parse_output_task(output_file=simulation.results_yaml)
    return {'variance_V': parsed.variance_V, 'mean_V': parsed.mean_V}
```

**Line by line**:

```python
prepared = prepare_input_task(parameters=parameters)
```

Adds the `prepare_input` task to the graph. The returned handle's attributes are output sockets, references to future values that don't exist as AiiDA nodes until the graph runs.

```python
simulation = shelljob(..., nodes={'script': script, 'input': prepared.result}, ...)
```

Adds a `ShellJob` task. `prepared.result` is the default output socket of `prepare_input` (since it returns a single value); passing a socket as one of the `nodes` automatically creates the link `prepared.result` &rarr; `simulation.nodes.input` in the graph.

```python
parsed = parse_output_task(output_file=simulation.results_yaml)
```

Adds the `parse_output` task. `simulation.results_yaml` is the ShellJob's output socket for the `results.yaml` file we declared in `outputs=`.

```python
return {'variance_V': parsed.variance_V, 'mean_V': parsed.mean_V}
```

Wires the two named outputs of `parse_output` to the graph's own outputs (`parsed.variance_V` &rarr; the graph's `variance_V`, same for `mean_V`).

Before running anything, it helps to convince yourself that the function body above really is just a *specification*. `.build(...)` returns a `WorkGraph` object whose tasks and sockets we can inspect without running any simulation:

```{code-cell} ipython3
wg_preview = gray_scott_pipeline.build(
    parameters=orm.Dict(BASE_PARAMS),
    command=python_code,
    script=script_node,
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

Three things to notice:

- The **return type annotation** `-> ParseOutputs` is what makes `variance_V` and `mean_V` appear as graph outputs. WorkGraph reads the TypedDict's keys and turns them into named output sockets.
- Task inputs accept **both plain Python values and sockets**. Above we passed `parameters` (an input socket), `script` (a real `SinglefileData` node), and `input_file` (a socket from `prepare_input_task`). WorkGraph treats them uniformly and creates links wherever a socket is passed.
- The first three tasks (`graph_inputs`, `graph_outputs`, `graph_ctx`) are **built-ins** WorkGraph adds to every graph: the first two expose the graph's own I/O as pseudo-tasks so links into/out of the graph look like ordinary task-to-task links; `graph_ctx` is a shared key-value store (the WorkGraph analogue of the WorkChain `ctx`), reachable via `wg.ctx.foo = ...`/`wg.ctx.foo`.

`gray_scott_pipeline` is now a **factory**: call `.build(...)` to get a standalone `WorkGraph` you can `run()` or `submit()` directly, or call it inside a parent graph to embed it as a sub-task. For now, let's exercise the standalone form: build the workflow with a single set of parameters and run it.

```{code-cell} ipython3

wg = gray_scott_pipeline.build(
    parameters=orm.Dict(BASE_PARAMS),
    command=python_code,
    script=script_node,
)
wg.run()

print(f"WorkGraph PK: {wg.process.pk}")
print(f"State: {wg.state}")
```

The three steps are now grouped under a single workflow node.
Let's inspect the hierarchy:

```{code-cell} ipython3

# Show the hierarchical process tree of the workflow.
%verdi process status {wg.process.pk}
```

We can again use the familiar `verdi process show` command here to get a full overview of the workflow. It shows the individual steps as well as the graph-level inputs and outputs we declared (folded by default since the table is long):

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi process show {wg.process.pk}
```

Each child step still has its own identity as an AiiDA process node. You can drill down to it directly and see its `caller` link pointing back to the workflow. For example, the inner `ShellJob`:

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

Compare this to Module 2's flat provenance: the three process nodes are the same (`prepare_input`, the `ShellJob`, `parse_output`), but now they sit *below* a `WorkGraph<gray_scott_pipeline>` orchestrator. The orchestrator has `CALL_CALC` links down to each child step and `RETURN` links back up from the exposed outputs, so the whole pipeline is one queryable, inspectable unit in the database.

## Integrating the for-loop into the workflow

In Module 2, the parameter sweep was a Python `for` loop calling the pipeline for each `F` value. But a `for` loop is not an AiiDA process: it doesn't show up in the provenance, can't be inspected with `verdi`, and can't recover from failures.

WorkGraph's {class}`~aiida_workgraph.Map` lets you run the same sub-workflow over multiple input values, like a parallel `for` loop, but as a single AiiDA workflow with full provenance.

:::{important}
Conceptually, a `Map` zone does three things:

1. It takes a **source collection** of the form `{key: value}` and schedules one copy of its body per entry.
2. Inside the zone, it exposes the current key/value via `map_zone.item.key` and `map_zone.item.value`. These are sockets, so you can wire them into tasks just like any other output.
3. At the end of the zone, `map_zone.gather({...})` declares which per-iteration outputs to collect. The gathered outputs become accessible on `map_zone.outputs.<name>` as a namespace keyed by the original source keys.
:::

To close the loop, we add a final **reduction step** to the workflow: a calcfunction `make_transition_plot` ({download}`include/tasks.py`) that takes the gathered `variance_V` `Float` nodes and renders a transition curve as a `SinglefileData` PNG. The workflow's primary output is then that single artifact: the per-iteration variances "fork out" via `Map`, and the plotting task "joins" them back together.

:::{tip}
The sweep is wrapped as a `@task.graph()` with three inputs: `param_sweep`, the `Code` to run on, and the simulation `script`. The blueprint is parameter-agnostic: change the contents of `param_sweep` and you can scan a different parameter (or several at once) without touching the workflow.
:::

```{code-cell} ipython3
from typing import Annotated

from include.tasks import make_transition_plot


@task.graph()
def gray_scott_sweep(
    param_sweep: Annotated[dict, dynamic(dict)],
    command: orm.AbstractCode,
    script: orm.SinglefileData,
) -> namespace(
    summary_plot=orm.SinglefileData,
    variance_V=dynamic(float),
    mean_V=dynamic(float),
):
    """Sweep gray_scott_pipeline over param_sweep and reduce to a transition plot."""
    with Map(param_sweep) as map_zone:
        result = gray_scott_pipeline(
            parameters=map_zone.item.value,
            command=command,
            script=script,
        )
        map_zone.gather({
            'variance_V': result.variance_V,
            'mean_V': result.mean_V,
        })

    summary = make_transition_plot(variances=map_zone.outputs.variance_V)

    return {
        'summary_plot': summary.result,
        'variance_V': map_zone.outputs.variance_V,
        'mean_V': map_zone.outputs.mean_V,
    }
```

:::{note}
A few things to keep in mind about `Map`:

- The source must be a mapping (a `dict` or a socket of a dynamic namespace). Iterating over a plain list is not supported directly. Wrap it into a dict first, using meaningful keys like `F_0_040` rather than integer indices, because those keys will show up in the provenance graph and as the names of the gathered outputs. **Avoid dots in keys**: WorkGraph treats dots as namespace separators, which will silently collapse your entries.
- `map_zone.item.value` is the value for the current iteration, `map_zone.item.key` is its key. Both are sockets, so you can pass them as task inputs, but you cannot use them as ordinary Python values inside the graph function (no `if` on them, no string concatenation).
- After the `with` block, `map_zone.outputs.<name>` gives you a namespace that behaves like a dict of AiiDA nodes, keyed by the original source keys.
:::

That's the blueprint; no execution yet. We need a `param_sweep` dict with one entry per iteration. The hidden cell below constructs it; the visible cell prints what's about to flow in:

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

Now `.build(...)` with concrete inputs and `.run()` to actually launch the sweep:

```{code-cell} ipython3
:tags: ["hide-output"]

wg_sweep = gray_scott_sweep.build(
    param_sweep=param_sweep,
    command=python_code,
    script=script_node,
)
wg_sweep.run()
```

The per-iteration variances are now reachable directly on the workflow's outputs:

```{code-cell} ipython3
# Access per-iteration variances via the workflow output namespace.
variances = wg_sweep.outputs.variance_V._value

for key in sorted(variances):
    print(f"  {key}: variance(V) = {float(variances[key].value):.4e}")
```

The numbers are the same as Module 2's sweep (same simulation, same parameters). What changed is the *shape* of the provenance: instead of a long flat list of disconnected processes, the sweep is one workflow node that fans out into per-`F` sub-workflows and fans back in through `make_transition_plot`:

```{code-cell} ipython3
print(f"Sweep WorkGraph PK: {wg_sweep.process.pk}")
%verdi process status {wg_sweep.process.pk}
```

Time to bring out the binoculars. Here's the same hierarchy rendered as a provenance graph:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
plot_provenance(wg_sweep.process)
```

It's deliberately busy: every input, output, and linked sub-process is represented. The point is not to read it in detail (you can't, it's tiny in the rendered docs) but to see how rich the provenance becomes *for free* as workflows nest. For a zoomable view, run `verdi node graph generate <PK>` from the command line.

And finally, the workflow's *real* output: the transition curve PNG produced by the reduction step inside the workflow itself, recovered from the database the same way you would recover any other `SinglefileData`:

```{code-cell} ipython3
# TODO: WorkGraph output-socket dereference for SinglefileData currently
# returns None via `.value`. Disabled until the right access path is settled.
#
# from IPython.display import Image
#
# with wg_sweep.outputs.summary_plot.value.open(mode='rb') as fh:
#     img_bytes = fh.read()
#
# Image(img_bytes)
```

`verdi process show` works on the sweep workflow node too, but its per-node table is long, so it's hidden here:

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi process show {wg_sweep.process.pk}
```

## Next steps

You now have the core building blocks: tracked external codes, structured data, calcfunctions, and reusable workflows. The remaining modules can be tackled in whatever order matches your needs, since they each pick up an independent thread:

- {ref}`Module 4 <tutorial:module4>`: more advanced workflow patterns (conditionals, dynamic graphs, sub-workflow composition)
- {ref}`Module 5 <tutorial:module5>`: running on remote HPC clusters
- {ref}`Module 6 <tutorial:module6>`: querying the database with the `QueryBuilder`
- {ref}`Module 7 <tutorial:module7>`: handling failures and recovering from them

## Further reading

- AiiDA's workflow concepts in depth: {ref}`topics:workflows`
- CalcJob concept (for `ShellJob` background): {ref}`topics:calculations:concepts:calcjobs`
- Calcfunctions refresher: {ref}`topics:processes:functions`
- WorkGraph imperative form (`with WorkGraph() as wg:`) and `spec` helpers: [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io)
