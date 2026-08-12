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

{bdg-secondary}`⏱️ ~90 min read` {bdg-success}`Beginner`

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module2.ipynb` {octicon}`download`
:::

:::{dropdown} Installation requirements (same as&nbsp;{ref}`Module 1 <tutorial:module1>`)
If you have not already installed these in an earlier module, run:

```bash
uv pip install "aiida-core>=2.9" git+https://github.com/aiidateam/aiida-shell matplotlib git+https://github.com/GeigerJ2/gsrd.git@fix/dont-raise-on-trivial-state
```
:::

:::{note}
This module reuses the tutorial profile and the `gsrd_code` object created in {ref}`Module 1 <tutorial:module1>`.
If you are following along locally, run that module first.
:::

```{code-cell} ipython3
:tags: [hide-input]
:mystnb:
:    code_prompt_show: 'Show the setup code (same as Module 1)'
:    code_prompt_hide: 'Hide the setup code (same as Module 1)'

# Set up the tutorial's isolated sandbox profile (see Module 1 for details).
from pathlib import Path

if not Path('include/setup_tutorial.py').exists():
    import urllib.request

    Path('include').mkdir(exist_ok=True)
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/GeigerJ2/aiida-core/docs/integrate-tutorials/docs/source/tutorials/include/setup_tutorial.py',
        'include/setup_tutorial.py',
    )

%run -i include/setup_tutorial.py
%load_ext aiida
```

## What you will learn

After this module, you will be able to:

- Recognize why file-based outputs are hard to query, and what structured data buys you
- Use AiiDA's structured data types (`Dict`, `Float`, ...) to store queryable results
- Add input preparation and output parsing as tracked `@calcfunction` steps in the provenance
- Organize and search results with extras, groups, and QueryBuilder

## Why structured data?

In {ref}`Module 1 <tutorial:module1>`, you ran a single `gsrd` simulation through `aiida-shell` and got back `SinglefileData` nodes: the input YAML, the captured stdout, and the `results.npz` file, all tracked with provenance.

Let's run one again here to work with, holding the Gray-Scott parameters fixed:

```{code-cell} ipython3
:tags: [hide-input]
:mystnb:
:    code_prompt_show: 'Show the run code (same as Module 1)'
:    code_prompt_hide: 'Hide the run code (same as Module 1)'

# Run a single tracked gsrd calculation (as in Module 1).
from pathlib import Path

import yaml

from aiida_shell import launch_shell_job

# The Gray-Scott parameters for this run.
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

input_dir = Path('/tmp/aiida-tutorial')
input_dir.mkdir(parents=True, exist_ok=True)
input_path = input_dir / 'input.yaml'
input_path.write_text(yaml.dump(BASE_PARAMS))

results, calc_node = launch_shell_job(
    gsrd_code,
    arguments='{input}',
    nodes={'input': str(input_path)},
    outputs=['results.npz'],
)
```

As in {ref}`Module 1 <tutorial:module1>`, getting the `variance_V` value back out means a hand-written regex over the run's `stdout` node.
The provenance records **file in → ShellJob → stdout/file out**, so AiiDA knows *that* a stdout log and a `results.npz` were produced, but not *what's inside* them.
A query like "all runs where `variance_V > 0.001`" would therefore mean opening every stdout node and re-running that regex ourselves.

Looking at the provenance graph of the run (essentially the same shape as the one we saw in {ref}`Module 1 <tutorial:module1>`) makes this visible:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
# Provenance graph of the run: opaque files in, opaque files out.
from include.plotting import plot_provenance

plot_provenance(calc_node)
```

Every input and every output is a `SinglefileData` blob: the YAML on the left, `results.npz` and `stdout` on the right.
The simulation ran with full provenance, but as far as the database is concerned, the values that we actually care about are buried inside opaque files.

Instead, we can register the simulation's inputs and outputs as **structured AiiDA data nodes**:

- The input parameters as a {py:class}`~aiida.orm.Dict` (queryable key-value pairs in the database)
- The output scalars as {py:class}`~aiida.orm.Float` nodes (directly searchable)

:::{note}
`Dict` and `Float` both come from AiiDA's {mod}`~aiida.orm` module (short for **Object-Relational Mapping**), which lets you work with database-stored objects as regular Python classes.
It also provides `Int`, `Str`, `List` (Python primitive equivalents), `SinglefileData`, and more, each automatically persisted in the database and linked in the provenance graph.
:::

## Tracking Python steps with `@calcfunction`

A {func}`@calcfunction <aiida.engine.processes.functions.calcfunction>` is the simplest way to register inputs and outputs as structured data nodes.
It's a regular Python function with a decorator that makes AiiDA automatically:

1. Store all input nodes
2. Create a **process node** recording the computation
3. Store all output nodes
4. Link everything in the provenance graph

Because a `calcfunction` records its inputs and outputs as AiiDA nodes, inside the body you work with AiiDA data objects rather than plain Python: `parameters` arrives as an `orm.Dict` node (not a plain `dict`), whose contents you read with `.value`, the same `.value` every data node exposes, including the `orm.Float` outputs later.
At the *call* site you can still pass a plain `dict`; AiiDA auto-wraps it into that `orm.Dict` node for you.

Let's write two: one for input preparation, and one for output parsing.

### Preparing the input

`prepare_input` bridges the two natural representations of a simulation's parameters: the dictionary of typed values we want to *think* in (floats, ints, strings) and the YAML input file the binary actually *reads*.
Most scientific codes take an input file on disk, but the values that drive them are often set programmatically (e.g., from Python), as typed variables.
Doing the conversion inside a `calcfunction` keeps both representations in the provenance graph: the `Dict` is queryable, the rendered file is what `gsrd` consumes:

```{code-cell} ipython3
# Define prepare_input: a calcfunction that converts a Dict to a YAML file.
from aiida import engine, orm


@engine.calcfunction
def prepare_input(parameters: orm.Dict) -> orm.SinglefileData:
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.value)
    return orm.SinglefileData.from_string(content, filename='input.yaml')
```

This also starts to address one of {ref}`Module 0 <tutorial:module0>`'s pain points: the parameters now live in a single `Dict` node, stored with full provenance and reviewable in one place, rather than a hand-edited YAML file whose mistyped keys vanish silently.

:::{tip}
A `Dict` on its own still doesn't *validate* the keys, but real {ref}`CalcJob <topics:calculations:concepts:calcjobs>` plugins do: they check the inputs for you and reject unknown or malformed parameters before the calculation ever runs.
:::

### Parsing the output

`parse_output` takes the captured stdout of a `gsrd` run and extracts the two scalar diagnostics as `Float` nodes.
We declare the two return keys as a {class}`~typing.TypedDict` so the function's return type is self-documenting (and so that {ref}`Module 3 <tutorial:module3>` can reuse the same annotation):

```{code-cell} ipython3
# Define parse_output: a calcfunction that reads the scalars from gsrd stdout.
import re
from typing import TypedDict

VARIANCE_RE = re.compile(r'Variance of V field\s*:\s*([\d.eE+-]+)')
MEAN_RE = re.compile(r'Mean\s+of V field\s*=\s*([\d.eE+-]+)')


class ParseOutputs(TypedDict):
    variance_V: float
    mean_V: float


@engine.calcfunction
def parse_output(stdout: orm.SinglefileData) -> ParseOutputs:
    """Extract variance_V and mean_V from the captured ``gsrd`` stdout log."""
    text = stdout.get_content(mode='r')

    variance_v = float(VARIANCE_RE.search(text).group(1))
    mean_v = float(MEAN_RE.search(text).group(1))

    return {
        'variance_V': orm.Float(variance_v),
        'mean_V': orm.Float(mean_v),
    }
```

:::{note}
Writing a small parsing step is a common cost when wrapping codes that emit their results in unstructured text (the alternative being a schema-defined output format like XML or HDF5, which not every code provides).
What is new here is that the parsing step itself becomes a tracked AiiDA process: its inputs (the stdout node) and its outputs (the `Float` nodes) get linked into the provenance graph, so the regex result lives at the same level as the simulation's other data.
:::

:::{note}
A calcfunction can return either a single data node or a plain `dict` mapping string labels to data nodes.
When returning a single node, AiiDA registers it under the default link label `result`, accessible via `node.outputs.result`.
When returning a dict, each value is registered as a named output instead, accessible via `node.outputs.<label>`.
:::

### Chaining the steps into a pipeline

Now, we can chain them: `prepare_input` → `launch_shell_job` → `parse_output`.
Each step is tracked, and the inputs and outputs are stored as structured, queryable nodes:

```{code-cell} ipython3
# Run the pipeline. engine.run_get_node runs a process and returns (outputs, process node),
# the same shape launch_shell_job returns just below; we keep the nodes we inspect later.
input_file, _ = engine.run_get_node(prepare_input, parameters=BASE_PARAMS)

results, node = launch_shell_job(
    gsrd_code,
    arguments='{input}',
    nodes={'input': input_file},
    outputs=['results.npz'],
)

parsed, parse_node = engine.run_get_node(parse_output, stdout=results['stdout'])
print(f"variance(V) = {parsed['variance_V'].value:.4e}")
print(f"mean(V)     = {parsed['mean_V'].value:.4e}")
```

That is already the payoff: instead of opening the output files, `variance(V)` and `mean(V)` come straight off the run's `Float` output nodes via `.value`.

:::{note}
`launch_shell_job` is `aiida-shell`'s convenience wrapper: it builds a **ShellJob** (a `CalcJob`) from your command and inputs, runs it, and returns `(outputs, node)`.
So the `gsrd` step is an AiiDA process just like the two calcfunctions around it..
:::

`parse_output` is now itself a first-class process node: the calcjob's `stdout` node is its input, and the `Float` nodes are its outputs:

```{code-cell} ipython3
# parse_output is a tracked process: SinglefileData (stdout) in, Float nodes out.
# parse_node came from engine.run_get_node above.
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

Compare this to the opaque run at the start of the module: the provenance now shows `Dict` going in and `Float` values coming out, not just opaque files.
What changed is not the simulation but *how* we get the numbers back: the `Dict` inputs and `Float` outputs now live in the database with full provenance, ready to be queried.

We've now chained these three steps by hand.
Packaging them as a function makes the pipeline repeatable, and it returns a small `GsrdRun` record so each run's nodes are reachable by name:

```{code-cell} ipython3
:tags: [hide-input]
:mystnb:
:    code_prompt_show: 'Show the GsrdRun dataclass'
:    code_prompt_hide: 'Hide the GsrdRun dataclass'

from dataclasses import dataclass


@dataclass
class GsrdRun:
    """One Gray-Scott run: its feed rate and the three process nodes that produced it."""

    F: float
    prepare: orm.ProcessNode
    shelljob: orm.ProcessNode
    parse: orm.ProcessNode
```

```{code-cell} ipython3
def run_pipeline(f_val: float) -> GsrdRun:
    """Run prepare_input → ShellJob → parse_output for one feed rate, returning a GsrdRun."""
    params = BASE_PARAMS | {'F': f_val}
    input_file, prepare_node = engine.run_get_node(prepare_input, parameters=params)

    results, shelljob_node = launch_shell_job(
        gsrd_code,
        arguments='{input}',
        nodes={'input': input_file},
        outputs=['results.npz'],
    )

    parsed, parse_node = engine.run_get_node(parse_output, stdout=results['stdout'])

    return GsrdRun(
        F=f_val,
        prepare=prepare_node,
        shelljob=shelljob_node,
        parse=parse_node,
    )
```

:::{note}
`run_pipeline` runs immediately: each `engine.run_get_node` and `launch_shell_job` call blocks until its process finishes, so the nodes exist as soon as the function returns.
{ref}`Module 3 <tutorial:module3>` takes this same function and turns it into a tracked **WorkGraph** workflow, where you instead *build* the graph first and run it as a single separate step.
:::

## Organizing and querying your results

The tools below only earn their keep once you have more than one run, so let's call `run_pipeline` over a few feed rates:

```{code-cell} ipython3
runs = [run_pipeline(f_val) for f_val in [0.040, 0.045, 0.048, 0.050]]
```

With a handful of tracked runs in the database, the payoff we are building toward is **searching** them, which is what the `QueryBuilder` does.
Queries get far more useful once each run carries additional metadata to filter on, so we take it in three steps:

- **Tag** nodes with ad-hoc metadata: **extras**.
- **Bundle** related runs as a single named unit you can retrieve or share: **groups**.
- **Search** across the database, including by extras and group membership: **QueryBuilder**.

### Extras

There are often properties you want to attach to a node *after* it was created: a quality flag, a review status, "this is the run I used in the paper".
The **extras** dictionary on every AiiDA node is AiiDA's mechanism for exactly that: unlike node attributes (immutable once stored), extras can be set and changed freely, long after the node was created, without touching the provenance graph.

Having run the sweep, say you want to mark the run at the **pattern transition**, a judgement about the results that the provenance itself does not record.
From the transition curve in {ref}`Module 3b <tutorial:module3b>`, the pattern dissolves around `F=0.050`, so we select that run and flag its `parse_output` node:

```{code-cell} ipython3
transition_run = next(run for run in runs if run.F == 0.050)
transition_run.parse.base.extras.set('note', 'pattern transition')
```

### Groups

Extras are great for filters and tags, but sometimes you want to bundle "the runs that belong together" as a single named object you can retrieve, share, or hand to someone else.
A {py:class}`~aiida.orm.Group` is AiiDA's named collection for that:

```{code-cell} ipython3
sweep_group, _ = orm.Group.collection.get_or_create('tutorial/F-sweep')
sweep_group.clear()  # start empty so re-running this cell doesn't accumulate nodes
sweep_group.add_nodes([run.parse for run in runs])

print(f"Group '{sweep_group.label}' contains {sweep_group.count()} nodes")
```

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi group list -C
```

Groups are purely organizational and do not affect provenance.
You can add or remove nodes at any time, and a node can belong to multiple groups.

:::{tip}
Group labels are hierarchical: the `/` works like a directory separator, so `tutorial/F-sweep` nests `F-sweep` under a `tutorial/` namespace, and AiiDA can navigate that hierarchy.
:::

### QueryBuilder

Extras and groups are how you *organize* nodes; {class}`~aiida.orm.QueryBuilder` is how you *find* them.
It is AiiDA's structured-search API over the provenance graph: filter by node type, by attribute value, by extras, by which group they belong to, by their relationships to other nodes, etc.

You build a query by **appending** the entity type you're after, optionally with `filters` (which nodes to keep) and a `project` (which fields to return), then run it with `.count()`, `.all()`, or `.first()`.
Filters are written against the entity's typed `fields`, which gives tab-completion and type checking instead of hand-typed string keys, as the examples below show.

Start by counting every `parse_output` run in the database:

```{code-cell} ipython3
# Filter by node type and process label.
qb = orm.QueryBuilder().append(
    orm.CalcFunctionNode,
    filters=orm.CalcFunctionNode.fields.process_label == 'parse_output',
)
print(f'parse_output calcfunctions in this profile: {qb.count()}')
```

That counts by node *type*. You can just as well filter by a stored **attribute**, for example the feed rate `F` that each run recorded on its input `Dict`:

```{code-cell} ipython3
# Filter input Dict nodes by a stored parameter value.
qb = orm.QueryBuilder().append(
    orm.Dict,
    filters=orm.Dict.fields.attributes['F'] == 0.046,
    project=['pk', 'attributes.F'],
)
pk, f_value = qb.first()
print(f'An input Dict with F = {f_value} sits at PK {pk}')
```

The `tutorial/F-sweep` Group we built earlier scopes a query to just its members, by chaining a second `.append` with `with_group`:

```{code-cell} ipython3
# Restrict to the parse_output nodes that belong to our Group.
qb = (
    orm.QueryBuilder()
    .append(orm.Group, filters=orm.Group.fields.label == 'tutorial/F-sweep', tag='grp')
    .append(orm.CalcFunctionNode, with_group='grp')
)
print(f'parse_output runs in the tutorial/F-sweep group: {qb.count()}')
```

Then use the extra we just set to pull the transition run straight back out, however many runs sit in between:

```{code-cell} ipython3
# Filter the same node type by an extras key.
qb = orm.QueryBuilder().append(
    orm.CalcFunctionNode,
    filters=orm.CalcFunctionNode.fields.extras['note'] == 'pattern transition',
    project='pk',
)
print(f'Transition run: parse_output PK {qb.first(flat=True)}')
```

That last query already chains two appends (Group → its members). QueryBuilder can go much further: *projecting* single fields instead of loading whole nodes, and following the links between nodes, a run to its `Float` outputs, back to its inputs, across entire workflows. We'll cover those patterns properly in a later module.

With all this activity, our profile is filling up, so let's list every process we have run so far across all modules:

```{code-cell} ipython3
:tags: ["hide-output"]

# List all processes run so far.
%verdi process list -a
```

## Next steps

We now have a tracked pipeline with structured data, but two things are still plain Python.
The pipeline, `prepare_input → ShellJob → parse_output`, is a bare sequence of calls: there's no single object that *is* the workflow, so if one step fails you handle it yourself, and there's nothing to hand around or query as one unit.
And, the sweep is a `for` loop that runs each parameter set one after another, with no way to run independent runs in parallel.

In {ref}`Module 3a <tutorial:module3a>`, you'll wrap that pipeline into a single **WorkGraph workflow**.
Then in {ref}`Module 3b <tutorial:module3b>`, you'll map it over the whole sweep in parallel with WorkGraph's `Map`, replacing the `for` loop.

## Further reading

- AiiDA's data model: {ref}`topics:data_types`
- Built-in data types (scalars, collections, arrays, files): {ref}`topics:data_types:core`
- In-depth guide to calcfunctions: {ref}`topics:processes:functions`
- CalcJob reference: {ref}`topics:calculations:concepts:calcjobs`
- {ref}`Auto-serialization of plain Python types in calcfunctions <topics:calculations:concepts:calcfunctions:automatic-serialization>` (introduced in v2.1)
- QueryBuilder: {ref}`querying how-to guide <how-to:query>`
