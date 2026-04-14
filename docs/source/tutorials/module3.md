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
  # Module 3 runs the Gray-Scott pipeline several times (single run +
  # parameter sweep via Map), so it needs a generous per-cell timeout.
  timeout: 600
---

(tutorial:module3)=
# Module 3: Writing simple workflows

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module3.ipynb` {octicon}`download`
:::

## What you will learn

After this module, you will be able to:

- Describe the WorkGraph mental model: tasks, sockets, links, and graphs
- Wrap existing calcfunctions so they can be composed inside a workflow
- Define a reusable workflow with `@task.graph` and `shelljob`
- Run the workflow and inspect hierarchical provenance
- Turn a Python for-loop into a parallel parameter sweep inside a single workflow

## What you will not learn yet

Error handling, automatic retries, and remote HPC submission are covered in future modules.

## Setup

This module requires an AiiDA profile and the `python_code` variable (see {ref}`Module 1 <tutorial:module1>` for details on the setup cell).

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

In {ref}`Module 2 <tutorial:module2>`, you built a three-step pipeline (`prepare_input` &rarr; ShellJob &rarr; `parse_output`) and ran it in a Python `for` loop.
This has important limitations:

- **No grouping**: each step is a separate process in AiiDA -- there is no single "simulation pipeline" object
- **No hierarchy**: the provenance graph is flat; you can't tell which steps belong together
- **No parallelism**: the loop runs each iteration sequentially and blocks until completion
- **No single entry point**: you can't re-run "the same workflow" with different parameters

A **workflow** solves all of these.
You define the steps and their connections once, and AiiDA handles execution, data passing, and provenance tracking -- grouping everything under a single workflow node.

:::{note}
AiiDA offers two workflow systems: **WorkGraph** (declarative, graph-based) and **WorkChain** (imperative, class-based).
This tutorial uses WorkGraph -- it is more intuitive for composing tasks and scales naturally to complex graphs.
:::

<!-- TODO: Add a comparison table between AiiDA core concepts and WorkGraph concepts:
     CalcJob / WorkChain ↔ WorkGraph task / graph, process nodes, etc.
     From meeting notes: "comparison table between core and WG, make analogous". -->

## The WorkGraph mental model

Before we write any code, it helps to have a mental picture of the four objects WorkGraph is built from:

- **{class}`~aiida_workgraph.WorkGraph`** -- the container. A directed graph of tasks that AiiDA runs as a single workflow process. Every WorkGraph run becomes one top-level process node in the provenance graph.
- **Task** -- a unit of work inside the graph. Each task wraps an *executor*: a Python function, a `calcfunction`, a `CalcJob`, or even another WorkGraph. Tasks are created by calling task-wrapped functions (like `prepare_input(...)` below) inside a graph context.
- **Socket** -- a typed input or output port on a task. When you write `prepare_input(parameters=...).result`, `parameters` is an input socket and `.result` is an output socket.
- **Link** -- a directed connection between an output socket of one task and an input socket of another. Links are created automatically when you pass one task's output socket as an argument to another task.

:::{important}
Inside a workflow definition, **calling a task function does not execute it**.
It creates a task node in the graph and returns a handle whose attributes are output sockets -- references to future values. The actual execution only happens when you call `wg.run()` (or `wg.submit()`).
This is the single most important mental shift when moving from plain Python loops to WorkGraph.
:::

A few more WorkGraph building blocks we will use:

- **`@task.graph`** -- a decorator that turns a Python function into a **graph task** (a reusable sub-workflow). Calling `my_workflow.build(...)` produces a standalone `WorkGraph`; calling `my_workflow(...)` inside another graph embeds it as a sub-task.
- **`shelljob(...)`** -- a helper that adds an `aiida-shell` `ShellJob` to the current graph. It is the WorkGraph equivalent of `launch_shell_job` from {ref}`Module 1 <tutorial:module1>`.
- **`spec`** -- a small module of helpers to declare socket types explicitly (for example `spec.namespace(variance_V=float, mean_V=float)` to declare that a task has two named outputs). You only need it when WorkGraph cannot infer the outputs from the function signature alone.

:::{note}
WorkGraph also ships context managers for runtime control flow: `If`/`While` for conditional and iterative logic, and `Map` for sub-workflows that run once per entry of a collection. We use `Map` for the parameter sweep below; a plain for-loop alternative is shown as well.
:::

## Building the workflow

With the mental model in place, we can now assemble the three-step pipeline (`prepare_input` &rarr; `ShellJob` &rarr; `parse_output`) as a reusable workflow.

### Preparing tasks and inputs

```{code-cell} ipython3
from aiida import orm

from aiida_workgraph import Map, WorkGraph, task, shelljob, spec

from include.constants import BASE_PARAMS, F_VALUES, SCRIPT_PATH
from include.tasks import prepare_input, parse_output
```

We reuse the `prepare_input` and `parse_output` calcfunctions from {ref}`Module 2 <tutorial:module2>` ({download}`include/tasks.py`).

A calcfunction is already an AiiDA process, but to compose it inside a graph we need to wrap it with `task()`.
This wrapping does two things:

1. It turns the function into a **task factory**: calling `prepare_input(parameters=...)` inside a graph no longer runs it, but instead adds a new task to the current graph and returns a handle.
2. It registers input and output sockets. The handle exposes those sockets so we can pass them as inputs to downstream tasks, for example `shelljob(..., nodes={'input': input_file})`.

For `prepare_input`, the default wrapping is enough: its single return value becomes an output socket called `.result`.

`parse_output` is trickier. It returns a plain Python `dict` of `{'variance_V': ..., 'mean_V': ...}`, and WorkGraph cannot introspect the keys of that dict just from the function signature. We have to spell them out using `spec.namespace`, which tells WorkGraph: *"this task has two named output sockets, `variance_V` and `mean_V`, both of type `float`"*.

```{code-cell} ipython3
# Wrap the calcfunctions so they return task handles inside @task.graph().
# We keep the originals around under their plain names and expose the
# WorkGraph-wrapped versions as `*_task`, so it is always clear which variant
# is being used where.
#
# `task(fn)` is enough for `prepare_input`: WorkGraph infers a single `.result`
# output from the return annotation. For `parse_output`, we use `spec.namespace`
# to declare the two named outputs explicitly, so that downstream code can
# refer to `parsed.variance_V` and `parsed.mean_V` as individual sockets.
prepare_input_task = task(prepare_input)
parse_output_task = task(outputs=spec.namespace(variance_V=float, mean_V=float))(parse_output)

# Convert the script path to a SinglefileData node.
# WorkGraph serializes all inputs, so plain Path objects must be wrapped.
script_node = orm.SinglefileData(SCRIPT_PATH)
```

:::{note}
The `spec` module provides other helpers too:

- `spec.namespace(a=int, b=str)` -- fixed, named outputs (what we use above)
- `spec.dynamic(int)` -- a dynamic, open-ended namespace whose keys are only known at runtime (useful for mapped outputs)

You only need `spec` when the default inference does not match what you want. For simple single-return functions, plain `task(fn)` is all you need.
:::

### Defining the graph task

We use the `@task.graph` decorator. The function body looks like regular Python, but remember: none of the calls inside it actually execute anything. They just record a graph of tasks and links that WorkGraph will run later.

```{code-cell} ipython3

@task.graph()
def gray_scott_pipeline(
    parameters: orm.Dict,
    command: orm.AbstractCode,
    script: orm.SinglefileData,
) -> spec.namespace(variance_V=float, mean_V=float):
    """Prepare input, run simulation, parse output."""
    # 1. Add a prepare_input task. `input_file` is an OUTPUT SOCKET of that task,
    #    not an AiiDA node -- the node will only exist once the graph runs.
    input_file = prepare_input_task(parameters=parameters).result

    # 2. Add a ShellJob task. Passing `input_file` as an entry in `nodes` creates
    #    a link from prepare_input.result -> sim.nodes.input automatically.
    sim = shelljob(
        command=command,
        arguments=['{script}', '--input', '{input}', '--output', 'results.yaml'],
        nodes={'script': script, 'input': input_file},
        outputs=['results.yaml'],
    )

    # 3. Add a parse_output task. `sim.results_yaml` is the ShellJob's output
    #    socket for the `results.yaml` file we declared above.
    parsed = parse_output_task(output_file=sim.results_yaml)

    # 4. Wire the two named outputs of parse_output to the graph's own outputs.
    #    Returning a dict here tells WorkGraph: "link parsed.variance_V to the
    #    graph output named 'variance_V', and parsed.mean_V to 'mean_V'".
    return {'variance_V': parsed.variance_V, 'mean_V': parsed.mean_V}
```

:::{dropdown} Declaring graph-level inputs and outputs explicitly
:icon: info

With `@task.graph`, the **function signature** automatically becomes the graph's input interface and the **return statement** its output interface. That's the most concise form and works well when the graph is a thin wrapper around its tasks.

If you need more control, WorkGraph also lets you declare graph-level inputs and outputs **explicitly**, typically with the imperative `with WorkGraph() as wg:` API:

```python
with WorkGraph('explicit_io') as wg:
    wg.inputs.parameters = orm.Dict(BASE_PARAMS)       # declare a graph input
    input_file = prepare_input_task(parameters=wg.inputs.parameters).result
    sim = shelljob(command=python_code, nodes={'input': input_file}, ...)
    parsed = parse_output_task(output_file=sim.results_yaml)
    wg.outputs.variance = parsed.variance_V            # expose under a custom name
```

This is useful when you want to

- reuse a single graph-level input across many tasks,
- hide internal tasks and only expose a curated subset of their outputs, or
- rename things on the way out (for example expose `parsed.variance_V` as `wg.outputs.variance`).

In this module we stick with the `@task.graph`-driven form because it keeps the graph definition close to its signature.
:::

:::{dropdown} (Optional) Peeking inside the graph before running it
:icon: info

If this is your first WorkGraph, it's worth pausing here to convince yourself that the function body above really is just a *specification*. The two cells below build the graph (without running any simulation) and print its structure.

Let's **build** the graph once (without running it) and poke at its structure. `.build(...)` returns a `WorkGraph` object whose tasks and sockets we can inspect directly -- no simulation runs, nothing is stored in AiiDA yet:

```python
wg_preview = gray_scott_pipeline.build(
    parameters=orm.Dict(BASE_PARAMS),
    command=python_code,
    script=script_node,
)

print('Graph outputs (from spec.namespace return annotation):')
for name in wg_preview.outputs._get_keys():
    print(f'  - {name}')

print('\nTasks in the graph (one per call inside the function body):')
for t in wg_preview.tasks:
    print(f'  - {t.name:<25} ({t.identifier})')

shell_task = wg_preview.tasks['ShellJob']
print(f'\nShellJob output sockets (note the underscore):')
for name in shell_task.outputs._get_keys():
    print(f'  - {name}')
```

Three takeaways from the printout:

- The **return type annotation** `-> spec.namespace(variance_V=float, mean_V=float)` is what makes `variance_V` and `mean_V` appear as graph outputs. Without it, WorkGraph would not expose them and the later `map_zone.gather(...)` call would have nothing to collect.
- Inside the function, task inputs accept **both plain Python values and sockets**. We passed `parameters` (an input socket of the graph), `script` (a real `SinglefileData` node), and `input_file` (a socket from `prepare_input_task`). WorkGraph treats them uniformly and creates links wherever a socket is passed.
- The first three entries in the task list are **built-ins** that WorkGraph adds to every graph: `graph_inputs` and `graph_outputs` expose the graph's own input/output sockets as pseudo-tasks (so links into and out of the graph look like ordinary task-to-task links), and `graph_ctx` is a shared key-value store for graph-scoped state -- the WorkGraph analogue of the WorkChain `ctx`. You can write to it with `wg.ctx = {'key': value}` or `wg.update_ctx({'key': ...})` and read back with `wg.ctx.key`. We don't use it in this module, but it's always there.

One more thing worth showing with a print: **the function body of a graph task runs once, at build time** -- the calls inside it don't compute anything, they just register tasks and links. Let's make that concrete with a throwaway graph task:

```python
@task
def double(x: int) -> int:
    return 2 * x


@task.graph()
def demo_graph(x: int) -> int:
    print('  [demo_graph body] running the Python function now')
    handle = double(x=x)
    print(f'  [demo_graph body] handle.result = {handle.result!r}')
    print(f'  [demo_graph body] type(handle.result) = {type(handle.result).__name__}')
    return handle.result


print('>>> calling .build() <<<')
wg_demo = demo_graph.build(x=21)

print('\n>>> calling .run() <<<')
wg_demo.run()

print(f'\nActual output after run: {wg_demo.outputs.result.value}')
```

Two things to notice in the output:

1. All three `[demo_graph body]` lines appear under `>>> calling .build() <<<`, not under `>>> calling .run() <<<`. The Python function itself only ever runs once, while the graph is being constructed.
2. At build time, `handle.result` prints as a `SocketInt` -- not an integer, but WorkGraph already knows the *type* of the eventual value, because `double` was annotated `-> int`. The socket's `value` is still `None`; the actual integer `42` only materializes during `.run()` and is retrieved afterwards via `wg_demo.outputs.result.value`.
:::

### Two ways to use a graph task

A `@task.graph`-decorated function is a **factory**. There are two ways to invoke it:

1. **Standalone workflow** via `.build(...)`. This creates a top-level `WorkGraph` that you can `run()` or `submit()` directly:

   ```python
   wg = gray_scott_pipeline.build(parameters=..., command=..., script=...)
   wg.run()
   ```

2. **Sub-task inside another graph** by calling it directly inside a `with WorkGraph() as wg:` block. In that case it is embedded as a single task in the parent graph, producing hierarchical provenance. We will use this form in the parameter sweep below.

### Running and inspecting

Let's build and run the workflow with a single set of parameters:

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

For a flat summary of the top-level workflow node alone (inputs, outputs, state, exit code, metadata), `verdi process show` is the companion command:

```{code-cell} ipython3

%verdi process show {wg.process.pk}
```

The provenance graph now shows a **hierarchical** structure -- the workflow contains the individual steps:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
# Visualize the hierarchical provenance graph of the workflow.
%run -i include/plot_provenance.py
plot_provenance(wg.process)
```

Compare this to Module 2's flat provenance: instead of disconnected steps, the workflow clearly shows that `prepare_input`, the simulation, and `parse_output` are part of a single logical operation.

## Turning the for-loop into a workflow

### The problem with loops

In Module 2, the parameter sweep was a Python `for` loop calling the pipeline for each `F` value.
But a `for` loop is not an AiiDA process -- it doesn't show up in the provenance, can't be inspected with `verdi`, and can't recover from failures.

### Using Map

WorkGraph's {class}`~aiida_workgraph.Map` lets you run the same sub-workflow over multiple input values, like a parallel `for` loop, but as a single AiiDA workflow with full provenance.

Conceptually, a `Map` zone does three things:

1. It takes a **source collection** of the form `{key: value}` and schedules one copy of its body per entry.
2. Inside the zone, it exposes the current key/value via `map_zone.item.key` and `map_zone.item.value`. These are sockets, so you can wire them into tasks just like any other output.
3. At the end of the zone, `map_zone.gather({...})` declares which per-iteration outputs to collect. The gathered outputs become accessible on `map_zone.outputs.<name>` as a namespace keyed by the original source keys.

```{code-cell} ipython3

# Build a plain-dict mapping {label: parameters} for Map to iterate over.
# The keys become the names of each map iteration in the provenance graph;
# the values are passed into each copy of the sub-workflow.
#
# Why plain dicts and not `orm.Dict` nodes? Map stores its `source` as a
# property on the map task (the stored attributes must be JSON-serializable).
# `orm.Dict` is a database node, not JSON-serializable. AiiDA auto-wraps each
# plain dict into an `orm.Dict` when the sub-task `prepare_input` runs.
#
# Keys must not contain dots -- WorkGraph treats dots as namespace separators.
param_sweep = {f'F_{f_val:.3f}'.replace('.', '_'): BASE_PARAMS | {'F': f_val} for f_val in F_VALUES}

print(f'{len(param_sweep)} parameter sets (only F varies):')
for key, val in param_sweep.items():
    print(f'  {key:<10}  ->  F = {val["F"]}')
```

```{code-cell} ipython3
:tags: ["hide-output"]

with WorkGraph('gray_scott_sweep') as wg_sweep:
    # Enter a map zone. Everything inside the `with Map(...)` block will be
    # executed once per entry in `param_sweep`.
    with Map(param_sweep) as map_zone:
        # Call the graph task inside the parent graph: this embeds it as a
        # sub-task. `map_zone.item.value` is a socket that resolves, at runtime,
        # to the dict of parameters for the current iteration.
        result = gray_scott_pipeline(
            parameters=map_zone.item.value,
            command=python_code,
            script=script_node,
        )

        # Tell the map zone which per-iteration outputs to collect. The keys
        # passed to `gather` become attributes on `map_zone.outputs`, each
        # holding a namespace keyed by the `param_sweep` keys.
        map_zone.gather({'variance_V': result.variance_V, 'mean_V': result.mean_V})

_ = wg_sweep.run()
```

:::{note}
A few things to keep in mind about `Map`:

- The source must be a mapping (a `dict` or a socket of a dynamic namespace). Iterating over a plain list is not supported directly -- wrap it into a dict first, using meaningful keys like `F_0_040` rather than integer indices, because those keys will show up in the provenance graph and as the names of the gathered outputs. **Avoid dots in keys** -- WorkGraph treats dots as namespace separators, which will silently collapse your entries.
- `map_zone.item.value` is the value for the current iteration, `map_zone.item.key` is its key. Both are sockets, so you can pass them as task inputs, but you cannot use them as ordinary Python values inside the graph function (no `if` on them, no string concatenation).
- After the `with` block, `map_zone.outputs.<name>` gives you a namespace that behaves like a dict of AiiDA nodes, keyed by the original source keys.
:::

### Running and inspecting the sweep

```{code-cell} ipython3
:tags: ["hide-output"]

print(f"Sweep WorkGraph PK: {wg_sweep.process.pk}")
%verdi process status {wg_sweep.process.pk}
```

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi process show {wg_sweep.process.pk}
```

:::{tip}
The provenance graph for the full sweep is quite large (5 sub-workflows with 3 steps each).
To explore it interactively, download this notebook via the link at the top and run `plot_provenance(wg_sweep.process)` locally, or use `verdi node graph generate {wg_sweep.process.pk}` from the command line.
:::

### Analyzing results

The gathered results are accessible on the map zone's output sockets.
Each gathered output is a namespace keyed by the `param_sweep` keys:

```{code-cell} ipython3

# Access the gathered results from the Map zone outputs.
variances = map_zone.outputs.variance_V._value

for key in sorted(variances):
    print(f"  {key}: variance(V) = {float(variances[key].value):.4e}")
```

```{code-cell} ipython3

%run -i include/plot_sweep.py
plot_transition_curve(
    list(F_VALUES),
    [float(variances[key].value) for key in sorted(variances)],
)
```

The key advantage: the entire sweep -- every pipeline run, every input, every output -- lives under a single workflow node in AiiDA's provenance graph.

## Summary

In this module you learned to:

- **Define a reusable workflow** with `@task.graph` and `shelljob`
- **Run and inspect** hierarchical provenance -- workflows grouping their child processes
- **Turn a Python for-loop** into a mapped workflow with `Map`
- **Compare** flat (Module 2) vs hierarchical (Module 3) provenance

:::{seealso}
- [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io) -- full reference for WorkGraph
- {ref}`Topic: workflows <topics:workflows>` -- AiiDA workflow concepts in depth
:::

## Next steps

You now have a complete pipeline from running simulations to building workflows.
Future modules will cover error handling, remote HPC submission, and advanced workflow patterns.
