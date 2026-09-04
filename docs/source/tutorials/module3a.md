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

:::{dropdown} Installation requirements
This module uses `aiida-core` and `aiida-workgraph`. Install them with:

```bash
uv pip install "aiida-core>=2.9" "aiida-workgraph>=0.9.0" matplotlib "gsrd>=0.2.0"
```

`aiida-workgraph` is currently a separate package; it is planned to become part of `aiida-core` with the v3.0 release.
:::

:::{note}
This module reuses the tutorial profile and the `gsrd_code` object from {ref}`Module 1 <tutorial:module1>`, and assumes both are already up and running.
If not, or you are starting here, work through the {ref}`setup section of Module 1 <tutorial:module1:setup>` first.
:::

```{code-cell} ipython3
:tags: [remove-cell]

# Point AiiDA at a local .aiida-tutorial/ sandbox (via AIIDA_PATH, so nothing touches
# your real ~/.aiida), then create the `tutorial` profile and register the gsrd code
# if they do not exist yet. Module 1 creates them; later modules find and reuse them.
import os
import shutil
import sys
import warnings
from importlib.resources import files
from pathlib import Path

from aiida.manage.configuration import get_config, reset_config
from aiida.manage.configuration.settings import AiiDAConfigDir

PROFILE_NAME = 'tutorial'
os.environ['AIIDA_PATH'] = str(
    Path(os.environ.get('AIIDA_TUTORIAL_SANDBOX', '.aiida-tutorial')).resolve()
)
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', message='Creating AiiDA configuration folder')
    AiiDAConfigDir.set()
    reset_config()
    config = get_config(create=True)

if PROFILE_NAME not in config.profile_names:
    # gsrd ships the Code config (label, computer, plugin); -X sets the executable path.
    gsrd = shutil.which('gsrd') or str(Path(sys.executable).parent / 'gsrd')
    code_config = files('gsrd') / 'data' / 'gsrd_code.yaml'
    !verdi presto --profile-name {PROFILE_NAME} --use-zeromq
    !verdi -p {PROFILE_NAME} config set warnings.development_version False
    !verdi -p {PROFILE_NAME} code create core.code.installed -n --config {code_config} -X {gsrd}
    reset_config()
```

```{code-cell} ipython3
:tags: [remove-cell]

# Load the profile into this kernel, start the daemon, and get a handle on the gsrd Code.
import time

from aiida import load_profile
from aiida.manage import get_manager
from aiida.orm import load_code

load_profile(PROFILE_NAME, allow_switch=True)
!verdi -p {PROFILE_NAME} daemon start

# `daemon start` returns before the ZeroMQ broker is reachable; wait for it so a later
# `verdi status` does not report "Broker is NOT running" (and fail the notebook).
_broker = get_manager().get_broker()
_deadline = time.monotonic() + 30.0
while _broker is not None and not _broker.check_service_reachable() and time.monotonic() < _deadline:
    time.sleep(0.2)

gsrd_code = load_code('gsrd@localhost')

%load_ext aiida
```

```{code-cell} ipython3
:tags: [remove-cell]

# A thin provenance-graph helper used throughout the tutorial (plotting is not the focus).
def plot_provenance(node):
    """Return a Graphviz digraph of *node* and its connected provenance (rendered inline)."""
    from aiida.tools.visualization import Graph

    graph = Graph()
    graph.recurse_ancestors(node, annotate_links='both', include_process_outputs=True)
    graph.recurse_descendants(node, annotate_links='both', include_process_inputs=True)
    return graph.graphviz
```

## What you will learn

After this module, you will be able to:

- Build a reusable workflow from existing calcfunctions and CalcJobs
- Connect tasks by passing one task's output as another task's input, so the whole pipeline is tracked as a single named process you can query and restart
- Inspect the workflow as a single process node and explore its individual child steps

Running that workflow over *many* inputs in parallel is the subject of {ref}`Module 3b <tutorial:module3b>`.

## Why workflows?

In {ref}`Module 2 <tutorial:module2>`, you built a three-step pipeline (`prepare_input` &rarr; `ShellJob` &rarr; `parse_output`) and wrapped it in a `run_pipeline` function.
That gets the job done, but leaves some gaps:

- **No single pipeline object**: the three steps are linked in the provenance graph only through the data passed between them, so nothing ties them into one node you can hand around, restart, or query as a single run.
- **Tied to your session**: the calls run inside your Python process and die with it; an actual AiiDA workflow can instead be submitted to the daemon, which runs it in the background so it survives you closing the notebook.

Both of these gaps close when you build the pipeline as one **workflow**.
You define the steps and their connections once, and AiiDA gathers the whole pipeline under a single workflow node, one object you can hand around, restart, query, or submit to the daemon.

:::{note}
AiiDA offers two workflow systems.
**WorkChain** (imperative, class-based) is the classical, long-standing API: you write the steps in order and pass state between them yourself.
**WorkGraph** (declarative, graph-based) is a newer, simpler API for building workflows by connecting tasks in a graph, and is what this tutorial uses.
:::

## The WorkGraph mental model

Before we write any code, it helps to have a mental picture of the four main objects WorkGraph is built from:

- **WorkGraph**: the container. A directed graph of tasks that AiiDA runs as a single workflow process. Every WorkGraph run becomes one process node in the provenance graph.
- **Task**: a unit of work inside the graph. Each task wraps an *executor*: a Python function, a `calcfunction`, a `CalcJob`, or even another WorkGraph.
- **Socket**: a typed input or output port on a task. A task's arguments are its input sockets, and the values it produces are its output sockets.
- **Link**: a directed connection between an output socket of one task and an input socket of another. Links are created automatically when you pass one task's output socket as an argument to another task.

:::{important}
Building the graph and running the graph are two separate steps.
Inside a WorkGraph definition, calling a task function does not execute it.
It creates a task in the graph and returns its **output sockets**: placeholders for values that don't exist yet.
You are handling sockets, not AiiDA ORM nodes or plain Python objects.
:::

This is the single most important shift from ordinary Python. Normally, running your code executes it; running the code that builds a WorkGraph only *assembles* the graph. Its tasks run only when you explicitly run or submit the graph via `wg.run` or `wg.submit`, respectively.

## Composing the pipeline as a workflow

With the mental model in place, we can assemble the three-step pipeline as a reusable workflow.
The imports below cover everything we will use across this module; each helper is introduced when it first comes up.

```{code-cell} ipython3
from aiida import orm

from aiida_workgraph import WorkGraph, task, shelljob

# The fixed Gray-Scott parameters we run the pipeline with.
BASE_PARAMS = {
    'grid_size': 128,
    'du': 0.16,
    'dv': 0.08,
    'F': 0.04,
    'k': 0.060,
    'dt': 1.0,
    'n_steps': 10000,
    'seed': 42,
}
```

We reuse the `prepare_input` and `parse_output` calcfunctions from {ref}`Module 2 <tutorial:module2>`. Each notebook runs in its own kernel, so we redefine them here (the same code as Module 2):

```{code-cell} ipython3
:tags: [hide-cell]
:mystnb:
:    code_prompt_show: 'Show the Module 2 calcfunctions'
:    code_prompt_hide: 'Hide the Module 2 calcfunctions'

# The prepare_input and parse_output calcfunctions from Module 2, redefined here
# so this notebook's kernel has them (each module runs in its own kernel).
import re
from typing import TypedDict

import yaml

from aiida import engine


class ParseOutputs(TypedDict):
    """Named outputs produced by parse_output."""

    variance_V: orm.Float
    mean_V: orm.Float


VARIANCE_RE = re.compile(r'Variance of V field\s*:\s*([\d.eE+-]+)')
MEAN_RE = re.compile(r'Mean\s+of V field\s*=\s*([\d.eE+-]+)')


@engine.calcfunction
def prepare_input(parameters: orm.Dict) -> orm.SinglefileData:
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.value)
    return orm.SinglefileData.from_string(content, filename='input.yaml')


@engine.calcfunction
def parse_output(stdout: orm.SinglefileData) -> ParseOutputs:
    """Extract variance_V and mean_V scalars from the gsrd stdout log."""
    text = stdout.get_content(mode='r')
    variance_match = VARIANCE_RE.search(text)
    mean_match = MEAN_RE.search(text)
    if variance_match is None or mean_match is None:
        msg = "gsrd stdout did not contain 'Variance of V field' / 'Mean of V field' diagnostics"
        raise ValueError(msg)
    return {
        'variance_V': orm.Float(float(variance_match.group(1))),
        'mean_V': orm.Float(float(mean_match.group(1))),
    }
```

A calcfunction is already an AiiDA process, but to compose it inside a graph we wrap it with `task()`.
The wrapped version adds a task to the current graph when called and returns that task's output sockets, which you can then pass to downstream tasks.

WorkGraph infers a task's sockets directly from the wrapped function's signature:

- **Input sockets** come from the function's parameters. Each parameter becomes an input socket of the same name.
- **Output sockets** come from the return annotation. A single annotated return type produces one output socket (named `.result` by default), while a `TypedDict`, dataclass, or Pydantic model produces one named socket per field.

Concretely:

- `prepare_input(parameters: orm.Dict) -> orm.SinglefileData` exposes one input socket `parameters` and the default output socket `.result`.
- `parse_output(stdout: orm.SinglefileData) -> ParseOutputs` exposes one input socket `stdout` and two output sockets `.variance_V` and `.mean_V` (the keys of the `ParseOutputs` TypedDict).

This is the same `.result` convention you saw for the plain calcfunctions in {ref}`Module 2 <tutorial:module2>` (there, `node.outputs.result`).

`@task()` is a Python decorator, so for functions defined elsewhere we apply it explicitly: calling `task()(fn)` is the same as writing `@task()` above the definition.

```{code-cell} ipython3
prepare_input_task = task()(prepare_input)
parse_output_task = task()(parse_output)
```

We assign the wrapped versions to the original names with a `_task` suffix (`prepare_input_task`, `parse_output_task`); the original functions stay usable under their plain names.

:::{note}
Socket inference needs a usable return annotation. Without one (for example, a function you don't control that returns a plain `dict`), WorkGraph falls back to a single `.result` socket holding the whole return value; pass `task(outputs=...)` to expose named output sockets instead.
:::

With the tasks wrapped, we can write the workflow itself: a Python function decorated with `@task.graph()`.
The function's parameters become the graph's inputs and the return statement its outputs.

:::{important}
The `@task.graph()` decorator is what assembles these calls into a workflow. Called on their own, outside, the wrapped tasks run nothing and produce no usable graph: each call only hands back its output sockets. Inside a `@task.graph()` body, though, an **active graph** is in scope, so each task call registers itself into the graph automatically; you never add tasks by hand.
The assembled steps become a single, named workflow you can `.build()` (see below), run, or submit.
:::

We define the workflow as a `@task.graph()`-decorated function. {ref}`Module 3b <tutorial:module3b>` needs the same pipeline; since each notebook has its own kernel, it redefines it there rather than importing.

```{code-cell} ipython3
from typing import TypedDict


class GrayScottOutputs(TypedDict):
    """Outputs of gray_scott_pipeline: the two scalars plus the full results.npz file."""

    variance_V: orm.Float
    mean_V: orm.Float
    results_npz: orm.SinglefileData


@task.graph()
def gray_scott_pipeline(
    parameters: orm.Dict,
    command: orm.InstalledCode,
) -> GrayScottOutputs:
    """Run one gsrd simulation and parse its results (variance_V, mean_V, results_npz)."""
    prepared = prepare_input_task(parameters=parameters)

    simulation = shelljob(
        command=command,
        arguments=['{input}'],
        nodes={'input': prepared.result},
        outputs=['results.npz'],
    )

    parsed = parse_output_task(stdout=simulation.stdout)

    return {
        'variance_V': parsed.variance_V,
        'mean_V': parsed.mean_V,
        'results_npz': simulation.results_npz,
    }
```

Let's walk through it line by line:

```python
prepared = prepare_input_task(parameters=parameters)
```

Adds the `prepare_input` task to the active graph.
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

:::{note}
This return is also where `gray_scott_pipeline` differs from `run_pipeline` in {ref}`Module 2 <tutorial:module2>`, which returned the `parse_output` **node**.
There, with no workflow node to hold onto, that node was the handle you tagged, grouped, and queried.
A `@task.graph()`'s `return` instead declares the workflow's **output sockets**, so the workflow exposes the results themselves (`variance_V`, `mean_V`, `results_npz`); the single handle for the whole run is now the WorkGraph node, which you organize and query as one unit.
:::

`gray_scott_pipeline`, until now, is a reusable graph *blueprint*, not a concrete `WorkGraph` object yet. Passing it an actual set of inputs through its `.build()` method produces an actual `WorkGraph` object:

```{code-cell} ipython3
wg = gray_scott_pipeline.build(
    parameters=BASE_PARAMS,
    command=gsrd_code,
)
```

Task inputs accept both **concrete data and sockets**: when we called `.build()`, `command` (an `InstalledCode` node) and `parameters` (a plain dict AiiDA stores as a `Dict`) went in as concrete values, while inside the workflow body `prepared.result` was a socket. A concrete input is stored directly on the task; a socket instead adds a link from the producing task, resolved to its value only at execution time.

WorkGraph can also render the assembled graph in an **interactive viewer**. Click around the nodes to see the sockets and links; the flow is `graph_inputs` &rarr; `prepare_input` &rarr; `ShellJob` &rarr; `parse_output` &rarr; `graph_outputs`.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg
```

The `graph_inputs` and `graph_outputs` nodes are built-ins that stand in for the graph's own inputs and outputs, so connections into and out of the graph look like ordinary links between tasks; a third built-in, `graph_ctx`, is a shared key-value store tasks can read and write (via `wg.ctx`).

Everything so far has only *built* the graph. To execute it, we call `.run()` (in-process), or `.submit()` that would instead hand it to the AiiDA daemon. You can also reuse `gray_scott_pipeline` as one step inside a bigger graph, which is exactly what {ref}`Module 3b <tutorial:module3b>` does.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

results = wg.run()
```

`.run()` executes the graph (expand the cell above for the progress log) and returns its resolved outputs, which we capture in `results`: a dict mapping each declared output to a concrete node, `variance_V` and `mean_V` as `Float` nodes and `results_npz` as a `SinglefileData`.

```{code-cell} ipython3
for label, node in results.items():
    print(f'{label:<12} {type(node).__name__:<15} {node}')
```

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
shelljob_node = next(
    child for child in wg.process.called if isinstance(child, orm.CalcJobNode)
)

print(f'ShellJob PK:    {shelljob_node.pk}')
print(f'process_label:  {shelljob_node.process_label}')
print(
    f'caller PK:      {shelljob_node.caller.pk}  ({shelljob_node.caller.process_label})'
)
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
plot_provenance(wg.process)
```

Compare this to Module 2's flat provenance: the three process nodes are the same (`prepare_input`, the `ShellJob`, `parse_output`), but they are now *children* of a `WorkGraph<gray_scott_pipeline>` orchestrator node (highlighted with a bold red border).
The orchestrator is linked to each child step it called and back to the outputs it returned, so the **whole pipeline is one queryable, inspectable unit in the database**.

## Reusing the pipeline

Because `gray_scott_pipeline` is a self-contained object, we can run it on any inputs, not only `BASE_PARAMS`.
To close the loop on {ref}`Module 0 <tutorial:module0>`, we reproduce three of its gallery patterns, this time each a tracked AiiDA workflow rather than a throwaway script run: the pipeline takes whatever feed and kill rates we hand it.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show the three workflow runs'
:    code_prompt_hide: 'Hide the three workflow runs'

morphologies = {
    'spots': {**BASE_PARAMS, 'F': 0.030, 'k': 0.062},
    'stripes': {**BASE_PARAMS, 'F': 0.026, 'k': 0.055},
    'labyrinth': {**BASE_PARAMS, 'F': 0.046, 'k': 0.063},
}

runs = {}
for name, params in morphologies.items():
    wg = gray_scott_pipeline.build(parameters=params, command=gsrd_code)
    wg.run()
    runs[name] = wg.process  # the WorkGraph node for this run
```

Each entry in `runs` is one workflow's **process node**, so `runs['spots'].outputs.results_npz` is that run's `results.npz`, with provenance back to the parameters that produced it.
Plotting the `V` field of each (unwrapping each run's `results.npz` node into its array, then handing them to `gsrd`'s `plot_field_gallery`) reproduces the Module 0 gallery, computed live:

```{code-cell} ipython3
:tags: [hide-input]
:mystnb:
:    code_prompt_show: 'Show the plotting code'
:    code_prompt_hide: 'Hide the plotting code'

import matplotlib.pyplot as plt
import numpy as np

from gsrd.plotting import plot_field_gallery

# Unwrap each run's results.npz node into its final V field, then plot the gallery.
fields = {}
for name, node in runs.items():
    with node.outputs.results_npz.open(mode='rb') as fh:
        fields[name] = np.load(fh, allow_pickle=True)['V_final']

plot_field_gallery(fields)
plt.show()
```

These are no longer static images: each is a node you can query, inspect, and trace back to its inputs.
To make one findable later, we attach a searchable **extra** to the labyrinth run's node, a free-form key-value tag:

```{code-cell} ipython3
labyrinth_run = runs['labyrinth']
labyrinth_run.base.extras.set('morphology', 'labyrinth')

print(f'Tagged {labyrinth_run} with morphology=labyrinth')
```

You can later find this exact run by that tag with the `QueryBuilder`, without needing to remember its PK.

## Next steps

You've now turned the pipeline of Module 2 into a single, reusable workflow.
In {ref}`Module 3b <tutorial:module3b>`, WorkGraph's `Map` runs that same workflow over many inputs at once, as a single tracked, parallel workflow.

## Further reading

- AiiDA's workflow concepts in depth: {ref}`topics:workflows`
- `ShellJob` (the launcher used in the pipeline): {ref}`How to run shell commands <how-to:run-shell-commands>`
- Calcfunctions refresher: {ref}`topics:processes:functions`
- Running versus submitting processes: {ref}`topics:processes:usage:launching`
- WorkGraph documentation: [aiida-workgraph](https://aiida-workgraph.readthedocs.io)
