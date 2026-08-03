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

{bdg-secondary}`⏱️ ~60 min read` {bdg-primary}`Intermediate`

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module3a.ipynb` {octicon}`download`
:::

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

- Build a reusable workflow from existing calcfunctions and CalcJobs
- Connect tasks by passing one task's output as another task's input, so the whole pipeline is tracked as a single named process you can query and restart
- Inspect the workflow as a single process node and explore its individual child steps

Running that workflow over *many* inputs, replacing the Python `for`-loop, is the subject of {ref}`Module 3b <tutorial:module3b>`.

:::{note}
This module uses `aiida-core`, `aiida-shell`, and `aiida-workgraph`. Install them with:

```bash
# aiida-core from `main` until v2.9 ships the ZeroMQ broker used here
uv pip install git+https://github.com/aiidateam/aiida-core aiida-shell aiida-workgraph matplotlib git+https://github.com/GeigerJ2/gsrd.git@fix/dont-raise-on-trivial-state
```

`aiida-workgraph` is currently a separate package; it is planned to become part of `aiida-core` with the v3.0 release.
:::

```{code-cell} ipython3
# Set up the tutorial's isolated sandbox profile (see Module 1 for details).
from pathlib import Path

if not Path('include/setup_tutorial.py').exists():
    import urllib.request

    Path('include').mkdir(exist_ok=True)
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/GeigerJ2/aiida-core/docs/integrate-tutorials/docs/source/tutorials/include/setup_tutorial.py',
        'include/setup_tutorial.py',
    )

%load_ext aiida
%run -i include/setup_tutorial.py
```

## Why workflows?

In {ref}`Module 2 <tutorial:module2>`, you built a three-step pipeline (`prepare_input` &rarr; `ShellJob` &rarr; `parse_output`) and ran it in a Python `for` loop.
That works for a single run, but leaves several gaps:

- **No single pipeline object**: the steps are linked in the provenance graph, but nothing ties them together into one entity you can restart, execute with different parameters, or query.
- **Sequential only**: the Python loop waits for each iteration to finish; a workflow can run independent iterations in parallel.
- **Tied to your session**: the loop runs inside your Python process and dies with it; a workflow submitted to the daemon runs in the background and survives you closing the notebook.

A **workflow** solves all of these.
You define the steps and their connections once, and AiiDA handles execution, data transfer, and provenance tracking, with the whole pipeline recorded under a single workflow node.

:::{note}
AiiDA offers two workflow systems.
**WorkChain** (imperative, class-based) is the classical, long-standing API: you write the steps in order and pass state between them yourself.
**WorkGraph** (declarative, graph-based) is a newer, simpler API for building workflows by connecting tasks in a graph, and is what this tutorial uses.
:::

::::{dropdown} WorkChain vs WorkGraph concept mapping
:icon: table

If you already know the older WorkChain API, or meet it in a plugin, here is how its concepts map to the WorkGraph ones this tutorial uses:

| WorkChain | WorkGraph | Notes |
|---|---|---|
| `WorkChain` class | `WorkGraph` / `@task.graph` | both are workflow-level process nodes |
| `spec.outline(...)` in `define()` | the `@task.graph` body wiring tasks | WorkGraph replaces the imperative outline with a declarative graph |
| `spec.input(...)` / `spec.output(...)` | input / output sockets | in WorkGraph these come from the wrapped function's signature |
| `self.submit(SomeCalcJob, ...)` | `task`-wrapped `CalcJob` (`shelljob()` for `ShellJob`) | how each framework runs a CalcJob |
| calling a `calcfunction` in a step | `@task`-wrapped function | `@task` turns any callable into a graph task |
| `ToContext` / `self.ctx` | socket links, plus `wg.ctx` for shared state | most data passes via socket links; `wg.ctx` covers state that doesn't fit a socket ({ref}`Module 6 <tutorial:module6>`) |
| `engine.submit(...)` / `engine.run(...)` | `wg.submit()` / `wg.run()` | same semantics: hand to the daemon (`submit`) or block in-process (`run`) |
| `WorkChainNode` | `WorkGraphNode` | the same kind of provenance node (`WorkGraphNode` subclasses `WorkChainNode`) |

::::

## The WorkGraph mental model

Before we write any code, it helps to have a mental picture of the four main objects WorkGraph is built from:

- **WorkGraph**: the container. A directed graph of tasks that AiiDA runs as a single workflow process. Every WorkGraph run becomes one process node in the provenance graph.
- **Task**: a unit of work inside the graph. Each task wraps an *executor*: a Python function, a `calcfunction`, a `CalcJob`, or even another WorkGraph. Tasks are created by calling task-wrapped functions inside a graph context.
- **Socket**: a typed input or output port on a task. A task's arguments are its input sockets, and the values it produces are its output sockets.
- **Link**: a directed connection between an output socket of one task and an input socket of another. Links are created automatically when you pass one task's output socket as an argument to another task.

:::{important}
Building the graph and running the graph are two separate steps.
:::

Inside a WorkGraph definition, calling a task function does not execute it.
It creates a task in the graph and returns its **output sockets**: placeholders for values that don't exist yet.
You are handling sockets, not AiiDA ORM nodes.

This is the single most important shift from ordinary Python. Normally, running your code executes it; running the code that builds a WorkGraph only *assembles* the graph. Its tasks run only when you explicitly run or submit the graph via `wg.run` or `wg.submit`, respectively.

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
The wrapped version adds a task to the current graph when called and returns that task's output sockets, which you can then pass to downstream tasks.

WorkGraph infers a task's sockets directly from the wrapped function's signature:

- **Input sockets** come from the function's positional and keyword arguments. Each argument name becomes an input socket of the same name.
- **Output sockets** come from the return annotation. A single annotated return type produces one output socket (named `.result` by default), while a `TypedDict`, dataclass, or Pydantic model produces one named socket per field.

Concretely:

- `prepare_input(parameters: orm.Dict) -> orm.SinglefileData` exposes one input socket `parameters` and the default output socket `.result`.
- `parse_output(stdout: orm.SinglefileData) -> ParseOutputs` exposes one input socket `stdout` and two output sockets `.variance_V` and `.mean_V` (the keys of the `ParseOutputs` TypedDict).

This is the same `.result` convention you saw for the plain calcfunctions in {ref}`Module 2 <tutorial:module2>` (there, `node.outputs.result`).

`@task()` is a decorator; for functions defined elsewhere we apply it explicitly:

```{code-cell} ipython3
prepare_input_task = task()(prepare_input)
parse_output_task = task()(parse_output)

# `*_task` = WorkGraph-wrapped variants; the originals stay usable under
# their plain names.
# `task()(fn)` is the explicit decorator-application form, equivalent to
# writing `@task()` above the definition.
```

:::{note}
Plain `task()(fn)` works whenever WorkGraph can infer the outputs from the return annotation (here, because `prepare_input` is annotated `-> orm.SinglefileData` and `parse_output` `-> ParseOutputs`).
When it can't (for example, a function you don't control that returns a plain `dict`), pass an explicit spec via `task(outputs=...)`.
:::

With the tasks wrapped, we can write the workflow itself: a Python function decorated with `@task.graph()`.
Its body reads like ordinary Python, but as the callouts above already noted, the calls inside register tasks and links rather than executing right away.
The function signature becomes the graph's inputs and the return statement its outputs.

The canonical definition lives in `include/workflows.py` so later modules (and other notebooks) can import the same pipeline rather than redefining it.
The file declares one extra output socket on top of what we strictly need here, `results_npz`, so Module 6 can read the V-field for follow-on analyses. It is inlined verbatim in the snippet below:

```{literalinclude} include/workflows.py
:language: python
:pyobject: gray_scott_pipeline
```

We bring it into the current namespace with a plain import:

```{code-cell} ipython3
from include.workflows import gray_scott_pipeline
```

Let's walk through it line by line:

```python
prepared = prepare_input_task(parameters=parameters)
```

Adds the `prepare_input` task to the graph. The add is implicit: because `gray_scott_pipeline` is a `@task.graph()` function, an active graph exists while its body runs, and calling a task-wrapped function registers it there.
`prepared` holds the task's output sockets: references to future values that don't exist as AiiDA nodes until the graph runs.

```python
simulation = shelljob(..., nodes={'input': prepared.result}, ...)
```

`shelljob()` is a convenience function provided by `aiida-workgraph` that handles the actual `ShellJob` setup for you behind the scenes and adds it to the active graph.
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
`parsed.variance_V` and `parsed.mean_V` are the two scalar results parsed from stdout; `simulation.results_npz` is the file output declared on the `ShellJob` (`outputs=['results.npz']`), kept around so later modules can read the V and U fields directly.

Before running anything, it helps to convince yourself that the function body above really is just a *specification*.
`.build(...)` returns a `WorkGraph` object whose tasks and sockets we can inspect without running any simulation:

```{code-cell} ipython3
wg_preview = gray_scott_pipeline.build(
    parameters=BASE_PARAMS,
    command=gsrd_code,
)

print('Graph inputs: ', [name for name in wg_preview.get_input_names() if name != 'metadata'])
print('Graph outputs:', wg_preview.get_output_names())
print('Tasks:        ', [t.name for t in wg_preview.tasks])
```

Two things to notice:

- Task inputs accept both **concrete data and sockets**. Above, `command` (an `InstalledCode` node) and `parameters` (a plain dict AiiDA stores as a `Dict`) are concrete inputs, while `prepared.result` is a socket. Concrete inputs are stored directly as the task's input; a socket instead adds a link from the producing task, resolved to its value only at execution time.
- The list also shows a few **built-ins** WorkGraph adds to every graph. `graph_inputs` and `graph_outputs` stand in for the graph's own inputs and outputs, so connections into and out of the graph look like ordinary links between tasks. `graph_ctx` is a shared key-value store tasks can read and write (via `wg.ctx`), covered in {ref}`Module 6 <tutorial:module6>`.

WorkGraph also exposes the same structure as an **interactive graph viewer**. Click around the nodes to see the sockets and links; the flow is `graph_inputs` &rarr; `prepare_input` &rarr; `ShellJob` &rarr; `parse_output` &rarr; `graph_outputs`.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg_preview
```

`gray_scott_pipeline` is a *blueprint*: a reusable definition, not yet tied to any particular inputs. `.build(parameters, command)` makes that blueprint concrete, wiring it up for one specific set of inputs and returning a concretized `WorkGraph`.
So, let's build it with a specific set of parameters.

```{code-cell} ipython3
wg = gray_scott_pipeline.build(
    parameters=BASE_PARAMS,
    command=gsrd_code,
)
```

Now run it: calling `run()` executes the graph in-process, while `submit()` would hand it to the AiiDA daemon. You can also reuse `gray_scott_pipeline` as one step inside a bigger graph, which is exactly what {ref}`Module 3b <tutorial:module3b>` does.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg.run()
```

Expanding the cell above shows the workflow's progress log and, at the very end, a dict of the resolved output values: `variance_V`, `mean_V`, and `results_npz` as concrete `Float` / `SinglefileData` nodes, the return value of `wg.run()`.

`wg` itself stays a Python-side container around the graph definition. The actual AiiDA process node that records the execution lives on `wg.process` and is a `WorkGraphNode` (a subclass of `aiida-core`'s `WorkChainNode`):

```{code-cell} ipython3
print(f"process: {wg.process.process_label}")
print(f"PK:      {wg.process.pk}")
print(f"state:   {wg.state}")
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
shelljob_node = [child for child in wg.process.called if isinstance(child, orm.CalcJobNode)][0]

print(f'ShellJob PK:    {shelljob_node.pk}')
print(f'process_label:  {shelljob_node.process_label}')
print(f'caller PK:      {shelljob_node.caller.pk}  ({shelljob_node.caller.process_label})')
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

Compare this to Module 2's flat provenance: the three process nodes are the same (`prepare_input`, the `ShellJob`, `parse_output`), but they are now *children* of a `WorkGraph<gray_scott_pipeline>` orchestrator node (highlighted with a bold red border).
The orchestrator is linked to each child step it called and back to the outputs it returned, so the **whole pipeline is one queryable, inspectable unit in the database**.

## Next steps

You've turned the Module 2 pipeline into a single, reusable workflow.
In {ref}`Module 3b <tutorial:module3b>`, you'll apply the same idea to the outer loop: running that workflow over many inputs at once with WorkGraph's `Map` turns the Python `for`-loop from Module 2 into one tracked, parallel workflow too.

## Further reading

- AiiDA's workflow concepts in depth: {ref}`topics:workflows`
- CalcJob concept (for `ShellJob` background): {ref}`topics:calculations:concepts:calcjobs`
- Calcfunctions refresher: {ref}`topics:processes:functions`
- Running versus submitting processes: {ref}`topics:processes:usage:launching`
- WorkGraph documentation: [aiida-workgraph](https://aiida-workgraph.readthedocs.io)
