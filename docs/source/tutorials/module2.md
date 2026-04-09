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
# Sweep the feed rate F using aiida-shell.
import tempfile
from pathlib import Path

import yaml

from aiida_shell import launch_shell_job

from include.constants import BASE_PARAMS, F_VALUES, SCRIPT_PATH

work_dir = Path(tempfile.mkdtemp(prefix='aiida_tut_m2_'))
calc_nodes = []

for f_val in F_VALUES:
    input_path = work_dir / f'input_F{f_val}.yaml'
    input_path.write_text(yaml.dump(BASE_PARAMS | {'F': f_val}))

    results, calc_node = launch_shell_job(
        python_code,
        arguments='{script} --input {input} --output results.npz',
        nodes={'script': SCRIPT_PATH, 'input': input_path},
        outputs=['results.npz'],
    )
    calc_nodes.append((f_val, calc_node))
```

```{code-cell} ipython3
# Extract and print results from each run.
import numpy as np

sweep_results = []

for f_val, calc_node in calc_nodes:
    with calc_node.outputs.results_npz.open(mode='rb') as fh:
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
As in {ref}`Module 0 <tutorial:module0>`, let's visualize representative fields from each side:

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

Every simulation is tracked by AiiDA -- we can inspect any of them:

```{code-cell} ipython3
# List all processes run so far in this profile.
%verdi process list -a
```

:::{important}
Notice what we had to do to get the `variance_V` values: manually open each `.npz` file and extract the number.

The provenance looks like this for each run: **file in &rarr; ShellJob &rarr; file out**.
AiiDA knows *that* a result file was produced, but it can't see *what's inside* it.
If we wanted to find "all runs where `variance_V > 0.001`", we'd have to open every output file ourselves &mdash; AiiDA's database can't help.
:::

## Richer provenance with calcfunctions

### The idea

What if, instead of just files in and files out, we could register the simulation's inputs and outputs as **structured AiiDA data nodes**?

- The input parameters as a {py:class}`~aiida.orm.Dict` (queryable key-value pairs in the database)
- The output scalars as {py:class}`~aiida.orm.Float` nodes (directly searchable)

:::{tip}
`orm` stands for **Object-Relational Mapping**: it lets you work with database-stored objects as regular Python classes.
AiiDA's {mod}`~aiida.orm` module provides data types like `Dict`, `Float`, `Int`, `Str`, `List`, and `SinglefileData` that are automatically persisted in the database and linked in the provenance graph.
:::

<!-- TODO: Add a "Built-in data types" subsection with a table of the most common types
     (Dict, Float, Int, Str, List, ArrayData, XyData, SinglefileData) and when to use each.
     Also mention richer 2D data types beyond files (e.g. ArrayData, XyData).
     From meeting notes: "filters & 2D data types beyond files". -->

<!-- TODO: Add an "Extras" subsection or note — show how to attach arbitrary metadata
     (extras) to nodes for tagging, filtering, and organizing results.
     From meeting notes: "possibly introduce Extras here". -->

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
def prepare_input(parameters: orm.Dict) -> orm.SinglefileData:
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.get_dict())
    return orm.SinglefileData(io.BytesIO(content.encode()), filename='input.yaml')
```

:::{note}
Inside a `calcfunction`, all parameters are AiiDA data nodes -- not plain Python types.
That is why the function calls `parameters.get_dict()` to extract the dictionary.

When *calling* the function, AiiDA auto-serializes plain Python types for you: `prepare_input(orm.Dict(params))` and `prepare_input(params)` both work.

You could also pass each parameter as a separate `orm.Float`/`orm.Int` node for finer-grained provenance, but a single `Dict` is the common pattern and its attributes are still queryable via the `QueryBuilder`.
:::

### Writing `parse_output`

This calcfunction reads the `.npz` output file and extracts the scalar results as `Float` nodes:

```{code-cell} ipython3
# Define parse_output: a calcfunction that extracts scalars from the .npz file.
@engine.calcfunction
def parse_output(output_file: orm.SinglefileData) -> dict[str, orm.Float]:
    """Extract variance_V and mean_V from a SinglefileData .npz file."""
    with output_file.open(mode='rb') as f:
        data = np.load(f)
        return {
            'variance_V': orm.Float(float(data['variance_V'])),
            'mean_V': orm.Float(float(data['mean_V'])),
        }
```

:::{note}
A calcfunction can return either a single data node or a plain `dict` mapping string labels to data nodes.
When returning a dict, AiiDA registers each value as a named output on the process node, accessible via `node.outputs.<label>`.
:::

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
These values can now be searched directly in AiiDA's database.

### Parameter sweep with the enriched pipeline

Let's run the full sweep again, this time with structured data at every step:

```{code-cell} ipython3
# Re-run the full sweep with the enriched pipeline (structured data at every step).
enriched_nodes = []

for f_val in F_VALUES:
    input_file = prepare_input(BASE_PARAMS | {'F': f_val})

    results, calc_node = launch_shell_job(
        python_code,
        arguments='{script} --input {input} --output results.npz',
        nodes={'script': SCRIPT_PATH, 'input': input_file},
        outputs=['results.npz'],
    )

    parsed = parse_output(results['results_npz'])
    enriched_nodes.append((f_val, parsed))
```

Now the payoff: instead of manually opening `.npz` files, the results are stored as `Float` nodes that we can access directly through the provenance graph:

```{code-cell} ipython3
# Access the structured results directly -- no file handling needed.
for f_val, parsed in enriched_nodes:
    print(f"F={f_val:.3f}  variance(V)={parsed['variance_V'].value:.4e}")
```

```{code-cell} ipython3
# Plot the transition curve from the structured AiiDA data.
plot_transition_curve(
    [f_val for f_val, _ in enriched_nodes],
    [parsed['variance_V'].value for _, parsed in enriched_nodes],
)
```

Compare this to the first sweep where we had to manually open every `.npz` file.
Now the `Dict` inputs and `Float` outputs live in the database with full provenance.

<!-- TODO: Add "Grouping results" subsection — collect all sweep runs into an AiiDA Group,
     show `verdi group list`, `verdi group show`. Groups let you organize related
     calculations (e.g. "all F-sweep runs") for later retrieval.
     From meeting notes: "groups; AiiDA manages your FS". -->

<!-- TODO: Consider adding a benchmark/speed note on *result retrieval* at scale.
     E.g. for 1k parameter values: without AiiDA you'd need 1k file opens + numpy loads
     just to find interesting runs. With AiiDA, the parsed Float values live in the database
     and can be queried instantly via QueryBuilder.
     (The file I/O during parse_output still happens, but in real-world scenarios
     that runs asynchronously in the background via AiiDA daemon workers.)
     From meeting notes: "show speed impact (benchmark?)". -->

:::{tip}
AiiDA's {class}`~aiida.orm.QueryBuilder` can search these structured nodes directly.
For example, to find all runs where `variance_V > 0.001`:

```python
qb = orm.QueryBuilder()
qb.append(orm.Float, filters={'attributes.value': {'>': 0.001}})
```

See the {ref}`querying how-to guide <how-to:query>` for more.
:::

```{code-cell} ipython3
# List all processes run so far.
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

We now have a tracked pipeline with structured data -- but it's still a Python `for` loop that runs each step in a blocking manner.
If one step fails, the loop stops. There's no single "sweep" object to query, and no way to run steps in parallel.
In {ref}`Module 3 <tutorial:module3>`, you'll wrap the pipeline into a **WorkGraph workflow** and turn the loop into a mapped workflow too.
