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
(tutorial:module3a)=
# Module 3a: Writing a simple workflow

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

Running that workflow over *many* inputs, replacing the Python `for`-loop, is the subject of {ref}`Module 3b <tutorial:module3b>`.

:::{note} Setup
This module uses AiiDA, `aiida-shell`, and `aiida-workgraph`:

```bash
pip install aiida-core aiida-shell aiida-workgraph
```
:::

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
That separation is why a comparison like `parsed.variance_V > threshold` produces a new socket (a comparison task) rather than a Python `bool`.
It is also why iterating a socket with a Python `for`, or branching on it with a plain `if`, does not work the way you might expect.
It is the single most important mental shift when moving from plain Python control flow to WorkGraph.
:::

## Composing the pipeline as a workflow

With the mental model in place, we can assemble the three-step pipeline as a reusable workflow.
The imports below cover everything we will use across this module; each helper is introduced when it first comes up.

```{code-cell} ipython3
from aiida import orm

from aiida_workgraph import WorkGraph, task, shelljob

from include.tasks import prepare_input, parse_output

# The fixed Gray-Scott parameters we run the pipeline with.
BASE_PARAMS = {
    'grid_size': 64,
    'du': 0.16,
    'dv': 0.08,
    'F': 0.04,
    'k': 0.065,
    'dt': 1.0,
    'n_steps': 3000,
    'seed': 42,
}
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
If WorkGraph can't infer the shape (for example, a function you don't control that returns a plain `dict`), you can pass an explicit spec via `task(outputs=...)`.
The `dynamic(...)` and `namespace(...)` helpers, for sockets whose keys are only known at runtime, come up in {ref}`Module 3b <tutorial:module3b>`, where we actually need them.
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
`simulation.stdout` is the ShellJob's auto-captured stdout socket; that is where `gsrd` prints the summary numbers our parser reads out.

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
- The task list includes a handful of **built-ins** that WorkGraph adds to every graph: `graph_inputs` and `graph_outputs` expose the graph's own I/O as pseudo-tasks so that links into and out of the graph look like ordinary task-to-task links, and `graph_ctx` is a shared key-value store that tasks can read and write, reachable via `wg.ctx.foo`, covered in {ref}`Module 6 <tutorial:module6>`.

WorkGraph also exposes the same structure as an **interactive graph viewer**. Click around the nodes to see the sockets and links; the flow is `graph_inputs` &rarr; `prepare_input` &rarr; `ShellJob` &rarr; `parse_output` &rarr; `graph_outputs`.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg_preview
```

`gray_scott_pipeline` does not run anything by itself.
Calling `.build(...)` turns it into a ready-to-run `WorkGraph`.
You can `run()` or `submit()` that graph directly, or drop the same call inside a bigger graph to reuse the pipeline as one step (which is exactly what {ref}`Module 3b <tutorial:module3b>` does).
For now, let's build it with a single set of parameters and run it.

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

## Next steps

You've turned the Module 2 pipeline into a single, reusable workflow node.
In {ref}`Module 3b <tutorial:module3b>`, you'll run that same workflow over many inputs at once with WorkGraph's `Map`, turning the Python `for`-loop from Module 2 into one tracked, parallel workflow.

## Further reading

- AiiDA's workflow concepts in depth: {ref}`topics:workflows`
- CalcJob concept (for `ShellJob` background): {ref}`topics:calculations:concepts:calcjobs`
- Calcfunctions refresher: {ref}`topics:processes:functions`
- Running versus submitting processes: {ref}`topics:processes:usage:launching`
- WorkGraph documentation: [aiida-workgraph](https://aiida-workgraph.readthedocs.io)
