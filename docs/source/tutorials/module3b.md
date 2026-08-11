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
  timeout: 300
---

(tutorial:module3b)=
# Module 3b: `for`-loops as workflows

{bdg-secondary}`⏱️ ~75 min read` {bdg-primary}`Intermediate`

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module3b.ipynb` {octicon}`download`
:::

:::{dropdown} Installation requirements
This module uses AiiDA, `aiida-shell`, and `aiida-workgraph`:

```bash
uv pip install "aiida-core>=2.9" git+https://github.com/aiidateam/aiida-shell git+https://github.com/GeigerJ2/aiida-workgraph.git@fix/map-zone-output-retrieval matplotlib git+https://github.com/GeigerJ2/gsrd.git@fix/dont-raise-on-trivial-state
```
:::

:::{note}
This module continues {ref}`Module 3a <tutorial:module3a>`, reusing the same tutorial profile and the `gray_scott_pipeline` workflow built there.
If you are following along locally, work through {ref}`Module 3a <tutorial:module3a>` first: this module builds directly on it.
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

- Run a workflow over many input sets at once with WorkGraph's `Map`, turning a plain Python `for`-loop into a single tracked, parallel workflow
- Gather per-iteration outputs back into a single result
- Reuse the same workflow for a 2D scan by changing only its input

We build on the `gray_scott_pipeline` workflow from {ref}`Module 3a <tutorial:module3a>`.
Because each notebook runs in its own kernel, we import it from the shared `include/workflows.py` rather than redefining it:

```{code-cell} ipython3
from aiida import orm

from aiida_workgraph import Map, task, dynamic, namespace

from include.workflows import gray_scott_pipeline

# The base parameters, and the feed-rate values to scan (same as Module 2).
BASE_PARAMS = {
    'grid_size': 64,
    'du': 0.16,
    'dv': 0.08,
    'F': 0.04,
    'k': 0.065,
    'dt': 1.0,
    'n_steps': 3000,
    'seed': 42,
}
F_VALUES = [0.038, 0.040, 0.042, 0.044, 0.046, 0.050, 0.055, 0.060]
```

The pipeline is unchanged from Module 3a; expand it if you need a refresher:

:::{dropdown} `gray_scott_pipeline`&nbsp;(from Module 3a, in&nbsp;`include/workflows.py`)
```{literalinclude} include/workflows.py
:language: python
:pyobject: gray_scott_pipeline
```
:::

## Integrating the for-loop into the workflow

In Module 2, you ran the pipeline for several `F` values with a plain Python `for` loop.
But a `for` loop is not an AiiDA process: it doesn't show up in the provenance, can't be inspected with `verdi`, and can't recover from failures.
It also runs strictly sequentially, waiting for each `F` value to finish before starting the next.

WorkGraph's {class}`~aiida_workgraph.Map` lets you run the same sub-workflow over multiple input values, like a parallel `for` loop, but as a single AiiDA workflow with full provenance.
In WorkGraph terminology, a `Map` is a **zone**: a region of the graph that controls how the tasks inside it are scheduled.

A `Map` zone works in three parts.
It takes a source mapping of the form `{key: value}` and runs the tasks inside it once per entry.
Inside the zone, `map_zone.item.key` and `map_zone.item.value` expose the current entry as sockets you wire into tasks like any other output.
At the end, `map_zone.gather({...})` picks which per-iteration outputs to collect; afterwards they are available as `map_zone.outputs.<name>`, a namespace keyed by the original source keys.

`Map` is imported alongside the rest of the WorkGraph helpers; its signature and docstring are visible via `help(Map)`:

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show `Map` signature and docstring'
:    code_prompt_hide: 'Hide signature'

help(Map)
```

To close the loop, we add a final **reduction step** to the workflow: a calcfunction `make_transition_plot` ({download}`include/tasks_module_3b.py`) that takes the gathered `variance_V` `Float` nodes and renders the transition curve as a `SinglefileData` PNG.
The workflow's primary output is then that single artifact: `Map` produces one variance per parameter set, and the plotting task combines them into a single figure.

:::{dropdown} `make_transition_plot`&nbsp;(in&nbsp;`include/tasks_module_3b.py`)
```{literalinclude} include/tasks_module_3b.py
:language: python
:pyobject: make_transition_plot
```
:::

Now the graph itself, `gray_scott_sweep`:

```{code-cell} ipython3
from typing import Annotated

from include.tasks_module_3b import make_transition_plot


@task.graph()
def gray_scott_sweep(
    param_sweep: Annotated[dict, dynamic(dict)],
    command: orm.InstalledCode,
) -> namespace(
    transition_plot=orm.SinglefileData,
    variance_V=dynamic(float),
    mean_V=dynamic(float),
):
    """Sweep gray_scott_pipeline over param_sweep and reduce to a transition plot."""
    with Map(param_sweep) as map_zone:
        result = gray_scott_pipeline(
            parameters=map_zone.item.value,
            command=command,
        )
        map_zone.gather({
            'variance_V': result.variance_V,
            'mean_V': result.mean_V,
        })

    plotted = make_transition_plot(variances=map_zone.outputs.variance_V)

    return {
        'transition_plot': plotted.result,
        'variance_V': map_zone.outputs.variance_V,
        'mean_V': map_zone.outputs.mean_V,
    }
```

Its signature uses two annotations you have not seen yet:

- `dynamic(dict)` marks `param_sweep` as a dict whose keys are only known at runtime, one entry (itself a parameter dict) per iteration.
- `namespace(...)` declares several named outputs at once: a fixed `transition_plot`, plus `dynamic(float)` outputs that the engine fills in with one value per iteration.

:::{important}
Two things to watch with `Map`:

- The keys of your source dict become labels in the provenance graph and the names of the gathered outputs, so use meaningful, identifier-safe keys (`F_0_040`, not an integer index). **Avoid dots**: WorkGraph treats them as namespace separators and will silently collapse entries.
- `map_zone.item.key` and `map_zone.item.value` are sockets, not Python values. You can pass them to tasks, but you cannot branch on them or build strings from them inside the graph function.
:::

That's the blueprint; no execution yet.
We build a `param_sweep` dict with one entry per iteration, printing each as we go so you can see what flows into the `Map`:

```{code-cell} ipython3
# {label: parameters} for Map to iterate over. Each key names one map iteration
# in the provenance graph; WorkGraph treats '.' as a namespace separator, so
# encode the F value with underscores (F_0_040, not F_0.040).
param_sweep = {}
print(f'{len(F_VALUES)} parameter sets (only F varies):')
for f_val in F_VALUES:
    key = f'F_{f_val:.3f}'.replace('.', '_')
    param_sweep[key] = BASE_PARAMS | {'F': f_val}
    print(f'  {key:<10}  ->  F = {f_val}')
```

Now `.build(...)` with these concrete inputs:

```{code-cell} ipython3
wg_sweep = gray_scott_sweep.build(
    param_sweep=param_sweep,
    command=gsrd_code,
)
```

The sweep graph contains the same `gray_scott_pipeline` sub-graph as before, now wrapped in a single `map_zone`. Even though we are about to run `gsrd` many times, the **build-time graph stays compact**: `Map` declares "run these tasks once per item in `param_sweep`", but the engine only creates the per-iteration sub-workflows when the graph actually runs.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg_sweep
```

`.run()` to launch the sweep:

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg_sweep.run()
```

Running the workflow returns its outputs: the `transition_plot` artifact, plus the gathered `variance_V` and `mean_V`, each a namespace keyed by the `Map` source keys.

```{code-cell} ipython3
# `._value` unwraps an output namespace into a plain dict. This is the current
# WorkGraph API for reading gathered outputs (may become public in future).
wg_sweep.outputs._value
```

Reading those values out, variance and mean side by side for each `F`:

```{code-cell} ipython3
variances = wg_sweep.outputs.variance_V._value
means = wg_sweep.outputs.mean_V._value

for key in sorted(variances):
    print(f"{key}: variance(V) = {float(variances[key].value):.4e}, mean(V) = {float(means[key].value):.4e}")
```

The numbers are the same as Module 2's sweep (same simulation, same parameters).
What changed is the *shape* of the provenance: instead of a long flat list of disconnected processes, the sweep is one workflow node that branches into one sub-workflow per `F` value and recombines through `make_transition_plot`:

```{code-cell} ipython3
print(f"Sweep WorkGraph PK: {wg_sweep.process.pk}")
%verdi process status {wg_sweep.process.pk}
```

`verdi process show` complements that with the node's full inputs and outputs; the table is long, so it's folded here:

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi process show {wg_sweep.process.pk}
```

Time to bring out the magnifying glass. 🔍
Here's the same hierarchy rendered as a provenance graph:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
from include.plotting import plot_provenance

plot_provenance(wg_sweep.process)
```

It's deliberately busy: every input, output, and linked sub-process is represented.
The point here is not to read it in detail but to see how rich the provenance becomes *for free* as workflows nest.
For a zoomable view, right-click the image and open it in a new tab, or run `verdi node graph generate <PK>` from the command line to get a standalone SVG.

And finally, the workflow's *real* output: the transition curve PNG produced by the reduction step inside the workflow itself, loaded from the database via its process node:

```{code-cell} ipython3
from IPython.display import Image

# Load the transition plot from the stored process node, not the live Python object.
sweep_node = orm.load_node(wg_sweep.process.pk)
img_bytes = sweep_node.outputs.transition_plot.get_content(mode='rb')

Image(img_bytes)
```

The curve's two regimes look strikingly different in real space: below the transition a rich pattern forms; above it the pattern dissolves.

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

## A 2D scan: feed rate &times; kill rate

Now that we have the workflow blueprint, we can expand it to a full 2D scan.
The classic Gray-Scott phase diagram is two-dimensional: the pattern type depends on both the feed rate `F` and the kill rate `k`, but so far we have varied only `F`.
Because `gray_scott_sweep` is parameter-agnostic, extending to a 2D grid means changing nothing but the contents of `param_sweep`.

We use a 5&times;5 grid that straddles the **boundary** of the pattern-forming region.
Inside the band, `variance(V)` is of order `1e-2`; near the edge it drops by an order of magnitude as the V field starts decaying toward a trivial steady state.

```{code-cell} ipython3
F_GRID = [0.040, 0.045, 0.050, 0.055, 0.060]
K_GRID = [0.061, 0.062, 0.063, 0.064, 0.065]

param_sweep_2d = {}
for f in F_GRID:
    for k in K_GRID:
        # Map keys must be valid identifiers (letters, digits, underscores
        # only); encode both 'F = 0.040' and 'k = 0.060' as `F_0_040_k_0_060`.
        f_key = f'F_{f:.3f}'.replace('.', '_')
        k_key = f'k_{k:.3f}'.replace('.', '_')
        key = f'{f_key}_{k_key}'
        param_sweep_2d[key] = {**BASE_PARAMS, 'F': f, 'k': k}

print(f'{len(param_sweep_2d)} parameter sets ({len(F_GRID)} F values x {len(K_GRID)} k values)')
```

The same `gray_scott_sweep` graph drives both the 1D and 2D scans; only the input dict changes.
The `make_transition_plot` reduction still runs and produces its 1D transition curve, but for the 2D case we use the gathered `variance_V` outputs directly and reshape them into a 5&times;5 matrix for plotting a heatmap instead.

```{code-cell} ipython3
wg_2d = gray_scott_sweep.build(
    param_sweep=param_sweep_2d,
    command=gsrd_code,
)
```

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg_2d
```

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg_2d.run()
```

Render the gathered variances as a heatmap. The plotting helper lives in {download}`include/plotting.py`; it does the bookkeeping (map keys back to `(F, k)`, floor non-positive entries for the log-norm, build the figure) so the cell stays a one-liner:

```{code-cell} ipython3
from include.plotting import plot_2d_variance_heatmap

plot_2d_variance_heatmap(
    variances=wg_2d.outputs.variance_V._value,
    param_sweep=param_sweep_2d,
    f_grid=F_GRID,
    k_grid=K_GRID,
)
```

The heatmap shows the edge of the **pattern-forming region** of the classic Gray-Scott phase diagram. High-variance cells (bright) develop the spots, stripes, and labyrinths the system is famous for; the low-variance corner is where the pattern dies out.
Twenty-five simulations, one workflow node, full provenance attached.

## Next steps

You now have the core building blocks: tracked external codes, structured data, calcfunctions, and reusable workflows.
The remaining modules can be tackled in whatever order matches your needs, since they each pick up an independent thread:

- {ref}`Module 4 <tutorial:module4>`: running on remote HPC clusters
- {ref}`Module 5 <tutorial:module5>`: querying the database with the `QueryBuilder`
- {ref}`Module 6 <tutorial:module6>`: more advanced workflow patterns (conditionals, dynamic graphs, sub-workflow composition)
- {ref}`Module 7 <tutorial:module7>`: handling failures and recovering from them

## Further reading

- AiiDA's workflow concepts in depth: {ref}`topics:workflows`
- CalcJob concept (for `ShellJob` background): {ref}`topics:calculations:concepts:calcjobs`
- Calcfunctions refresher: {ref}`topics:processes:functions`
- Control flow (`If`, `While`, dynamic graph construction): {ref}`Module 6 <tutorial:module6>`
- WorkGraph imperative form (`with WorkGraph() as wg:`) and `spec` helpers: [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io)
- Running versus submitting processes: {ref}`topics:processes:usage:launching`
- The AiiDA daemon (architecture and management): {ref}`topics:daemon`, {ref}`how-to:manage-daemon`
