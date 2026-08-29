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

{bdg-secondary}`⏱️ ~75 min read` {bdg-success}`Beginner`

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module2.ipynb` {octicon}`download`
:::

:::{dropdown} Installation requirements (same as&nbsp;{ref}`Module 1 <tutorial:module1>`)
If you have not already installed these in an earlier module, run:

```bash
uv pip install "aiida-core>=2.9" "aiida-shell>=0.9.0" matplotlib "gsrd>=0.2.0"
```
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

- Recognize why file-based outputs are hard to query, and what structured data buys you
- Use AiiDA's structured data types (`Dict`, `Float`, ...) to store queryable results
- Add input preparation and output parsing as tracked `@calcfunction` steps in the provenance
- Organize and search results with extras, groups, and the QueryBuilder

## Why structured data?

In {ref}`Module 1 <tutorial:module1>`, you ran a single `gsrd` simulation through `aiida-shell` and got back `SinglefileData` nodes: the input YAML, the captured stdout, and the `results.npz` file, all tracked with provenance.

Let's run one again here to work with, holding the Gray-Scott parameters fixed:

```{code-cell} ipython3
:tags: [hide-input]
:mystnb:
:    code_prompt_show: 'Show the run code (same as Module 1)'
:    code_prompt_hide: 'Hide the run code (same as Module 1)'

# Run a single tracked gsrd calculation (as in Module 1).
from importlib.resources import files

from aiida_shell import launch_shell_job

results, calc_node = launch_shell_job(
    gsrd_code,
    arguments='{input}',
    nodes={'input': str(files('gsrd') / 'data' / 'input.yaml')},
    outputs=['results.npz'],
)
```

As in {ref}`Module 1 <tutorial:module1>`, getting the `variance_V` value back out means a hand-written regex over the run's `stdout` node.
The provenance records **file in → ShellJob → stdout/file out**, so AiiDA knows *that* a stdout log and a `results.npz` were produced, but not *what's inside* them.
A query like "all runs where `variance_V > 0.001`" would therefore mean opening every stdout node and re-running that regex ourselves.

Looking at the provenance graph of the run (exactly the same shape as the one we saw in {ref}`Module 1 <tutorial:module1>`) makes this visible:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
# Provenance graph of the run: opaque files in, opaque files out
# (plot_provenance is defined in the setup cell above).
plot_provenance(calc_node)
```

Every file here is a `SinglefileData` blob: the input YAML at the top, `results.npz`, `stdout`, and `stderr` at the bottom.
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

Because a `calcfunction` records its inputs and outputs as AiiDA nodes, inside the body you work with AiiDA data objects rather than plain Python, as you will see below.

Let's write two: one for input preparation, and one for output parsing.

### Preparing the input

In {ref}`Module 1 <tutorial:module1>`, we handed `gsrd` a ready-made `input.yaml`. To capture the parameters themselves as queryable data, we now build that file from a `Dict` inside a calcfunction instead.
`prepare_input` bridges the two natural representations of a simulation's parameters: the dictionary of typed values we want to *think* in (floats, ints, strings) and the YAML input file the binary actually *reads*.
Most scientific codes take an input file on disk, but the values that drive them are often set programmatically (e.g., from Python), as typed variables.
Doing the conversion inside a `calcfunction` keeps both representations in the provenance graph: the `Dict` is queryable, the rendered file is what `gsrd` consumes:

```{code-cell} ipython3
# Define prepare_input: a calcfunction that converts a Dict to a YAML file.
import yaml

from aiida import engine, orm


@engine.calcfunction
def prepare_input(parameters: orm.Dict) -> orm.SinglefileData:
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.value)
    return orm.SinglefileData.from_string(content, filename='input.yaml')
```

Inside `prepare_input`, `parameters` arrives as an `orm.Dict` node (not a plain `dict`), whose contents you read with `.value`, the same `.value` every data node exposes, including the `orm.Float` outputs later.
At the *call* site you can still pass a plain `dict`; AiiDA auto-wraps it into that `orm.Dict` node for you.

This also starts to address one of {ref}`Module 0 <tutorial:module0>`'s pain points: the parameters now live in a single `Dict` node, stored with full provenance and reviewable in one place, rather than a hand-edited YAML file whose mistyped keys vanish silently.

:::{tip}
A `Dict` on its own still doesn't *validate* the keys, but real {ref}`CalcJob <topics:calculations:concepts:calcjobs>` plugins do: they check the inputs for you and reject unknown or malformed parameters before the calculation ever runs.
:::

### Parsing the output

`parse_output` takes the captured stdout of a `gsrd` run and extracts the two scalar diagnostics as `Float` nodes.
We declare the two return keys as a {class}`~typing.TypedDict` so the function's return type is self-documenting (and, pedagogically, so that {ref}`Module 3 <tutorial:module3>` can reuse the same annotation):

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

Writing a small parsing step is a common cost when wrapping codes that emit their results in unstructured text (the alternative being a schema-defined output format like XML or HDF5, which not every code provides).
What is new here is that the parsing step itself becomes a tracked AiiDA process: its inputs (the stdout node) and its outputs (the `Float` nodes) get linked into the provenance graph, so the regex result lives at the same level as the simulation's other data.

:::{note}
A calcfunction can return either a single data node or a `dict` mapping string labels to data nodes.
When returning a single node, AiiDA registers it under the default link label `result`, accessible via `node.outputs.result`.
When returning a dict, each value is registered as a named output instead, accessible via `node.outputs.<label>`.
:::

:::{note}
`prepare_input` and `parse_output` are kept deliberately small here to keep the AiiDA concepts in focus; in real workflows any of these steps can carry substantial work, such as expensive input preparation, data analysis, or downstream simulation stages.
:::

### Chaining the steps into a pipeline

Now, we can chain them: `prepare_input` → `launch_shell_job` → `parse_output`.
We pass the input parameters as a `dict` (`BASE_PARAMS`, the same values as the opening run's `input.yaml`, now in the queryable form we motivated above).
`engine.run_get_node` runs each calcfunction and returns its `(outputs, node)`, the same shape `launch_shell_job` returns; we keep the nodes we inspect later.
Each step is tracked, and the inputs and outputs are stored as structured, queryable nodes:

```{code-cell} ipython3
# The Gray-Scott parameters, as a dict.
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

# Run the pipeline.
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

Reading `variance(V)` and `mean(V)` straight off the run's `Float` output nodes via `.value`, instead of opening the output files, is one of the advantages of structured data.

:::{note}
`launch_shell_job` is `aiida-shell`'s convenience wrapper: it builds a **ShellJob** (a `CalcJob`) from your command and inputs, runs it, and returns `(outputs, node)`.
So the `gsrd` step is an AiiDA process just like the two calcfunctions around it.
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
plot_provenance(node)
```

Compare this to the opaque run at the start of the module: the provenance now shows `Dict` going in and `Float` values coming out, not just opaque files.
What changed is not the simulation but *how* we get the numbers back: the `Dict` inputs and `Float` outputs now live in the database with full provenance, ready to be queried.

We've now chained these three steps by hand.
Packaging them into a function, `run_pipeline`, makes the sweep below repeatable. It returns the run's final `parse_output` node, which carries the `variance_V` and `mean_V` outputs and links back through the full provenance:

```{code-cell} ipython3
def run_pipeline(params: dict, command: orm.InstalledCode) -> orm.CalcFunctionNode:
    """Run prepare_input → ShellJob → parse_output; return the parse_output node."""
    input_file, _ = engine.run_get_node(prepare_input, parameters=params)

    results, _ = launch_shell_job(
        command,
        arguments='{input}',
        nodes={'input': input_file},
        outputs=['results.npz'],
    )

    _, parse_node = engine.run_get_node(parse_output, stdout=results['stdout'])
    return parse_node
```

:::{note}
`run_pipeline` runs immediately: each `engine.run_get_node` and `launch_shell_job` call blocks until its process finishes, so the nodes exist as soon as the function returns.
{ref}`Module 3 <tutorial:module3>` takes this same function and turns it into a tracked **WorkGraph** workflow, where you instead *build* the graph first and run it as a single separate step.
:::

## Organizing and querying your results

The tools below only earn their keep once you have more than one run, so let's call `run_pipeline` over a few feed rates, keyed by `F`:

```{code-cell} ipython3
F_VALUES = [0.040, 0.045, 0.048, 0.050]
runs = {
    f_val: run_pipeline(BASE_PARAMS | {'F': f_val}, gsrd_code) for f_val in F_VALUES
}
```

With a handful of tracked runs in the database, the payoff we are building toward is **searching** them, which is what the `QueryBuilder` does.
Queries also get far more useful once each run carries additional metadata to filter on, so we take it in three steps:

- **Tag** nodes with ad-hoc metadata: **extras**.
- **Bundle** related runs as a single named unit you can retrieve or share: **groups**.
- **Search** across the database, including by extras and group membership: **QueryBuilder**.

### Extras

There are often properties you want to attach to a node *after* it was created: a quality flag, a review status, e.g., "this is the run I used in the paper", etc.
The **extras** dictionary on every AiiDA node is AiiDA's mechanism for exactly that: unlike node attributes (immutable once stored), extras can be set and changed freely, long after the node was created, without touching the provenance graph.

Having run the sweep, say you want to mark the run at the **pattern transition**, a judgement about the results that the provenance itself does not record.
From the transition curve in {ref}`Module 3b <tutorial:module3b>`, the pattern dissolves around `F=0.050`, so we take that run's `parse_output` node from the sweep and flag it:

```{code-cell} ipython3
transition_node = runs[0.050]
transition_node.base.extras.set('note', 'pattern transition')
```

### Groups

Extras are great for filters and tags, but sometimes you want to bundle "the runs that belong together" as a single named object you can retrieve, share, or hand to someone else.
A {py:class}`~aiida.orm.Group` is AiiDA's named collection for that:

```{code-cell} ipython3
sweep_group, _ = orm.Group.collection.get_or_create('tutorial/F-sweep')
sweep_group.clear()  # start empty so re-running this cell doesn't accumulate nodes
sweep_group.add_nodes(list(runs.values()))

print(f"Group '{sweep_group.label}' contains {sweep_group.count()} nodes")
```

We can see the group we just created via the `verdi` CLI:

```{code-cell} ipython3
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
Filters can be written against the entity's typed `fields`, which gives tab-completion and type checking instead of hand-typed string keys, as the examples below show.

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
    filters=orm.Dict.fields.attributes['F'] == 0.045,
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

Then use the extra we just set to pull the transition run straight back out, however many runs sit in between. That gives us the `parse_output` node; because it is wired into the graph, we can hop one link further to the `gsrd` simulation that produced its `stdout`, no second query needed:

```{code-cell} ipython3
# Find the tagged parse_output node, then hop to the ShellJob behind its stdout.
qb = orm.QueryBuilder().append(
    orm.CalcFunctionNode,
    filters=orm.CalcFunctionNode.fields.extras['note'] == 'pattern transition',
)
transition_parse = qb.first(flat=True)
simulation = transition_parse.inputs.stdout.creator
print(f'Transition run: parse_output PK {transition_parse.pk}')
print(f'gsrd simulation behind it: ShellJob PK {simulation.pk}')
```

The examples above already chain multiple `append` calls and follow a link through the provenance graph by hand. QueryBuilder and node navigation go much further: *projecting* single fields instead of loading whole nodes, and chaining hops across entire workflows. We'll cover those patterns properly in a later module.

With all this activity, our profile is filling up, so let's list every process we have run so far across all modules:

```{code-cell} ipython3
:tags: ["hide-output"]

# List all processes run so far.
%verdi process list -a
```

## Next steps

We now have a tracked pipeline with structured data, but two things are still plain Python.
`run_pipeline` packages `prepare_input → ShellJob → parse_output` into one function, but that function just runs the three steps in order when you call it. The provenance records them as three individual processes with no parent **workflow** node tying them together, so there's no single object that *is* a run to hand around, restart, or query as one unit, and if a step fails you handle it yourself.
And the sweep runs each parameter set one after another, with no way to run independent runs in parallel.

In {ref}`Module 3a <tutorial:module3a>`, you'll wrap that pipeline into a single **WorkGraph workflow**.
Then in {ref}`Module 3b <tutorial:module3b>`, you'll map it over the whole sweep in parallel with WorkGraph's `Map`, replacing the `for` loop.

## Further reading

- AiiDA's data model: {ref}`topics:data_types`
- Built-in data types (scalars, collections, arrays, files): {ref}`topics:data_types:core`
- In-depth guide to calcfunctions: {ref}`topics:processes:functions`
- CalcJob reference: {ref}`topics:calculations:concepts:calcjobs`
- {ref}`Auto-serialization of plain Python types in calcfunctions <topics:calculations:concepts:calcfunctions:automatic-serialization>` (introduced in v2.1)
- QueryBuilder: {ref}`querying how-to guide <how-to:query>`
