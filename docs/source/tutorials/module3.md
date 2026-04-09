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
# Module 3: Writing Simple Workflows

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module3.ipynb` {octicon}`download`
:::

## What you will learn

After this module, you will be able to:

- Define a reusable workflow with `@task.graph` and `shelljob`
- Run the workflow and inspect hierarchical provenance
- Turn a Python for-loop into a mapped workflow with `Map`

## What you will not learn yet

Error handling, automatic retries, and remote HPC submission are covered in future modules.

## Setup

This module requires an AiiDA profile and the `python_code` variable (see {ref}`Module 1 <tutorial:module1>` for details on the setup cell).

```{code-cell} ipython3
:tags: ["hide-cell"]

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

## Setup

```{code-cell} ipython3
from aiida import orm

from aiida_workgraph import WorkGraph, task, shelljob, spec, Map

from include.constants import BASE_PARAMS, F_VALUES, SCRIPT_PATH
from include.tasks import prepare_input, parse_output
```

We reuse the `prepare_input` and `parse_output` calcfunctions from {ref}`Module 2 <tutorial:module2>` ({download}`include/tasks.py`).

To use them inside a `@task.graph` definition, we wrap them with `task()`.
This turns them into WorkGraph task handles that return output sockets (e.g., `.result`) instead of AiiDA nodes directly, which is how WorkGraph wires tasks together:

```{code-cell} ipython3
# Wrap the calcfunctions so they return task handles inside @task.graph().
prepare_input = task(prepare_input)
parse_output = task(parse_output)

# Convert the script path to a SinglefileData node.
# WorkGraph serializes all inputs, so plain Path objects must be wrapped.
script_node = orm.SinglefileData(SCRIPT_PATH)
```

## Building the workflow

A {class}`~aiida_workgraph.WorkGraph` is a directed graph of **tasks** connected by **links**.
We use the `@task.graph` decorator to define our three-step pipeline as a reusable workflow:

```{code-cell} ipython3

@task.graph()
def gray_scott_pipeline(
    parameters: orm.Dict,
    command: orm.AbstractCode,
    script: orm.SinglefileData,
) -> spec.namespace(variance_V=float, mean_V=float):
    """Prepare input, run simulation, parse output."""
    input_file = prepare_input(parameters=parameters).result
    sim = shelljob(
        command=command,
        arguments=['{script}', '--input', '{input}', '--output', 'results.npz'],
        nodes={'script': script, 'input': input_file},
        outputs=['results.npz'],
    )
    return parse_output(output_file=sim.results_npz)
```

The `@task.graph` decorator turns `gray_scott_pipeline` into a reusable sub-workflow.
Calling it inside a `with WorkGraph()` block registers a task; calling `.build()` creates a standalone WorkGraph.

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

WorkGraph's {class}`~aiida_workgraph.Map` lets you run the same sub-workflow over multiple input values -- like a parallel `for` loop, but as a single AiiDA workflow with full provenance:

```{code-cell} ipython3

# Create a Dict node for each F value.
param_nodes = {f'F_{f_val}': orm.Dict(BASE_PARAMS | {'F': f_val}) for f_val in F_VALUES}

with WorkGraph('gray_scott_sweep') as wg_sweep:
    # Generate the parameter nodes as a dynamic namespace.
    with Map(param_nodes) as map_zone:
        result = gray_scott_pipeline(
            parameters=map_zone.item.value,
            command=python_code,
            script=script_node,
        )
        map_zone.gather({'variance_V': result.variance_V, 'mean_V': result.mean_V})

wg_sweep.run()
```

:::{note}
`Map` iterates over a dictionary of inputs. For each entry, it runs the sub-workflow with that entry's value, then gathers the specified outputs into collections accessible via `map_zone.outputs`.
:::

### Running and inspecting the sweep

```{code-cell} ipython3

print(f"Sweep WorkGraph PK: {wg_sweep.process.pk}")
%verdi process status {wg_sweep.process.pk}
```

The sweep is now a single workflow node containing all individual pipeline runs.
The provenance graph shows the full hierarchy:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
%run -i include/plot_provenance.py
plot_provenance(wg_sweep.process)
```

### Analyzing results

```{code-cell} ipython3

# Extract results from the Map outputs and plot.
%run -i include/plot_sweep.py

variances = map_zone.outputs.variance_V
plot_transition_curve(
    list(F_VALUES),
    [variances[key].value for key in sorted(variances)],
)
```

The key advantage: the entire sweep -- every pipeline run, every input, every output -- lives under a single workflow node in AiiDA's provenance graph.

## Control flow (teaser)

WorkGraph also supports **conditional logic** and **loops** -- running different tasks based on intermediate results.
For example, you could skip the parse step if the simulation failed, or repeat a simulation with refined parameters:

```python
from aiida_workgraph import If, While

with WorkGraph('conditional_example') as wg:
    result = some_task(x=x)
    with If(result.converged) as if_zone:
        detailed_analysis(data=result.output)
```

More advanced workflow patterns (If/While control flow, error handlers) will be covered in future modules.

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
