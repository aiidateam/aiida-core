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
# Module 3b: Turning `for`-loops into workflows with `Map`

<!-- TODO: re-enable once the md->ipynb conversion script is verified
:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module3b.ipynb` {octicon}`download`
:::
-->

:::{note}
This module continues {ref}`Module 3a <tutorial:module3a>`, reusing the same tutorial profile and the `gray_scott_pipeline` workflow built there.
If you are following along locally, work through {ref}`Module 3a <tutorial:module3a>` first: the sweep below wraps its pipeline.
:::

## What you will learn

After this module, you will be able to:

- Run a workflow over many input sets at once with WorkGraph's `Map`, replacing a plain Python `for`-loop with tracked, parallel, fan-out execution
- Gather per-iteration outputs back into a single result
- Reuse the same workflow for a 2D scan by changing only its input

:::{note} Setup
This module uses AiiDA, `aiida-shell`, and `aiida-workgraph`:

```bash
pip install aiida-core aiida-shell aiida-workgraph
```
:::

```{code-cell} ipython3
# Set up the tutorial's isolated sandbox profile (same as Module 1).
# `%load_ext aiida` enables the `%verdi` magic; `%run` creates or loads the
# shared `tutorial-<hash>` profile, so data from earlier modules is available.
%load_ext aiida
%run -i include/setup_tutorial.py
```

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

:::{dropdown} `gray_scott_pipeline` (from Module 3a, in `include/workflows.py`)
```{literalinclude} include/workflows.py
:language: python
:pyobject: gray_scott_pipeline
```
:::

## Integrating the for-loop into the workflow

In Module 2, the parameter sweep was a Python `for` loop calling the pipeline for each `F` value.
But a `for` loop is not an AiiDA process: it doesn't show up in the provenance, can't be inspected with `verdi`, and can't recover from failures.

WorkGraph's {class}`~aiida_workgraph.Map` lets you run the same sub-workflow over multiple input values, like a parallel `for` loop, but as a single AiiDA workflow with full provenance.
In WorkGraph terminology, a `Map` is a **zone**: a region of the graph that controls how the tasks inside it are scheduled.

:::{important}
Conceptually, a `Map` zone does three things:

1. It takes a **source collection** of the form `{key: value}` and runs the tasks inside the zone once per entry.
2. Inside the zone, it exposes the current key/value via `map_zone.item.key` and `map_zone.item.value`. These are sockets, so you can wire them into tasks just like any other output.
3. At the end of the zone, `map_zone.gather({...})` declares which per-iteration outputs to collect. The gathered outputs become accessible on `map_zone.outputs.<name>` as a namespace keyed by the original source keys.
:::

`Map` is imported alongside the rest of the WorkGraph helpers; its signature and docstring are visible via `help(Map)`:

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show `Map` signature and docstring'
:    code_prompt_hide: 'Hide signature'

help(Map)
```

To close the loop, we add a final **reduction step** to the workflow: a calcfunction `make_transition_plot` ({download}`include/tasks.py`) that takes the gathered `variance_V` `Float` nodes and renders the transition curve as a `SinglefileData` PNG.
The workflow's primary output is then that single artifact: the per-iteration variances "fork out" via `Map`, and the plotting task "joins" them back together.

:::{dropdown} `make_transition_plot` (in `include/tasks.py`)
```{literalinclude} include/tasks.py
:language: python
:pyobject: make_transition_plot
```
:::

:::{tip}
The sweep is wrapped as a `@task.graph()` with two inputs: `param_sweep` and the `Code` to run on.
The blueprint is parameter-agnostic: change the contents of `param_sweep` and you can scan a different parameter (or several at once) without touching the workflow.
:::

The signature of `gray_scott_sweep` uses two helpers from the WorkGraph type system (both already imported at the top of this module):

- `dynamic(dict)` on the input tells WorkGraph that `param_sweep` is a dict whose keys are not known until runtime. Each value is itself a dict (the parameter set for one iteration).
- `namespace(...)` on the return type declares multiple named outputs. Some are fixed (`transition_plot`), others are `dynamic(float)`, meaning the engine will create one output per Map iteration under that name.

```{code-cell} ipython3
from typing import Annotated

from include.tasks import make_transition_plot


@task.graph()
def gray_scott_sweep(
    param_sweep: Annotated[dict, dynamic(dict)],
    command: orm.AbstractCode,
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

:::{important}
A few things to keep in mind about `Map`:

- The source must be a mapping (a `dict` or a socket of a dynamic namespace). Iterating over a plain list is not supported directly. Wrap it into a dict first, using meaningful keys like `F_0_040` rather than integer indices, because those keys will show up in the provenance graph and as the names of the gathered outputs. **Avoid dots in keys**: WorkGraph treats dots as namespace separators, which will silently collapse your entries.
- `map_zone.item.value` is the value for the current iteration, `map_zone.item.key` is its key. Both are sockets, so you can pass them as task inputs, but you cannot use them as ordinary Python values inside the graph function (no `if` on them, no string concatenation).
- After the `with` block, `map_zone.outputs.<name>` gives you a namespace that behaves like a dict of AiiDA nodes, keyed by the original source keys.
:::

That's the blueprint; no execution yet.
We need a `param_sweep` dict with one entry per iteration.
The folded cell below constructs it; the visible cell prints what's about to flow in:

```{code-cell} ipython3
:tags: ["hide-cell"]

# {label: parameters} for Map to iterate over. Keys become the names of
# each map iteration in the provenance graph.
param_sweep = {}
for f_val in F_VALUES:
    key = f'F_{f_val:.3f}'.replace('.', '_')  # WorkGraph treats `.` as namespace separator, so use `_`
    param_sweep[key] = BASE_PARAMS | {'F': f_val}
```

```{code-cell} ipython3
# Show what's flowing into the Map.
print(f'{len(param_sweep)} parameter sets (only F varies):')
for key, val in param_sweep.items():
    print(f'  {key:<10}  ->  F = {val["F"]}')
```

Now `.build(...)` with concrete inputs:

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

:::{note}
We called `.run()`, which blocks your Python session until the whole graph has finished.
The alternative, `.submit()`, hands the workflow to the AiiDA daemon and returns immediately, freeing your session while the daemon drives execution in the background.
In both cases the sub-workflows inside the `Map` zone run concurrently (the engine schedules them as independent processes); the only difference is whether *your session* waits for the result or not.
For a tutorial `.run()` is convenient because the outputs are available right away.
:::

The per-iteration variances are now reachable directly on the workflow's outputs:

```{code-cell} ipython3
# Access per-iteration variances via the workflow output namespace.
# `._value` unwraps the namespace into a plain dict; this is the current
# WorkGraph API for accessing gathered outputs (may become public in future).
variances = wg_sweep.outputs.variance_V._value

for key in sorted(variances):
    print(f"  {key}: variance(V) = {float(variances[key].value):.4e}")
```

The numbers are the same as Module 2's sweep (same simulation, same parameters).
What changed is the *shape* of the provenance: instead of a long flat list of disconnected processes, the sweep is one workflow node that fans out into per-`F` sub-workflows and fans back in through `make_transition_plot`:

```{code-cell} ipython3
print(f"Sweep WorkGraph PK: {wg_sweep.process.pk}")
%verdi process status {wg_sweep.process.pk}
```

🔭 Time to bring out the binoculars.
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
The point is not to read it in detail (you can't, it's tiny in the rendered docs) but to see how rich the provenance becomes *for free* as workflows nest.
For a zoomable view, right-click the image and open it in a new tab, or run `verdi node graph generate <PK>` from the command line to get a standalone SVG.

And finally, the workflow's *real* output: the transition curve PNG produced by the reduction step inside the workflow itself, loaded from the database via its process node:

```{code-cell} ipython3
from IPython.display import Image

# Load the transition plot from the stored process node, not the live Python object.
sweep_node = orm.load_node(wg_sweep.process.pk)
with sweep_node.outputs.transition_plot.open(mode='rb') as fh:
    img_bytes = fh.read()

Image(img_bytes)
```

`verdi process show` works on the sweep workflow node too, but its per-node table is long, so its output is folded here:

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi process show {wg_sweep.process.pk}
```

## A 2D scan: feed rate &times; kill rate

So far the sweep has varied only `F`. The classic Gray-Scott phase diagram is two-dimensional, though: the pattern type depends on both the feed rate `F` and the kill rate `k`.
The point of wrapping the sweep as a `@task.graph()` was that it is parameter-agnostic; we can scan a 2D grid by changing nothing but the contents of `param_sweep`.

We use a 5&times;5 grid that straddles the **boundary** of the pattern-forming region.
Inside the band, `variance(V)` is of order `1e-2`; near the edge it drops by an order of magnitude as the V field starts decaying toward a trivial steady state.
The grid is chosen so that every (F, k) combination still produces a `results.npz` file; points that land fully outside the band cause `gsrd` to skip the output file entirely, which would make the `ShellJob` fail for those iterations.

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
The `make_transition_plot` reduction still runs and produces its 1D transition curve, but for the 2D case we use the gathered `variance_V` outputs directly and reshape them into a 5&times;5 matrix for the heatmap.

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

The heatmap shows the edge of the **pattern-forming region** of the classic Gray-Scott phase diagram. High-variance cells (bright) develop the spots, stripes, and labyrinths the system is famous for; toward the upper-right corner, `variance(V)` drops by an order of magnitude as the V field begins decaying toward a trivial steady state.
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
