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
# Module 2: Structured data and calcfunctions

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module2.ipynb` {octicon}`download`
:::

:::{note}
This module reuses the tutorial profile and the `python_code` object created in {ref}`Module 1 <tutorial:module1>`. If you are following along locally, run that module first. To use your own profile instead, replace the setup cell at the top of the downloaded notebook with:

```python
from aiida import load_profile

load_profile()
```
:::

## What you will learn

After this module, you will be able to:

- Launch many tracked calculations programmatically
- Use AiiDA's structured data types to obtain queryable results
- Add input preparation and output parsing as tracked Python steps to the simulation's provenance

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

## Running many calculations with `aiida-shell`

In {ref}`Module 1 <tutorial:module1>`, you ran a single simulation through `aiida-shell` and got back `SinglefileData` nodes: the raw input and output files, tracked with provenance.

Let's start varying our simulation parameters: scan the feed rate `F` and see how the pattern strength (`variance_V`) changes across a range of values.

```{code-cell} ipython3
# Sweep the feed rate F using aiida-shell.
import tempfile
from pathlib import Path

import yaml

from aiida_shell import launch_shell_job

from include.constants import BASE_PARAMS, F_VALUES, SCRIPT_PATH

work_dir = Path(tempfile.mkdtemp(prefix='aiida_tutorial_m2_'))
calc_nodes = []

for f_val in F_VALUES:
    input_path = work_dir / (f'input_F{f_val:.3f}'.replace('.', '_') + '.yaml')
    input_path.write_text(yaml.dump(BASE_PARAMS | {'F': f_val}))

    results, calc_node = launch_shell_job(
        python_code,
        arguments='{script} --input {input} --output results.yaml',
        nodes={'script': SCRIPT_PATH, 'input': input_path},
        outputs=['results.yaml'],
    )
    calc_nodes.append((f_val, calc_node))
```

The output of each run is a `SinglefileData` YAML node. To get the `variance_V` numbers for plotting, we open and parse each file:

```{code-cell} ipython3
# Extract and print results from each run.
import yaml

sweep_results = []

for f_val, calc_node in calc_nodes:
    with calc_node.outputs.results_yaml.open(mode='r') as fh:
        data = yaml.safe_load(fh)
        sweep_results.append({
            'F': f_val,
            'variance_V': data['variance_V'],
        })

for r in sweep_results:
    print(f"F={r['F']:.3f}  variance(V)={r['variance_V']:.4e}")
```

```{code-cell} ipython3
# Plot variance_V vs F to show the phase transition.
from include.plotting import plot_transition_curve

plot_transition_curve(
    [r['F'] for r in sweep_results],
    [r['variance_V'] for r in sweep_results],
)
```

The sharp drop in `variance_V` marks a **phase transition**: below it, the system forms rich spatial patterns; above it, the patterns dissolve.

::::{grid} 2
:gutter: 2

:::{grid-item}
```{image} include/reaction-diffusion-fields.png
:width: 100%
:align: center
```
*Below the transition (`F=0.040`): rich spatial pattern.*
:::

:::{grid-item}
```{image} include/reaction-diffusion-fields-2.png
:width: 100%
:align: center
```
*Above the transition (`F=0.055`): pattern dissolved.*
:::
::::

Every simulation is tracked by AiiDA, so we can inspect any of them:

```{code-cell} ipython3
:tags: ["hide-output"]

# List all processes run so far in this profile.
%verdi process list -a
```

:::{important}
Notice what we had to do to get the `variance_V` values: manually open each YAML output file and extract the number.

The provenance looks like this for each run: **file in → ShellJob → file out**.
AiiDA knows *that* a result file was produced, but it can't see *what's inside* it, so a query like "all runs where `variance_V > 0.001`" would mean opening every file ourselves.
:::

## Structured data nodes

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

## Tracking Python steps with `@calcfunction`

A {func}`@calcfunction <aiida.engine.processes.functions.calcfunction>` is the simplest way to register inputs and outputs as structured data nodes.
It's a regular Python function with a decorator that makes AiiDA automatically:

1. Store all input nodes
2. Create a **process node** recording the computation
3. Store all output nodes
4. Link everything in the provenance graph

Let's write two: one for input preparation, one for output parsing.

The first, `prepare_input`, takes a `Dict` of parameters and produces the YAML input file our simulation script expects:

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
Inside a `calcfunction`, all parameters are AiiDA data nodes, not plain Python types. That is why the function calls `parameters.get_dict()` to extract the dictionary.

When *calling* the function, AiiDA auto-serializes plain Python types (`int`, `float`, `str`, `bool`, `dict`, `list`) to the corresponding `orm` nodes, so `prepare_input(orm.Dict(params))` and `prepare_input(params)` both work.
:::

The second, `parse_output`, reads the YAML output file and extracts the scalar results as `Float` nodes. We declare the two return keys as a {class}`~typing.TypedDict` so the function's return type is self-documenting (and so that {ref}`Module 3 <tutorial:module3>` can reuse the same annotation):

```{code-cell} ipython3
# Define parse_output: a calcfunction that extracts scalars from the YAML results file.
from typing import TypedDict


class ParseOutputs(TypedDict):
    variance_V: float
    mean_V: float


@engine.calcfunction
def parse_output(output_file: orm.SinglefileData) -> ParseOutputs:
    """Extract variance_V and mean_V from a SinglefileData YAML results file."""
    with output_file.open(mode='r') as f:
        data = yaml.safe_load(f)
        return {
            'variance_V': orm.Float(data['variance_V']),
            'mean_V': orm.Float(data['mean_V']),
        }
```

:::{note}
A calcfunction can return either a single data node or a plain `dict` mapping string labels to data nodes.
When returning a dict, AiiDA registers each value as a named output on the process node, accessible via `node.outputs.<label>`.
:::

Now chain them: `prepare_input` → `launch_shell_job` → `parse_output`. Each step is tracked, and the inputs and outputs are stored as structured, queryable nodes:

```{code-cell} ipython3
# Run the enriched pipeline: prepare_input → ShellJob → parse_output.
input_file = prepare_input(orm.Dict(BASE_PARAMS))

results, node = launch_shell_job(
    python_code,
    arguments='{script} --input {input} --output results.yaml',
    nodes={'script': SCRIPT_PATH, 'input': input_file},
    outputs=['results.yaml'],
)

parsed = parse_output(results['results_yaml'])
print(f"variance(V) = {parsed['variance_V'].value:.4e}")
print(f"mean(V)     = {parsed['mean_V'].value:.4e}")
```

`parse_output` is now itself a first-class process node: the calcjob's YAML output node is its input, and the `Float` nodes are its outputs:

```{code-cell} ipython3
# parse_output is a tracked process: SinglefileData in, Float nodes out.
parse_node = parsed['variance_V'].creator
%verdi process show {parse_node.pk}
```

Visualized as a graph, the full chain `prepare_input → ShellJob → parse_output` is one connected piece of provenance:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
# Provenance graph now shows Dict in and Float out, not just files.
from include.plotting import plot_provenance

plot_provenance(node)
```

Compare this to the first sweep: the provenance now shows **Dict** going in and **Float** values coming out, not just opaque files.
These values can now be searched directly in AiiDA's database.

Scaling that up to the full sweep, with the same structured data at every step:

```{code-cell} ipython3
# Re-run the full sweep with the enriched pipeline (structured data at every step).
enriched_results = []

for f_val in F_VALUES:
    input_file = prepare_input(BASE_PARAMS | {'F': f_val})

    results, calc_node = launch_shell_job(
        python_code,
        arguments='{script} --input {input} --output results.yaml',
        nodes={'script': SCRIPT_PATH, 'input': input_file},
        outputs=['results.yaml'],
    )

    parsed = parse_output(results['results_yaml'])
    enriched_results.append({'F': f_val, 'parsed': parsed})
```

Now the payoff: instead of manually opening YAML files, the results are stored as `Float` nodes that we can access directly through the provenance graph:

```{code-cell} ipython3
# Access the structured results directly (no file handling needed).
for r in enriched_results:
    print(f"F={r['F']:.3f}  variance(V)={r['parsed']['variance_V'].value:.4e}")
```

The transition curve looks identical to the first sweep (same simulation, same parameters); what changed is *how* we got the numbers. The `Dict` inputs and `Float` outputs now live in the database with full provenance, ready to be queried.

<!-- TODO: Add "Grouping results" subsection — collect all sweep runs into an AiiDA Group,
     show `verdi group list`, `verdi group show`. Groups let you organize related
     calculations (e.g. "all F-sweep runs") for later retrieval.
     From meeting notes: "groups; AiiDA manages your FS". -->

<!-- TODO: Consider adding a benchmark/speed note on *result retrieval* at scale.
     E.g. for 1k parameter values: without AiiDA you'd need 1k file opens + YAML loads
     just to find interesting runs. With AiiDA, the parsed Float values live in the database
     and can be queried instantly via QueryBuilder.
     (The file I/O during parse_output still happens, but in real-world scenarios
     that runs asynchronously in the background via AiiDA daemon workers.)
     From meeting notes: "show speed impact (benchmark?)". -->

This is what {class}`~aiida.orm.QueryBuilder` enables: structured search over the provenance graph. A few examples on the `Float` nodes we just stored:

```{code-cell} ipython3
# Three QueryBuilder examples on the Float nodes stored by parse_output.

# 1. Count all Float nodes in the database.
qb = orm.QueryBuilder().append(orm.Float)
print(f'Total Float nodes stored: {qb.count()}')

# 2. Filter by attribute value (the "find runs above a threshold" pattern).
qb = orm.QueryBuilder().append(orm.Float, filters={'attributes.value': {'>': 0.01}})
print(f'  with value > 0.01:      {qb.count()}')

# 3. Project just the values, so the DB doesn't have to load full nodes.
qb = orm.QueryBuilder().append(orm.Float, project='attributes.value')
values = sorted(row[0] for row in qb.all())
print(f'All Float values (sorted): {[round(v, 4) for v in values]}')
```

QueryBuilder can also join across the provenance graph: filter `Float` nodes by the calcfunction that created them, by output label, by the workflow they belong to, etc. We'll cover those patterns properly in {ref}`Module 5 <tutorial:module5>`.

```{code-cell} ipython3
:tags: ["hide-output"]

# List all processes run so far.
%verdi process list -a -p 1
```

## Next steps

We now have a tracked pipeline with structured data, but it's still a Python `for` loop that runs each step in a blocking manner.
If one step fails, the loop stops. There's no single "sweep" object to query, and no way to run steps in parallel.
In {ref}`Module 3 <tutorial:module3>`, you'll wrap the pipeline into a **WorkGraph workflow** and turn the loop into a mapped workflow too.

## Further reading

- AiiDA's data model: {ref}`topics:data_types`
- Base data types (`Dict`, `Float`, `Int`, `Str`, `List`): {ref}`topics:data_types:core:base`
- In-depth guide to calcfunctions: {ref}`topics:processes:functions`
- CalcJob reference: {ref}`topics:calculations:concepts:calcjobs`
- Auto-serialization of plain Python types in calcfunctions: {ref}`introduced in v2.1 <topics:calculations:concepts:calcfunctions:automatic-serialization>`
- QueryBuilder (covered properly in {ref}`Module 5 <tutorial:module5>`): {ref}`querying how-to guide <how-to:query>`
