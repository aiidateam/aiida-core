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

<!-- TODO: re-enable once the md->ipynb conversion script is verified
:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module2.ipynb` {octicon}`download`
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

- Launch many tracked calculations programmatically
- Use AiiDA's structured data types to obtain queryable results
- Add input preparation and output parsing as tracked Python steps to the simulation's provenance
- Organize results with extras and groups for quick retrieval

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

In {ref}`Module 1 <tutorial:module1>`, you ran a single `gsrd` simulation through `aiida-shell` and got back `SinglefileData` nodes: the input YAML, the captured stdout, and the `results.npz` file, all tracked with provenance.

Let's start varying our simulation parameters: scan the feed rate `F` and see how the pattern strength (`variance_V`) changes across a range of values.

```{code-cell} ipython3
# Sweep the feed rate F using aiida-shell.
import tempfile
from pathlib import Path

import yaml

from aiida_shell import launch_shell_job

from include.constants import BASE_PARAMS, F_VALUES

work_dir = Path(tempfile.mkdtemp(prefix='aiida_tutorial_m2_'))
calc_nodes = []

for f_val in F_VALUES:
    input_path = work_dir / (f'input_F{f_val:.3f}'.replace('.', '_') + '.yaml')
    input_path.write_text(yaml.dump(BASE_PARAMS | {'F': f_val}))

    results, calc_node = launch_shell_job(
        gsrd_code,
        arguments='{input}',
        nodes={'input': input_path},
        outputs=['results.npz'],
    )
    calc_nodes.append((f_val, calc_node))
```

We saw in {ref}`Module 1 <tutorial:module1>` that `gsrd` only prints its scalar diagnostics (`variance(V)`, `mean(V)`) to stdout.
So to get the numbers for plotting, we have to grep stdout for each run, same regex as before, just inside a `for` loop now:

```{code-cell} ipython3
# Extract and print results from each run by regexing stdout.
# VARIANCE_RE / MEAN_RE live in `include/constants.py` so every module that
# needs to scrape gsrd's diagnostics can import the same patterns.
from include.constants import VARIANCE_RE

sweep_results = []

for f_val, calc_node in calc_nodes:
    text = calc_node.outputs.stdout.get_content()
    variance_v = float(VARIANCE_RE.search(text).group(1))
    sweep_results.append({'F': f_val, 'variance_V': variance_v})

for r in sweep_results:
    print(f"F={r['F']:.3f}  variance(V)={r['variance_V']:.4e}")
```

Plotting `variance_V` against `F` shows what we are after: a sharp drop somewhere along the swept range, marking the boundary between the "pattern forms" and "pattern dies out" regimes:

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
Notice what we had to do to get the `variance_V` values: regex each `stdout` node individually, the same hand-written line as in {ref}`Module 1 <tutorial:module1>`, just inside a `for` loop.

The provenance looks like this for each run: **file in → ShellJob → stdout/file out**.
AiiDA knows *that* a stdout log and a `results.npz` were produced, but it doesn't know *what's inside* them, so a query like "all runs where `variance_V > 0.001`" would mean opening every stdout node and re-running that same regex ourselves.
:::

Looking at the provenance graph of one of the runs (essentially the same shape as the one we already saw in {ref}`Module 1 <tutorial:module1>`) makes this visible:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
# Provenance graph of a single sweep run: opaque files in, opaque files out.
from include.plotting import plot_provenance

plot_provenance(calc_nodes[0][1])
```

Every input and every output is a `SinglefileData` blob: the YAML on the left, `results.npz` and `stdout` on the right.
The simulation ran with full provenance, but as far as the database is concerned, the values that we actually care about are buried inside opaque files.

## Structured data nodes

What if we could register the simulation's inputs and outputs as **structured AiiDA data nodes** instead?

- The input parameters as a {py:class}`~aiida.orm.Dict` (queryable key-value pairs in the database)
- The output scalars as {py:class}`~aiida.orm.Float` nodes (directly searchable)

:::{note}
`orm` stands for **Object-Relational Mapping**: it lets you work with database-stored objects as regular Python classes.
AiiDA's {mod}`~aiida.orm` module provides data types like `Dict`, `Float`, `Int`, `Str`, `List`, `SinglefileData` (and more) that are automatically persisted in the database and linked in the provenance graph.
:::

### Built-in data types at a glance

AiiDA ships a range of data types for different use cases.
The ones you will see most often:

| Category | Type | When to use |
|---|---|---|
| Scalars | {py:class}`~aiida.orm.Int`, {py:class}`~aiida.orm.Float`, {py:class}`~aiida.orm.Str`, {py:class}`~aiida.orm.Bool` | Single values you want queryable in the database |
| Collections | {py:class}`~aiida.orm.Dict`, {py:class}`~aiida.orm.List` | Key-value maps or ordered sequences of simple Python types |
| Arrays | {py:class}`~aiida.orm.ArrayData`, {py:class}`~aiida.orm.XyData` | NumPy arrays (grids, spectra, x-y curves) |
| Files | {py:class}`~aiida.orm.SinglefileData`, {py:class}`~aiida.orm.FolderData`, {py:class}`~aiida.orm.RemoteData` | Opaque binary or text files, directory trees, pointers to files on a remote machine |

The full catalogue is in {ref}`topics:data_types:core`.

## Tracking Python steps with `@calcfunction`

A {func}`@calcfunction <aiida.engine.processes.functions.calcfunction>` is the simplest way to register inputs and outputs as structured data nodes.
It's a regular Python function with a decorator that makes AiiDA automatically:

1. Store all input nodes
2. Create a **process node** recording the computation
3. Store all output nodes
4. Link everything in the provenance graph

Let's write two: one for input preparation, and one for output parsing.

The first, `prepare_input`, bridges the two natural representations of a simulation's parameters: the dictionary of typed values we want to *think* in (floats, ints, strings) and the YAML input file the binary actually *reads*.
Most scientific codes take an input file on disk, but the values that drive them are often set programmatically (e.g., from Python), as typed variables.
Doing the conversion inside a `calcfunction` keeps both representations in the provenance graph: the `Dict` is queryable, the rendered file is what `gsrd` consumes:

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
Inside a `calcfunction`, all parameters are AiiDA data nodes, not plain Python types.
That is why the function calls `parameters.get_dict()` to extract the dictionary.

When *calling* the function, AiiDA auto-serializes plain Python types (`int`, `float`, `str`, `bool`, `dict`, `list`) to the corresponding `orm` nodes, so `prepare_input(orm.Dict(params))` and `prepare_input(params)` both work.
:::

This also starts to address one of {ref}`Module 0 <tutorial:module0>`'s pain points: the parameters now live in a single `Dict` node, stored with full provenance and reviewable in one place, rather than a hand-edited YAML file whose mistyped keys vanish silently.
The `Dict` alone still doesn't validate the keys, but real {ref}`CalcJob <topics:calculations:concepts:calcjobs>` plugins do: they declare typed, validated input ports in their process spec, rejecting unknown or malformed parameters before the calculation ever runs.

The second, `parse_output`, takes the captured stdout of a `gsrd` run and extracts the two scalar diagnostics as `Float` nodes.
We declare the two return keys as a {class}`~typing.TypedDict` so the function's return type is self-documenting (and so that {ref}`Module 3 <tutorial:module3>` can reuse the same annotation):

```{code-cell} ipython3
# Define parse_output: a calcfunction that regexes scalars out of gsrd stdout.
from typing import TypedDict

from include.constants import MEAN_RE, VARIANCE_RE


class ParseOutputs(TypedDict):
    variance_V: float
    mean_V: float


@engine.calcfunction
def parse_output(stdout: orm.SinglefileData) -> ParseOutputs:
    """Extract variance_V and mean_V from the captured ``gsrd`` stdout log."""
    with stdout.open(mode='r') as f:
        text = f.read()

    variance_v = float(VARIANCE_RE.search(text).group(1))
    mean_v = float(MEAN_RE.search(text).group(1))

    return {
        'variance_V': orm.Float(variance_v),
        'mean_V': orm.Float(mean_v),
    }
```

:::{note}
Writing a small parser is a common cost when wrapping codes that emit their results in unstructured text (the alternative being a schema-defined output format like XML or HDF5, which not every code provides).
What is new here is that the parser itself becomes a tracked AiiDA process: its inputs (the stdout node) and its outputs (the `Float`s) get linked into the provenance graph, so the regex result lives at the same level as the simulation's other data.
:::

:::{note}
A calcfunction can return either a single data node or a plain `dict` mapping string labels to data nodes.
When returning a single node, AiiDA registers it under the default link label `result`, accessible via `node.outputs.result`.
When returning a dict, each value is registered as a named output instead, accessible via `node.outputs.<label>`.
:::

Now, we can chain them: `prepare_input` → `launch_shell_job` → `parse_output`.
Each step is tracked, and the inputs and outputs are stored as structured, queryable nodes:

```{code-cell} ipython3
# Run the enriched pipeline: prepare_input → ShellJob → parse_output.
input_file = prepare_input(orm.Dict(BASE_PARAMS))

results, node = launch_shell_job(
    gsrd_code,
    arguments='{input}',
    nodes={'input': input_file},
    outputs=['results.npz'],
)

parsed = parse_output(results['stdout'])
print(f"variance(V) = {parsed['variance_V'].value:.4e}")
print(f"mean(V)     = {parsed['mean_V'].value:.4e}")
```

`parse_output` is now itself a first-class process node: the calcjob's `stdout` node is its input, and the `Float` nodes are its outputs:

```{code-cell} ipython3
# parse_output is a tracked process: SinglefileData (stdout) in, Float nodes out.
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
        gsrd_code,
        arguments='{input}',
        nodes={'input': input_file},
        outputs=['results.npz'],
    )

    parsed = parse_output(results['stdout'])
    enriched_results.append({'F': f_val, 'parsed': parsed})
```

Now the payoff: instead of manually opening YAML files, the results are stored as `Float` nodes that we can access directly through the provenance graph:

```{code-cell} ipython3
# Access the structured results directly (no file handling needed).
for r in enriched_results:
    print(f"F={r['F']:.3f}  variance(V)={r['parsed']['variance_V'].value:.4e}")
```

The transition curve looks identical to the first sweep (same simulation, same parameters); what changed is *how* we got the numbers.
The `Dict` inputs and `Float` outputs now live in the database with full provenance, ready to be queried.

## Organizing your results

Once you have run more than a handful of calculations, three needs show up: (a) tagging nodes by ad-hoc properties you only realized you cared about later, (b) bundling related runs as a single named unit you can retrieve or share, and (c) actually searching across the database to answer questions like "which runs are above the threshold?".
AiiDA gives you three tools, one for each: **extras**, **groups**, and **QueryBuilder**.

### Extras

There are often properties you want to attach to a node *after* it was created: a quality flag, a review status, an experiment label, "this is the run I used in the paper".
The **extras** dictionary on every AiiDA node is AiiDA's mechanism for exactly that.
Unlike node attributes (which are immutable once stored), extras can be updated freely, even long after the node was created, without touching the provenance graph:

```{code-cell} ipython3
# Tag each enriched-sweep CalcJob with its F value and a sweep label.
from pprint import pprint

for r in enriched_results:
    calc_node = r['parsed']['variance_V'].creator  # the parse_output CalcFunctionNode
    calc_node.base.extras.set_many({'F': r['F'], 'sweep': 'F_scan'})

first_calc_node = enriched_results[0]['parsed']['variance_V'].creator
user_extras = {k: v for k, v in first_calc_node.base.extras.all.items() if not k.startswith('_')}
print('Extras on first node:')
pprint(user_extras)
```

### Groups

Extras are great for filters and tags, but sometimes you want to bundle "the runs that belong together" as a single named object you can retrieve, share, or hand to someone else.
A {py:class}`~aiida.orm.Group` is AiiDA's named collection for that:

```{code-cell} ipython3
# Collect all enriched-sweep CalcJobs into a Group.
# `get_or_create` returns a (Group, bool) tuple: the group itself and a flag
# indicating whether it was just created (True) or already existed (False).
sweep_group: orm.Group
created: bool
sweep_group, created = orm.Group.collection.get_or_create('tutorial/F-sweep')

if created:
    for r in enriched_results:
        calc_node = r['parsed']['variance_V'].creator
        sweep_group.add_nodes(calc_node)

print(f"Group '{sweep_group.label}' contains {sweep_group.count()} nodes")
```

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi group list
```

Groups are purely organizational and do not affect provenance.
You can add or remove nodes at any time, and a node can belong to multiple groups.

### Searching with QueryBuilder

Extras and groups are how you *organize* nodes; {class}`~aiida.orm.QueryBuilder` is how you *find* them.
It is AiiDA's structured-search API over the provenance graph: filter by node type, by attribute value, by extras, by which group they belong to, by their relationships to other nodes, etc.
A few examples on the `Float` nodes we just stored:

All three patterns below operate on the F-sweep we just ran. Start by counting how many `parse_output` calcfunction nodes there are:

```{code-cell} ipython3
# 1. Filter by node type and process label.
qb = orm.QueryBuilder().append(
    orm.CalcFunctionNode,
    filters={'attributes.process_label': 'parse_output'},
)
print(f'parse_output calcfunctions in this profile: {qb.count()}')
```

Narrow that down to the ones we tagged with `sweep=F_scan` (using the extras we attached earlier):

```{code-cell} ipython3
# 2. Filter the same node type by an extras key.
qb = orm.QueryBuilder().append(
    orm.CalcFunctionNode,
    filters={'extras.sweep': 'F_scan'},
)
print(f'of which tagged sweep=F_scan: {qb.count()}')
```

Instead of returning whole nodes, *project* a single attribute. Here, recover the `F` values directly from the sweep tags:

```{code-cell} ipython3
# 3. Project a single field, so the database doesn't load full nodes.
qb = orm.QueryBuilder().append(
    orm.CalcFunctionNode,
    filters={'extras.sweep': 'F_scan'},
    project='extras.F',
)
F_values = sorted(row[0] for row in qb.all())
print(f'F values recovered from the sweep tags: {F_values}')
```

QueryBuilder can also join across the provenance graph: filter `Float` nodes by the calcfunction that created them, by output label, by the workflow they belong to, etc. We'll cover those patterns properly in {ref}`Module 5 <tutorial:module5>`.

After all this activity, our profile is filling up.
To list every process we have run so far across all modules:

```{code-cell} ipython3
:tags: ["hide-output"]

# List all processes run so far.
%verdi process list -a
```

## Next steps

We now have a tracked pipeline with structured data, however, it's still a Python `for` loop that runs each step in a blocking manner.
If one step fails, the loop stops.
There's no single "sweep" object to query, and no way to run steps in parallel.
In {ref}`Module 3 <tutorial:module3>`, you'll wrap the pipeline into a **WorkGraph workflow** and turn the loop itself into a mapped workflow too.

## Further reading

- AiiDA's data model: {ref}`topics:data_types`
- Base data types (`Dict`, `Float`, `Int`, `Str`, `List`): {ref}`topics:data_types:core:base`
- In-depth guide to calcfunctions: {ref}`topics:processes:functions`
- CalcJob reference: {ref}`topics:calculations:concepts:calcjobs`
- {ref}`Auto-serialization of plain Python types in calcfunctions <topics:calculations:concepts:calcfunctions:automatic-serialization>` (introduced in v2.1)
- QueryBuilder (covered properly in {ref}`Module 5 <tutorial:module5>`): {ref}`querying how-to guide <how-to:query>`
