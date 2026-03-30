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
- Build a linear workflow chain with WorkGraph
- Use `shelljob` tasks in a WorkGraph
- Run a parameter sweep as a workflow using Map
- Inspect hierarchical provenance graphs

## What you will not learn yet

Error handling, automatic retries, and remote HPC submission are covered in future modules.

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

In {ref}`Module 2 <tutorial:module2>`, you ran a parameter sweep as a Python `for` loop: prepare input, run simulation, parse output -- for each parameter value.
This works, but has important limitations:

- If one step fails, the whole loop stops
- There's no hierarchical provenance -- each step is independent in AiiDA's graph
- You can't easily parallelize the runs
- There's no single "sweep" object you can query or inspect

A **workflow** solves all of these: you define the steps and their connections once, and AiiDA handles execution, data passing, error recovery, and provenance tracking.

:::{note}
AiiDA offers two workflow systems: **WorkGraph** (declarative, graph-based) and **WorkChain** (imperative, class-based).
This tutorial uses WorkGraph -- it's more intuitive for composing tasks and scales naturally to complex graphs.
:::

## Part 1: Linear chain

### WorkGraph basics

A {class}`~aiida_workgraph.WorkGraph` is a directed graph of **tasks** connected by **links**.
Each task wraps a function (calcfunction, CalcJob, or another workflow) and declares its inputs and outputs.

Let's build a simple workflow that chains our three steps from Module 2: `prepare_input` -> `ShellJob` -> `parse_output`.

First, let's define the calcfunctions we need:

```{code-cell} ipython3
import io
from pathlib import Path

import numpy as np
import yaml

from aiida import engine, orm

script_path = Path('include/reaction-diffusion.py').resolve()


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

### Building the simulation workflow

Now let's wire these into a WorkGraph:

```{code-cell} ipython3
:tags: ["skip-execution"]

from aiida_workgraph import WorkGraph

wg = WorkGraph('gray_scott_pipeline')

# Task 1: prepare the input file
prepare_task = wg.add_task(prepare_input, name='prepare_input')

# Task 2: run the simulation via aiida-shell's ShellJob
sim_task = wg.add_task(
    'aiida_shell.launch_shell_job',
    name='simulate',
    command=python_code,
    arguments='{script} {input} --output results.npz',
    nodes={
        'script': script_path,
    },
    outputs=['results.npz'],
)

# Task 3: parse the output
parse_task = wg.add_task(parse_output, name='parse_output')

# Link the tasks: prepare_input -> simulate -> parse_output
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

params = {
    'grid_size': 64,
    'du': 0.16,
    'dv': 0.08,
    'F': 0.04,
    'k': 0.065,
    'dt': 1.0,
    'n_steps': 3000,
    'seed': 42,
}

wg.run(inputs={'prepare_input': {'parameters': orm.Dict(params)}})

print(f"WorkGraph PK: {wg.process.pk}")
print(f"State: {wg.state}")
```

The WorkGraph groups all three steps under a single workflow node.
Let's inspect the hierarchy:

```{code-cell} ipython3
:tags: ["skip-execution"]

%verdi process status {wg.process.pk}
```

```{code-cell} ipython3
:tags: ["skip-execution"]

%verdi process list -a -p 1
```

The provenance graph now shows a **hierarchical** structure -- the workflow contains the individual steps, and the data flows between them:

```{code-cell} ipython3
:tags: ["skip-execution"]

%run -i include/plot_provenance.py
plot_provenance(wg.process)
```

Compare this to Module 2's flat provenance: instead of disconnected steps, the workflow clearly shows that `prepare_input`, `simulate`, and `parse_output` are part of a single logical operation.

## Part 2: Parameter sweep as workflow

### Using Map

WorkGraph's `Map` feature lets you run the same sub-workflow over multiple input values -- like a parallel `for` loop, but with full provenance:

```{code-cell} ipython3
:tags: ["skip-execution"]

from aiida_workgraph import WorkGraph

f_values = [0.02, 0.03, 0.035, 0.04, 0.045, 0.05, 0.06]

wg_sweep = WorkGraph('gray_scott_sweep')

# Create a parameter set for each F value
base_params = {
    'grid_size': 64,
    'du': 0.16, 'dv': 0.08,
    'k': 0.065,
    'dt': 1.0, 'n_steps': 3000,
    'seed': 42,
}

param_nodes = []
for f_val in f_values:
    p = base_params.copy()
    p['F'] = f_val
    param_nodes.append(orm.Dict(p))

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

### Running the sweep workflow

```{code-cell} ipython3
:tags: ["skip-execution"]

# Once the Map is set up:
# wg_sweep.run()
# print(f"Sweep WorkGraph PK: {wg_sweep.process.pk}")
```

### Analyzing results

After the sweep completes, all results are accessible through AiiDA's provenance graph:

```{code-cell} ipython3
:tags: ["skip-execution"]

# Extract results from the workflow outputs
# sweep_results = []
# for task_name, task in wg_sweep.tasks.items():
#     if 'parse_output' in task_name:
#         variance = task.outputs.variance_V.value
#         # ... collect F value and variance
#
# %run -i include/plot_sweep.py
# plot_transition_curve(f_values, variances)
```

The key advantage: each point in the sweep is a tracked workflow with hierarchical provenance.
You can trace any result back to its exact inputs, and the sweep itself is a single queryable object.

## Branching (teaser)

WorkGraph also supports **conditional logic** -- running different tasks based on intermediate results.
For example, you could skip the parse step if the simulation failed, or run additional analysis only for interesting parameter values.

```python
# Conceptual example — syntax may differ
if_task = wg.add_task(If, condition=lambda result: result['variance_V'] > 1e-6)
if_task.then(detailed_analysis_task)
if_task.otherwise(log_failure_task)
```

This will be covered in more detail in future modules on error handling and advanced workflows.

## Summary

In this module you learned to:

- **Build** a linear workflow with WorkGraph: `prepare_input` -> `simulate` -> `parse_output`
- **Run** the workflow and inspect hierarchical provenance
- **Map** a workflow over multiple inputs for parameter sweeps
- **Compare** flat (Module 2) vs hierarchical (Module 3) provenance

:::{seealso}
- [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io) -- full reference for WorkGraph
- {ref}`Topic: workflows <topics:workflows>` -- AiiDA workflow concepts in depth
:::

## Next steps

You now have a complete pipeline from running simulations to building workflows.
Future modules will cover error handling, remote HPC submission, and advanced workflow patterns.
