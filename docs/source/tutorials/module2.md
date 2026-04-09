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

(tutorial:module2)=
# Module 2: Interacting with Data

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module2.ipynb` {octicon}`download`
:::

## What you will learn

After this module, you will be able to:

- Run a parameter sweep using `aiida-shell` in a loop
- Understand the limitation of file-only provenance
- Write `@calcfunction`-decorated functions for input preparation and output parsing
- Use AiiDA's structured data types (`Dict`, `Float`) for queryable results
- Run a parameter sweep with richer provenance

## What you will not learn yet

You cannot yet chain steps into automated workflows or run them in parallel -- that comes in {ref}`Module 3 <tutorial:module3>`.

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

## Parameter sweep with `aiida-shell`

In {ref}`Module 1 <tutorial:module1>`, you ran a single simulation through `aiida-shell` and got back `SinglefileData` nodes -- the raw input and output files, tracked with provenance.

Now let's scale that up: scan the feed rate `F` and see how the pattern strength (`variance_V`) changes across a range of parameters.

```{code-cell} ipython3
# Sweep the feed rate F using aiida-shell, collecting results from each run.
import tempfile
from pathlib import Path

import numpy as np
import yaml

from aiida_shell import launch_shell_job

from include.constants import BASE_PARAMS, F_VALUES, SCRIPT_PATH

work_dir = Path(tempfile.mkdtemp())
sweep_results = []

for f_val in F_VALUES:
    input_path = work_dir / f'input_F{f_val}.yaml'
    input_path.write_text(yaml.dump(BASE_PARAMS | {'F': f_val}))

    results, calc_node = launch_shell_job(
        python_code,
        arguments='{script} --input {input} --output results.npz',
        nodes={'script': SCRIPT_PATH, 'input': input_path},
        outputs=['results.npz'],
    )

    with results['results_npz'].open(mode='rb') as fh:
        data = np.load(fh)
        sweep_results.append({
            'F': f_val,
            'variance_V': float(data['variance_V']),
            'U_final': data['U_final'],
            'V_final': data['V_final'],
        })

for r in sweep_results:
    print(f"F={r['F']:.3f}  variance(V)={r['variance_V']:.4e}")
```

```{code-cell} ipython3
# Plot variance_V vs F to show the phase transition.
%run -i include/plot_sweep.py
plot_transition_curve(
    [r['F'] for r in sweep_results],
    [r['variance_V'] for r in sweep_results],
)
```

The sharp drop in `variance_V` marks a **phase transition**: below it, the system forms rich spatial patterns; above it, the patterns dissolve.
Let's visualize representative fields from each side:

```{code-cell} ipython3
# Show U/V fields before and after the transition for visual comparison.
%run -i include/plot_fields.py

before = sweep_results[0]   # F = 0.040 — strong patterns
after = sweep_results[-1]   # F = 0.060 — weak patterns

print(f"Before transition (F={before['F']})")
plot_uv_fields(before['U_final'], before['V_final'])

print(f"After transition (F={after['F']})")
plot_uv_fields(after['U_final'], after['V_final'])
```

Every simulation is tracked by AiiDA -- we can inspect any of them with `verdi process show <PK>`.
But notice what we had to do to get the `variance_V` values: manually open each `.npz` file and extract the number.

The provenance looks like this for each run: **file in -> ShellJob -> file out**.
AiiDA knows *that* a result file was produced, but it can't see *what's inside* it.
If we wanted to find "all runs where `variance_V > 0.001`", we'd have to open every output file ourselves -- AiiDA's database can't help.

## Richer provenance with calcfunctions

### The idea

What if, instead of just files in and files out, we could register the simulation's inputs and outputs as **structured AiiDA data nodes**?

- The input parameters as a {py:class}`~aiida.orm.Dict` (queryable key-value pairs in the database)
- The output scalars as {py:class}`~aiida.orm.Float` nodes (directly searchable)

A {func}`@calcfunction <aiida.engine.processes.functions.calcfunction>` is the simplest way to do this.
It's a regular Python function with a decorator that makes AiiDA automatically:

1. Store all input nodes
2. Create a **process node** recording the computation
3. Store all output nodes
4. Link everything in the provenance graph

### Writing `prepare_input`

This calcfunction takes a `Dict` of parameters and produces the YAML input file that our simulation script expects:

```{code-cell} ipython3
# Define prepare_input: a calcfunction that converts a Dict to a YAML file.
import io

from aiida import engine, orm


@engine.calcfunction
def prepare_input(parameters):
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.get_dict())
    return orm.SinglefileData(io.BytesIO(content.encode()), filename='input.yaml')
```

:::{note}
Inside a `calcfunction`, all parameters are AiiDA data nodes -- not plain Python types.
That is why the function calls `parameters.get_dict()` to extract the dictionary.

When *calling* the function, AiiDA auto-serializes plain Python types for you: `prepare_input(orm.Dict(params))` and `prepare_input(params)` both work.
:::

### Writing `parse_output`

This calcfunction reads the `.npz` output file and extracts the scalar results as `Float` nodes:

```{code-cell} ipython3
# Define parse_output: a calcfunction that extracts scalars from the .npz file.
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

### Running the enriched pipeline

Now we chain the three steps: `prepare_input` -> `launch_shell_job` -> `parse_output`.
Each step is tracked, and the inputs/outputs are stored as structured, queryable nodes:

```{code-cell} ipython3
# Run the enriched pipeline: prepare_input → ShellJob → parse_output.
input_file = prepare_input(orm.Dict(BASE_PARAMS))

results, node = launch_shell_job(
    python_code,
    arguments='{script} --input {input} --output results.npz',
    nodes={'script': SCRIPT_PATH, 'input': input_file},
    outputs=['results.npz'],
)

parsed = parse_output(results['results_npz'])
print(f"variance(V) = {parsed['variance_V'].value:.4e}")
print(f"mean(V)     = {parsed['mean_V'].value:.4e}")
```

Let's look at the provenance graph:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
# Provenance graph now shows Dict in and Float out, not just opaque files.
%run -i include/plot_provenance.py
plot_provenance(node)
```

Compare this to the first sweep: the provenance now shows **Dict** going in and **Float** values coming out, not just opaque files.
AiiDA's database can now search these values directly.

### Parameter sweep with the enriched pipeline

Let's run the full sweep again, this time with structured data at every step:

```{code-cell} ipython3
# Re-run the full sweep with the enriched pipeline (structured data at every step).
enriched_results = []

for f_val in F_VALUES:
    input_file = prepare_input(BASE_PARAMS | {'F': f_val})

    results, calc_node = launch_shell_job(
        python_code,
        arguments='{script} --input {input} --output results.npz',
        nodes={'script': SCRIPT_PATH, 'input': input_file},
        outputs=['results.npz'],
    )

    parsed = parse_output(results['results_npz'])
    enriched_results.append({'F': f_val, 'variance_V': parsed['variance_V'].value})

for r in enriched_results:
    print(f"F={r['F']:.3f}  variance(V)={r['variance_V']:.4e}")
```

```{code-cell} ipython3
# Same transition curve — but now every point is backed by queryable AiiDA nodes.
plot_transition_curve(
    [r['F'] for r in enriched_results],
    [r['variance_V'] for r in enriched_results],
)
```

The plot looks the same -- but now every data point is backed by structured AiiDA nodes.
The `Dict` inputs and `Float` outputs live in the database, queryable and with full provenance linking them to the simulation that produced them.

```{code-cell} ipython3
# List all processes run in the last day.
%verdi process list -a -p 1
```

## Summary

In this module you learned to:

- **Run a parameter sweep** with `aiida-shell` in a loop (file in -> file out)
- **Recognize the limitation**: AiiDA can't query inside opaque files
- **Write calcfunctions** (`prepare_input`, `parse_output`) to convert between files and structured data
- **Build an enriched pipeline** with queryable `Dict` inputs and `Float` outputs

:::{seealso}
- {ref}`Topic: data types <topics:data_types>` -- full reference on AiiDA's data model
- {ref}`Topic: processes <topics:processes>` -- in-depth guide to calcfunctions and CalcJobs
:::

## Next steps

We now have a tracked pipeline with structured data -- but it's still a Python `for` loop.
If one step fails, the loop stops. There's no single "sweep" object to query, and no way to parallelize.
In {ref}`Module 3 <tutorial:module3>`, you'll wrap the pipeline into a **WorkGraph workflow** and turn the loop into a mapped workflow too.
