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
uv pip install "aiida-core>=2.9" "aiida-shell>=0.9.0" git+https://github.com/GeigerJ2/aiida-workgraph.git@fix/map-zone-output-retrieval matplotlib git+https://github.com/aiidateam/gsrd.git

# or, without uv:

pip install "aiida-core>=2.9" "aiida-shell>=0.9.0" git+https://github.com/GeigerJ2/aiida-workgraph.git@fix/map-zone-output-retrieval matplotlib git+https://github.com/aiidateam/gsrd.git
```
:::

:::{note}
This module continues {ref}`Module 3a <tutorial:module3a>`, reusing the same tutorial profile and the `gray_scott_pipeline` workflow built there.
If you are following along locally, work through {ref}`Module 3a <tutorial:module3a>` first: this module builds directly on it.
:::

```{code-cell} ipython3
:tags: [hide-cell]
:mystnb:
:    code_prompt_show: 'Show the setup code (same as Module 1)'
:    code_prompt_hide: 'Hide the setup code (same as Module 1)'

# Set up the tutorial's sandbox profile (created in Module 1; reused here).
from pathlib import Path

if not Path('include/tutorial_plumbing.py').exists():
    import urllib.request

    Path('include').mkdir(exist_ok=True)
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/GeigerJ2/aiida-core/docs/integrate-tutorials/docs/source/tutorials/include/tutorial_plumbing.py',
        'include/tutorial_plumbing.py',
    )

%run -i include/tutorial_plumbing.py
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
    'grid_size': 128,
    'du': 0.16,
    'dv': 0.08,
    'F': 0.04,
    'k': 0.060,
    'dt': 1.0,
    'n_steps': 10000,
    'seed': 42,
}
F_VALUES = [0.040, 0.043, 0.045, 0.047, 0.048, 0.049, 0.050]
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
Inside the zone, `map_zone.key` and `map_zone.value` expose the current entry as sockets you wire into tasks like any other output.
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

Now the sweep workflow itself. Like `gray_scott_pipeline` in {ref}`Module 3a <tutorial:module3a>`, `gray_scott_sweep` is a `@task.graph()`-decorated function whose body assembles the graph; the new piece is the `Map` zone wrapping the pipeline call.

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
            parameters=map_zone.value,
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

- `dynamic(...)` marks a namespace whose entries arrive one per `Map` iteration, keyed at runtime. It appears on both sides here: `dynamic(dict)` makes `param_sweep` one parameter dict per iteration, and `variance_V=dynamic(float)` collects one `Float` per iteration, keyed by the source keys.
- `namespace(...)` bundles several named outputs into one return type. In {ref}`Module 3a <tutorial:module3a>` every output was fixed, so a `TypedDict` (`GrayScottOutputs`) sufficed; a `TypedDict` can only declare fixed fields, so here, where `variance_V` and `mean_V` vary per iteration, `namespace(...)` lets you mix the fixed `transition_plot` with those `dynamic(float)` outputs.

:::{important}
Two things to watch with `Map`:

- The keys of your source dict become labels in the provenance graph and the names of the gathered outputs, so use meaningful, identifier-safe keys (`F_0_040`, not an integer index). **Avoid dots**: WorkGraph treats them as namespace separators and will silently collapse entries.
- `map_zone.key` and `map_zone.value` are sockets, not Python values. You can pass them to tasks, but you cannot branch on them or build strings from them inside the graph function.
:::

Again, that's the blueprint; no execution yet.
We now construct a `param_sweep` dict with one entry per iteration, printing each as we go so you can see what flows into the `Map`:

```{code-cell} ipython3
# {label: parameters} for Map to iterate over. Each key names one map iteration
# in the provenance graph; WorkGraph treats '.' as a namespace separator, so
# encode the F value with underscores (F_0_040, not F_0.040).
print(f'{len(F_VALUES)} parameter sets (only F varies):')
param_sweep = {}
for f_val in F_VALUES:
    key = f'F_{f_val:.3f}'.replace('.', '_')
    param_sweep[key] = BASE_PARAMS | {'F': f_val}
    print(f'  {key:<7}  ->  F = {f_val}')
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

`.run()` launches the sweep and, as in {ref}`Module 3a <tutorial:module3a>`, returns its resolved outputs, which we capture in `results`:

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

results = wg_sweep.run()
```

`results` holds the `transition_plot` artifact plus the gathered `variance_V` and `mean_V`, each a dict keyed by the `Map` source keys:

```{code-cell} ipython3
for label, value in results.items():
    if isinstance(value, orm.Node):
        print(f'{label:<16}{type(value).__name__:<16}{value}')
    else:
        print(f'{label:<16}{type(value).__name__:<16}{len(value)} entries')
```

Reading those values out, variance and mean side by side for each `F`:

```{code-cell} ipython3
variances = results['variance_V']
means = results['mean_V']

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

And, here's the same hierarchy rendered as a provenance graph:

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

The curve's two regimes look strikingly different in the simulated concentration fields: below the transition a rich pattern forms; above it the pattern dissolves.

::::{grid} 2
:gutter: 2

:::{grid-item}
```{image} https://raw.githubusercontent.com/aiidateam/gsrd/2b43234ba82c796fd082278f7b0f874c35829d89/gallery/fields.png
:width: 100%
:align: center
```
*Below the transition (`F=0.040`): rich spatial pattern.*
:::

:::{grid-item}
```{image} https://raw.githubusercontent.com/aiidateam/gsrd/2b43234ba82c796fd082278f7b0f874c35829d89/gallery/dissolved.png
:width: 100%
:align: center
```
*Above the transition (`F=0.050`): pattern dissolved.*
:::
::::

## A 2D scan: feed rate &times; kill rate

Now that we have the workflow blueprint, we can expand it to a full 2D scan.
The classic Gray-Scott phase diagram is two-dimensional: the pattern type depends on both the feed rate `F` and the kill rate `k`, but so far we have varied only `F`.
Because `gray_scott_sweep` is parameter-agnostic, extending to a 2D grid means changing nothing but the contents of `param_sweep`. The `Map` itself still iterates a flat `{key: parameters}` mapping; we flatten the `F`&times;`k` grid into it by encoding both values in each key (`F_0_044_k_0_063`), and recover the 2D structure only at plotting time.

We keep the scan **coarse** on purpose, a 5&times;5 grid chosen to bracket the **pattern-forming band** while keeping it to a manageable 25 simulations.
Patterns form only within a band of kill rates: inside it `variance(V)` is of order `1e-2`, but step off either edge and the field decays to a flat, trivial steady state, with the variance collapsing by orders of magnitude.

Twenty-five simulations is a lot to run inside a docs page, so we do not execute this scan inline.
Here is the full code, driven by the exact same `gray_scott_sweep` graph; only the input dict grows from a 1D list to a 2D grid. Run it yourself to reproduce the heatmap shown below.

```python
F_GRID = [0.038, 0.044, 0.050, 0.056, 0.062]
K_GRID = [0.059, 0.061, 0.063, 0.065, 0.067]

param_sweep_2d = {}
for f in F_GRID:
    for k in K_GRID:
        # Map keys must be valid identifiers (letters, digits, underscores
        # only); encode both 'F = 0.044' and 'k = 0.063' as `F_0_044_k_0_063`.
        f_key = f'F_{f:.3f}'.replace('.', '_')
        k_key = f'k_{k:.3f}'.replace('.', '_')
        key = f'{f_key}_{k_key}'
        param_sweep_2d[key] = {**BASE_PARAMS, 'F': f, 'k': k}

# The same graph drives both the 1D and 2D scans; only the input dict changes.
wg_2d = gray_scott_sweep.build(param_sweep=param_sweep_2d, command=gsrd_code)
results_2d = wg_2d.run()

# The plotting helper (include/plotting.py) does the bookkeeping: map keys back
# to (F, k), clamp dead-zone entries below 1e-6 for the log-norm, build the
# figure. That keeps the plotting call a one-liner.
from include.plotting import plot_2d_variance_heatmap

plot_2d_variance_heatmap(
    variances=results_2d['variance_V'],
    param_sweep=param_sweep_2d,
    f_grid=F_GRID,
    k_grid=K_GRID,
)
```

```{image} https://raw.githubusercontent.com/aiidateam/gsrd/2b43234ba82c796fd082278f7b0f874c35829d89/gallery/heatmap.png
:width: 90%
:align: center
:alt: Heatmap of variance(V) over a 5x5 feed-rate-by-kill-rate grid
```

The heatmap shows the **pattern-forming band** of the classic Gray-Scott phase diagram: a bright vertical strip of high variance, where the spots, stripes, and labyrinths the system is famous for develop, flanked by dark dead zones on either side where the field decays to a flat steady state.

## Next steps

You now have the core building blocks: tracked external codes, structured data, calcfunctions, and reusable workflows.
Further modules build on these fundamentals and will follow: running on remote HPC clusters, querying provenance at scale with the `QueryBuilder`, advanced workflow patterns (conditionals, dynamic graphs, sub-workflow composition), and recovering from failures with error handlers.

To apply these skills to real materials-science calculations, [aiida-quantumespresso](https://aiida-quantumespresso.readthedocs.io/) provides AiiDA workflows for [Quantum ESPRESSO](https://www.quantum-espresso.org/), from single self-consistent-field runs to automated band structures, if you want to drive DFT codes with AiiDA. For other codes, the [AiiDA plugin registry](https://aiida.net/plugin-registry/) lists plugins that connect AiiDA to a range of other simulation tools.

## Further reading

- AiiDA's workflow concepts in depth: {ref}`topics:workflows`
- `aiida-shell` (the `ShellJob` launcher used in the pipeline): [aiida-shell documentation](https://aiida-shell.readthedocs.io)
- Calcfunctions refresher: {ref}`topics:processes:functions`
- Alternative workflow construction APIs WorkGraph offers (beyond the `@task.graph()` decorator used here, including `If`/`While` control flow): [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io)
- Running versus submitting processes: {ref}`topics:processes:usage:launching`
- The AiiDA daemon (architecture and management): {ref}`topics:daemon`, {ref}`how-to:manage-daemon`
- Tips for running real-world production calculations on HPC resources: {ref}`how-to:real-world-tricks`
