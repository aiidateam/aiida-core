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

- Understand why workflows matter for reproducible science
- Build a linear workflow with WorkGraph (grouping the pipeline from Module 2 into one process)
- Turn a Python for-loop into a mapped workflow
- Inspect hierarchical provenance graphs

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

In {ref}`Module 2 <tutorial:module2>`, you built a three-step pipeline (`prepare_input` -> ShellJob -> `parse_output`) and ran it in a Python `for` loop.
This has important limitations:

- **No grouping**: each step is a separate process in AiiDA -- there's no single "simulation pipeline" object
- **No hierarchy**: the provenance graph is flat; you can't tell which steps belong together
- **No parallelism**: the loop runs sequentially; one failure stops everything
- **No single entry point**: you can't re-run "the same workflow" with different parameters

A **workflow** solves all of these.
You define the steps and their connections once, and AiiDA handles execution, data passing, and provenance tracking -- grouping everything under a single workflow node.

:::{note}
AiiDA offers two workflow systems: **WorkGraph** (declarative, graph-based) and **WorkChain** (imperative, class-based).
This tutorial uses WorkGraph -- it's more intuitive for composing tasks and scales naturally to complex graphs.
:::

## Wrapping the pipeline as a workflow

### Defining the tasks

These are the same calcfunctions from Module 2 -- they convert between files and structured AiiDA data:

```{code-cell} ipython3
# Re-define the calcfunctions from Module 2 (prepare_input and parse_output).
import io

import numpy as np
import yaml

from aiida import engine, orm

from include.constants import BASE_PARAMS, F_VALUES, SCRIPT_PATH


@engine.calcfunction
def prepare_input(parameters):
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.get_dict())
    return orm.SinglefileData(io.BytesIO(content.encode()), filename='input.yaml')


@engine.calcfunction
def parse_output(output_file):
    """Extract variance_V and mean_V from a SinglefileData .npz file."""
    with output_file.open(mode='rb') as f:
        data = np.load(f)
        return {
            'variance_V': orm.Float(float(data['variance_V'])),
            'mean_V': orm.Float(float(data['mean_V'])),
        }
```

### Building the WorkGraph

A {class}`~aiida_workgraph.WorkGraph` is a directed graph of **tasks** connected by **links**.
Let's wire our three steps into a single workflow:

```{code-cell} ipython3
:tags: ["skip-execution"]

from aiida_workgraph import WorkGraph

wg = WorkGraph('gray_scott_pipeline')

# Task 1: prepare the input file (Dict -> SinglefileData)
prepare_task = wg.add_task(prepare_input, name='prepare_input')

# Task 2: run the simulation via aiida-shell's ShellJob
sim_task = wg.add_task(
    'aiida_shell.launch_shell_job',
    name='simulate',
    command=python_code,
    arguments='{script} {input} --output results.npz',
    nodes={'script': SCRIPT_PATH},
    outputs=['results.npz'],
)

# Task 3: parse the output (SinglefileData -> Float, Float)
parse_task = wg.add_task(parse_output, name='parse_output')

# Link the tasks together
wg.add_link(prepare_task.outputs.result, sim_task.inputs.nodes__input)
wg.add_link(sim_task.outputs.results_npz, parse_task.inputs.output_file)
```

:::{note}
The exact API for adding `shelljob` tasks and linking them in WorkGraph may differ depending on the `aiida-workgraph` version.
Consult the [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io) for the latest syntax.
:::

### Running and inspecting

```{code-cell} ipython3
:tags: ["skip-execution"]

# Run the WorkGraph and inspect its state.
wg.run(inputs={'prepare_input': {'parameters': orm.Dict(BASE_PARAMS)}})

print(f"WorkGraph PK: {wg.process.pk}")
print(f"State: {wg.state}")
```

The three steps are now grouped under a single workflow node.
Let's inspect the hierarchy:

```{code-cell} ipython3
:tags: ["skip-execution"]

# Show the hierarchical process tree of the workflow.
%verdi process status {wg.process.pk}
```

The provenance graph now shows a **hierarchical** structure -- the workflow contains the individual steps:

```{code-cell} ipython3
:tags: ["skip-execution"]

# Visualize the hierarchical provenance graph of the workflow.
%run -i include/plot_provenance.py
plot_provenance(wg.process)
```

Compare this to Module 2's flat provenance: instead of disconnected steps, the workflow clearly shows that `prepare_input`, `simulate`, and `parse_output` are part of a single logical operation.

## Turning the for-loop into a workflow

### The problem with loops

In Module 2, the parameter sweep was a Python `for` loop calling the pipeline for each `F` value.
But a `for` loop is not an AiiDA process -- it doesn't show up in the provenance, can't be inspected with `verdi`, and can't recover from failures.

### Using Map

WorkGraph's `Map` feature lets you run the same sub-workflow over multiple input values -- like a parallel `for` loop, but as a single AiiDA workflow with full provenance:

```{code-cell} ipython3
:tags: ["skip-execution"]

wg_sweep = WorkGraph('gray_scott_sweep')

param_nodes = [orm.Dict(BASE_PARAMS | {'F': f_val}) for f_val in F_VALUES]

# TODO: The exact Map API depends on the aiida-workgraph version.
# The concept: map the pipeline (prepare_input -> simulate -> parse_output)
# over the list of parameter sets.
# Consult https://aiida-workgraph.readthedocs.io for the current Map syntax.
```

:::{admonition} Implementation note
:class: warning

The exact `Map` API in `aiida-workgraph` is under active development.
The concept is stable: you define a sub-workflow and map it over a list of inputs.
The code above shows the *intent* -- check the [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io) for the current syntax.
:::

### Running and inspecting the sweep

```{code-cell} ipython3
:tags: ["skip-execution"]

# Once the Map is set up:
# wg_sweep.run()
# print(f"Sweep WorkGraph PK: {wg_sweep.process.pk}")
# %verdi process status {wg_sweep.process.pk}
```

The sweep is now a single workflow node containing all individual pipeline runs.
You can query it, inspect it, and see the full hierarchical provenance:

```{code-cell} ipython3
:tags: ["skip-execution"]

# %run -i include/plot_provenance.py
# plot_provenance(wg_sweep.process)
```

### Analyzing results

```{code-cell} ipython3
:tags: ["skip-execution"]

# Extract results from the workflow outputs and plot:
# %run -i include/plot_sweep.py
# plot_transition_curve(f_values, variances)
```

The key advantage: the entire sweep -- every pipeline run, every input, every output -- lives under a single workflow node in AiiDA's provenance graph.

## Branching (teaser)

WorkGraph also supports **conditional logic** -- running different tasks based on intermediate results.
For example, you could skip the parse step if the simulation failed, or run additional analysis only for interesting parameter values.

```python
# Conceptual example — syntax may differ
if_task = wg.add_task(If, condition=lambda result: result['variance_V'] > 1e-6)
if_task.then(detailed_analysis_task)
if_task.otherwise(log_failure_task)
```

More advanced workflow patterns (If/While control flow, error handlers) will be covered in future modules.

## Summary

In this module you learned to:

- **Wrap a multi-step pipeline** into a single WorkGraph workflow
- **Turn a Python for-loop** into a mapped workflow with `Map`
- **Inspect hierarchical provenance** -- workflows grouping their child processes
- **Compare** flat (Module 2) vs hierarchical (Module 3) provenance

:::{seealso}
- [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io) -- full reference for WorkGraph
- {ref}`Topic: workflows <topics:workflows>` -- AiiDA workflow concepts in depth
:::

## Next steps

You now have a complete pipeline from running simulations to building workflows.
Future modules will cover error handling, remote HPC submission, and advanced workflow patterns.
