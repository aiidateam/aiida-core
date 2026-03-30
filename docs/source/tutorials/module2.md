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

- Understand AiiDA's built-in data types and when to use each one
- Store data explicitly in the AiiDA database
- Write `@calcfunction`-decorated functions for tracked in-process computations
- Build a multi-step pipeline: prepare inputs, run a simulation, parse outputs
- Run a parameter sweep with full provenance tracking

## What you will not learn yet

You cannot yet chain steps into automated workflows or run them in parallel -- that comes in {ref}`Module 3 <tutorial:module3>`.

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

## Part A: Data types

### What Module 1 produced

In {ref}`Module 1 <tutorial:module1>`, you ran the simulation through `aiida-shell` and got back `SinglefileData` nodes -- opaque binary files stored in AiiDA's repository.
This is fine for archival, but AiiDA can't search *inside* a `.npz` file.

To make results **queryable** and **reusable**, we need to extract the relevant quantities into structured AiiDA data types.

### AiiDA's built-in data types

AiiDA provides several data types for different kinds of scientific data:

| Data type | Python equivalent | Use for |
|-----------|-------------------|---------|
| {py:class}`~aiida.orm.Int` | `int` | Integer parameters |
| {py:class}`~aiida.orm.Float` | `float` | Scalar results (e.g., `variance_V`) |
| {py:class}`~aiida.orm.Str` | `str` | Labels, identifiers |
| {py:class}`~aiida.orm.Bool` | `bool` | Flags |
| {py:class}`~aiida.orm.List` | `list` | Ordered collections |
| {py:class}`~aiida.orm.Dict` | `dict` | Parameter sets, metadata |
| {py:class}`~aiida.orm.ArrayData` | `numpy.ndarray` | Grids, spectra, trajectories |
| {py:class}`~aiida.orm.SinglefileData` | file on disk | Raw files (any format) |

:::{tip}
**Rule of thumb**: Use the most specific type that fits.
`Float` for a single number, `Dict` for a parameter set, `ArrayData` for grids or spectra.
Reserve `SinglefileData` for files whose internal structure you don't need to query.
:::

### Storing data explicitly

Let's store simulation parameters as AiiDA nodes:

```{code-cell} ipython3
from aiida import orm

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

parameters = orm.Dict(params)
parameters.store()
parameters
```

The node now has a **PK** (primary key, unique within this database) and a **UUID** (universally unique identifier).
We can inspect it with the `verdi` CLI:

```{code-cell} ipython3
%verdi node show {parameters.pk}
```

We can also retrieve the stored dictionary contents through the Python API:

```{code-cell} ipython3
parameters.get_dict()
```

Similarly, we can store individual scalar values:

```{code-cell} ipython3
feed_rate = orm.Float(0.04)
feed_rate.store()
print(f"Stored Float node: PK={feed_rate.pk}, value={feed_rate.value}")
```

## Part B: Calcfunctions and parameter sweep

### Parameter sweep without AiiDA

Before introducing AiiDA tools, let's see what a parameter sweep looks like with plain Python.
We want to scan the feed rate `F` and see how the pattern strength (`variance_V`) changes:

```{code-cell} ipython3
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import yaml

script_path = Path('include/reaction-diffusion.py').resolve()
work_dir = Path(tempfile.mkdtemp())

f_values = [0.02, 0.03, 0.035, 0.04, 0.045, 0.05, 0.06]
variances = []

for f_val in f_values:
    sweep_params = params.copy()
    sweep_params['F'] = f_val

    input_path = work_dir / f'input_F{f_val}.yaml'
    input_path.write_text(yaml.dump(sweep_params))
    output_path = work_dir / f'results_F{f_val}.npz'

    result = subprocess.run(
        ['python3', str(script_path), str(input_path), '--output', str(output_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        data = np.load(output_path)
        variances.append(float(data['variance_V']))
    else:
        variances.append(0.0)  # Failed — no pattern

print("F values:  ", [f"{v:.3f}" for v in f_values])
print("Variances: ", [f"{v:.4e}" for v in variances])
```

```{code-cell} ipython3
%run -i include/plot_sweep.py
plot_transition_curve(f_values, variances)
```

This works, but the results are just Python variables.
There is no record of which parameters produced which result, no provenance, and no way to query or reproduce it later.

### Introducing `@calcfunction`

A {func}`@calcfunction <aiida.engine.processes.functions.calcfunction>` is the simplest way to make a Python function tracked by AiiDA.
By adding the decorator, AiiDA automatically:

1. Stores all input nodes (if not already stored)
2. Creates a **process node** that records the computation
3. Stores all output nodes
4. Links everything in a **provenance graph**

Let's start with a simple in-process version using the `simulate()` function:

```{code-cell} ipython3
%run -i include/simulate.py
```

```{code-cell} ipython3
from aiida import engine


@engine.calcfunction
def run_simulation(parameters):
    """Run the Gray-Scott simulation, tracked by AiiDA."""
    result = simulate(parameters.get_dict())
    return {
        'variance_V': orm.Float(result['variance_V']),
        'mean_V': orm.Float(result['mean_V']),
    }
```

:::{note}
Inside a `calcfunction`, all parameters are AiiDA data nodes -- not plain Python types.
That is why the function calls `parameters.get_dict()` to extract the dictionary, and returns `orm.Float(...)` rather than a bare float.

When *calling* the function, however, AiiDA auto-serializes plain Python types for you: `run_simulation(orm.Dict(params))` and `run_simulation(params)` both work -- AiiDA wraps the plain `dict` into an `orm.Dict` automatically.
:::

```{code-cell} ipython3
result = run_simulation(orm.Dict(params))
print(f"variance(V) = {result['variance_V'].value:.4e}")
print(f"mean(V)     = {result['mean_V'].value:.4e}")
```

The result values are now stored as `Float` nodes in AiiDA -- queryable, with full provenance.

### Writing `prepare_input`

To use the command-line script (as we did in Module 1 with `aiida-shell`), we need to convert our `Dict` parameters into a YAML file.
Let's write a calcfunction for this:

```{code-cell} ipython3
@engine.calcfunction
def prepare_input(parameters):
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    import io

    content = yaml.dump(parameters.get_dict())
    return orm.SinglefileData(io.BytesIO(content.encode()), filename='input.yaml')
```

```{code-cell} ipython3
input_file = prepare_input(orm.Dict(params))
print(f"Created: {input_file.__class__.__name__} (PK={input_file.pk})")
print(f"Content preview:\n{input_file.get_content()[:200]}")
```

### Writing `parse_output`

After the simulation runs, we need to extract the structured data from the `.npz` output file:

```{code-cell} ipython3
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

Now we can combine all the pieces: prepare the input, run via `aiida-shell`, and parse the output.
Each step is tracked by AiiDA:

```{code-cell} ipython3
from aiida_shell import launch_shell_job

# Step 1: Prepare input file
input_file = prepare_input(orm.Dict(params))

# Step 2: Run the simulation via aiida-shell
results, node = launch_shell_job(
    python_code,
    arguments='{script} {input} --output results.npz',
    nodes={
        'script': script_path,
        'input': input_file,
    },
    outputs=['results.npz'],
)

print(f"ShellJob PK: {node.pk}, exit status: {node.exit_status}")

# Step 3: Parse the output
parsed = parse_output(results['results_npz'])
print(f"variance(V) = {parsed['variance_V'].value:.4e}")
print(f"mean(V)     = {parsed['mean_V'].value:.4e}")
```

Let's look at the provenance graph of the full pipeline:

```{code-cell} ipython3
---
mystnb:
    image:
        align: center
        width: 500px
    figure:
        caption: "Provenance graph of the enriched pipeline: prepare_input -> ShellJob -> parse_output."
        name: fig_module2_pipeline
---
%run -i include/plot_provenance.py
plot_provenance(node)
```

### Parameter sweep with calcfunctions

Now let's run the parameter sweep with the full tracked pipeline.
Every step is recorded by AiiDA:

```{code-cell} ipython3
f_values_sweep = [0.02, 0.03, 0.035, 0.04, 0.045, 0.05, 0.06]
sweep_results = []

for f_val in f_values_sweep:
    sweep_params = params.copy()
    sweep_params['F'] = f_val

    # Full pipeline: prepare -> run -> parse
    input_file = prepare_input(orm.Dict(sweep_params))
    results, calc_node = launch_shell_job(
        python_code,
        arguments='{script} {input} --output results.npz',
        nodes={
            'script': script_path,
            'input': input_file,
        },
        outputs=['results.npz'],
    )

    if calc_node.is_finished_ok:
        parsed = parse_output(results['results_npz'])
        sweep_results.append({
            'F': f_val,
            'variance_V': parsed['variance_V'].value,
            'pk': calc_node.pk,
        })
    else:
        sweep_results.append({
            'F': f_val,
            'variance_V': 0.0,
            'pk': calc_node.pk,
        })
        print(f"F={f_val}: failed with exit status {calc_node.exit_status}")

for r in sweep_results:
    print(f"F={r['F']:.3f}  variance(V)={r['variance_V']:.4e}  (PK={r['pk']})")
```

Now plot the transition curve -- this time built from AiiDA-tracked data:

```{code-cell} ipython3
plot_transition_curve(
    [r['F'] for r in sweep_results],
    [r['variance_V'] for r in sweep_results],
)
```

Every data point in this plot is connected to a full provenance chain in AiiDA: which parameters were used, which script ran, what the raw output was, and how the parsed values were extracted.

```{code-cell} ipython3
%verdi process list -a -p 1
```

## Summary

In this module you learned to:

- **Use AiiDA data types** (`Dict`, `Float`, `SinglefileData`) to store scientific data with provenance
- **Write calcfunctions** to make Python functions tracked by AiiDA
- **Build a multi-step pipeline**: `prepare_input` -> `launch_shell_job` -> `parse_output`
- **Run a parameter sweep** with full provenance tracking for every data point

:::{seealso}
- {ref}`Topic: data types <topics:data_types>` -- full reference on AiiDA's data model
- {ref}`Topic: processes <topics:processes>` -- in-depth guide to calcfunctions and CalcJobs
:::

## Next steps

We can now run tracked simulations and extract structured data. But our sweep is still a Python `for` loop -- if one step fails, we lose everything. In {ref}`Module 3 <tutorial:module3>`, you'll learn how to wrap this pipeline into a **WorkGraph workflow** that handles data flow, parallelism, and provenance hierarchy automatically.
