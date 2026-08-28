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
uv pip install "aiida-core>=2.9" "aiida-shell>=0.9.0" "aiida-workgraph>=0.9.0" matplotlib "gsrd>=0.2.0"
```
:::

:::{note}
This module continues {ref}`Module 3a <tutorial:module3a>`, reusing the same tutorial profile and the `gray_scott_pipeline` workflow built there.
If you are following along locally, work through {ref}`Module 3a <tutorial:module3a>` first: this module builds directly on it.
:::

```{code-cell} ipython3
:tags: [hide-cell]
:mystnb:
:    code_prompt_show: 'Show the profile-setup code (same as Module 1)'
:    code_prompt_hide: 'Hide the profile-setup code'

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
:tags: [hide-cell]
:mystnb:
:    code_prompt_show: 'Show the connect-and-daemon code (same as Module 1)'
:    code_prompt_hide: 'Hide the connect-and-daemon code'

# Load the profile into this kernel, start the daemon, and get a handle on the gsrd Code.
from aiida import load_profile
from aiida.orm import load_code

load_profile(PROFILE_NAME, allow_switch=True)
!verdi -p {PROFILE_NAME} daemon start
gsrd_code = load_code('gsrd@localhost')

%load_ext aiida
```

```{code-cell} ipython3
:tags: [hide-cell]
:mystnb:
:    code_prompt_show: 'Show the plot_provenance helper (same as Module 1)'
:    code_prompt_hide: 'Hide the plot_provenance helper'

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

- Run a workflow over many input sets at once with WorkGraph's `Map`, turning a plain Python `for`-loop into a single tracked, parallel workflow
- Gather per-iteration outputs back into a single result
- Reuse the same workflow for a 2D scan by changing only its input

## Setup

We build on the `gray_scott_pipeline` workflow from {ref}`Module 3a <tutorial:module3a>`.
Because each notebook runs in its own kernel, we redefine it here (the same code as Module 3a); the imports and parameters for this module come first:

```{code-cell} ipython3
from aiida import orm

from aiida_workgraph import Map, task, dynamic, namespace

# Base parameters (same as Module 2); a finer set of F values to scan the transition.
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

The pipeline definition is unchanged from Module 3a, folded here (it also brings back the Module 2 calcfunctions it wraps):

```{code-cell} ipython3
:tags: [hide-cell]
:mystnb:
:    code_prompt_show: 'Show the Module 3a pipeline'
:    code_prompt_hide: 'Hide the Module 3a pipeline'

# The gray_scott_pipeline workflow from Module 3a (with the Module 2 calcfunctions it
# wraps), redefined here so this notebook's kernel has it.
import re
from typing import TypedDict

import yaml

from aiida import engine
from aiida_workgraph import shelljob


class ParseOutputs(TypedDict):
    variance_V: orm.Float
    mean_V: orm.Float


VARIANCE_RE = re.compile(r'Variance of V field\s*:\s*([\d.eE+-]+)')
MEAN_RE = re.compile(r'Mean\s+of V field\s*=\s*([\d.eE+-]+)')


@engine.calcfunction
def prepare_input(parameters: orm.Dict) -> orm.SinglefileData:
    """Convert a Dict of parameters into a SinglefileData YAML file."""
    content = yaml.dump(parameters.value)
    return orm.SinglefileData.from_string(content, filename='input.yaml')


@engine.calcfunction
def parse_output(stdout: orm.SinglefileData) -> ParseOutputs:
    """Extract variance_V and mean_V scalars from the gsrd stdout log."""
    text = stdout.get_content(mode='r')
    variance_match = VARIANCE_RE.search(text)
    mean_match = MEAN_RE.search(text)
    if variance_match is None or mean_match is None:
        msg = "gsrd stdout did not contain 'Variance of V field' / 'Mean of V field' diagnostics"
        raise ValueError(msg)
    return {
        'variance_V': orm.Float(float(variance_match.group(1))),
        'mean_V': orm.Float(float(mean_match.group(1))),
    }


prepare_input_task = task()(prepare_input)
parse_output_task = task()(parse_output)


class GrayScottOutputs(TypedDict):
    variance_V: orm.Float
    mean_V: orm.Float
    results_npz: orm.SinglefileData


@task.graph()
def gray_scott_pipeline(
    parameters: orm.Dict,
    command: orm.InstalledCode,
) -> GrayScottOutputs:
    """Run one gsrd simulation and parse its results (variance_V, mean_V, results_npz)."""
    prepared = prepare_input_task(parameters=parameters)
    simulation = shelljob(
        command=command,
        arguments=['{input}'],
        nodes={'input': prepared.result},
        outputs=['results.npz'],
    )
    parsed = parse_output_task(stdout=simulation.stdout)
    return {
        'variance_V': parsed.variance_V,
        'mean_V': parsed.mean_V,
        'results_npz': simulation.results_npz,
    }
```

## Integrating the for-loop into the workflow

You now already have run the pipeline twice over multiple inputs by looping in plain Python: in {ref}`Module 2 <tutorial:module2>` with the plain `run_pipeline` function over a handful of `F` values, and in {ref}`Module 3a <tutorial:module3a>` with the `gray_scott_pipeline` workflow over a few parameter sets.
Now picture a full sweep instead: the same pipeline over a whole range of `F` values.
The natural reach is again a `for` loop, but a `for` loop is not an AiiDA process: it doesn't show up in the provenance, can't be inspected with `verdi`, and can't recover from failures.
It also runs strictly sequentially, waiting for each `F` value to finish before starting the next.

WorkGraph's {class}`~aiida_workgraph.Map` is the workflow analogue of Python's built-in `map(fn, iterable)`: where `map()` applies a function to each item of a sequence, `Map` applies the same sub-workflow to each entry of your inputs, running the iterations in parallel as a single tracked AiiDA workflow.
In WorkGraph terminology, a `Map` is a **zone**: a region of the graph that controls how the tasks inside it are scheduled.

A `Map` zone works in three parts:

- **Source mapping**: it takes a mapping of the form `{key: value}` and runs the tasks inside it once per entry.
- **Inside the zone**: `map_zone.key` and `map_zone.value` expose the current entry as sockets you wire into tasks like any other output.
- **Gather**: `map_zone.gather({...})` picks which per-iteration outputs to collect; afterwards they are available as `map_zone.outputs.<name>`, a namespace keyed by the original source keys.

To close the loop, we add a final **reduction step** to the workflow: a `make_transition_plot` task that takes the gathered `variance_V` `Float` nodes and renders the transition curve as a `SinglefileData` PNG (its body is matplotlib, folded below).
The workflow's primary output is then that single artifact: `Map` produces one variance per parameter set, and the plotting task combines them into a single figure.

```{code-cell} ipython3
:tags: [hide-cell]
:mystnb:
:    code_prompt_show: 'Show make_transition_plot (matplotlib)'
:    code_prompt_hide: 'Hide make_transition_plot'

import io
from typing import Annotated


@task()
def make_transition_plot(variances: Annotated[dict, dynamic(float)]) -> orm.SinglefileData:
    """Plot variance(V) vs feed rate F from the gathered sweep results."""
    import matplotlib.pyplot as plt

    # Sweep keys encode the feed rate as `F_0_038` (= 0.038). Keys from a
    # multi-parameter sweep (e.g. `F_0_040_k_0_060`) don't fit that 1D shape,
    # so we skip them and plot only the points that sit on a single F axis.
    points = {}
    for key, value in variances.items():
        parts = key.split('_')
        if len(parts) == 3 and parts[0] == 'F':
            points[float(f'{parts[1]}.{parts[2]}')] = float(value)

    f_values = sorted(points)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(f_values, [points[f] for f in f_values], 'o-')
    ax.set_xlabel('Feed rate F')
    ax.set_ylabel('variance(V)')
    ax.set_yscale('log')
    ax.set_title('Pattern transition curve')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    plt.close(fig)

    return orm.SinglefileData.from_bytes(buf.getvalue(), filename='transition_curve.png')
```

Now the sweep workflow itself. Like `gray_scott_pipeline` in {ref}`Module 3a <tutorial:module3a>`, `gray_scott_sweep` is a `@task.graph()`-decorated function whose body assembles the graph; the new piece is the `Map` zone wrapping the pipeline call.

```{code-cell} ipython3
from typing import Annotated


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

    plot = make_transition_plot(variances=map_zone.outputs.variance_V)

    return {
        'transition_plot': plot.result,
        'variance_V': map_zone.outputs.variance_V,
        'mean_V': map_zone.outputs.mean_V,
    }
```

Note where the two steps sit relative to the `Map` zone: `map_zone.gather(...)` is the last step *inside* it, naming the per-iteration outputs to accumulate, while `make_transition_plot` runs *once, after* the zone closes, reducing the gathered results into the final plot.

The signature also uses two annotations you have not seen yet:

- `dynamic(...)` marks a namespace whose entries are only known at runtime: the `Map` decides how many there are and what they are keyed by (its source-dict keys), so you cannot list them as fixed fields when writing the function. It appears on both sides here: `dynamic(dict)` makes `param_sweep` one parameter dict per iteration, and `variance_V=dynamic(float)` collects one `Float` per iteration, keyed by those same source keys.
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
    print(
        f"{key}: variance(V) = {float(variances[key].value):.4e}, "
        f"mean(V) = {float(means[key].value):.4e}"
    )
```

The numbers are exactly what you would get by running the pipeline once per `F` yourself, as in the earlier modules: the simulation is unchanged.
What changed is the *shape* of the provenance: instead of separate runs with no parent node tying them together, the sweep is one workflow node that branches into one sub-workflow per `F` value and recombines through `make_transition_plot`:

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
# plot_provenance is defined in the setup cell above.
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
```{image} https://raw.githubusercontent.com/aiidateam/gsrd/v0.2.0/gallery/fields.png
:width: 100%
:align: center
```
*Below the transition (`F=0.040`): rich spatial pattern.*
:::

:::{grid-item}
```{image} https://raw.githubusercontent.com/aiidateam/gsrd/v0.2.0/gallery/dissolved.png
:width: 100%
:align: center
```
*Above the transition (`F=0.050`): pattern dissolving.*
:::
::::

:::{note}
The sweep stops at `F=0.050` on purpose.
At `k=0.060` the pattern holds up to about `F=0.046`, then collapses across a sharp cliff: `variance(V)` falls to `~2e-3` at `F=0.050` and, just beyond, to essentially zero (a flat, trivial steady state) that sits off the bottom of the log axis.
`gsrd` runs fine at higher `F` (the 2D scan below reaches `F=0.062`); extending the curve would only add an unplottable tail, so stopping here is a physics choice, not a limit of the code.
:::

## A 2D scan: feed rate &times; kill rate

Now that we have the workflow blueprint, we can expand it to a full 2D scan.
The classic Gray-Scott phase diagram is two-dimensional: the pattern type depends on both the feed rate `F` and the kill rate `k`, but so far we have varied only `F`.
Because `gray_scott_sweep` is parameter-agnostic, extending to a 2D grid means changing nothing but the contents of `param_sweep`. The `Map` itself still iterates a flat `{key: parameters}` mapping; we flatten the `F`&times;`k` grid into it by encoding both values in each key (`F_0_044_k_0_063`), and recover the 2D structure only at plotting time.

We keep the scan **coarse** on purpose, a 5&times;5 grid chosen to bracket the **pattern-forming band** while keeping it to a manageable 25 simulations.
Patterns form only within a band of kill rates: inside it `variance(V)` is of order `1e-2`, but step off either edge and the field decays to a flat, trivial steady state, with the variance collapsing by orders of magnitude.

Twenty-five simulations is a lot to run inside a docs page, so we do not execute this scan inline.
The full code is folded below, driven by the exact same `gray_scott_sweep` graph; only the input dict grows from a 1D list to a 2D grid. Run it yourself to reproduce the heatmap shown below.

:::{dropdown} Full 2D-scan code
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

# Reshape the flat {key: Float} results back onto the (F, k) grid, then plot with
# gsrd's helper (it clamps dead-zone entries below 1e-6 for the log colour scale).
import matplotlib.pyplot as plt
import numpy as np

from gsrd.plotting import plot_variance_heatmap

grid = np.full((len(F_GRID), len(K_GRID)), np.nan)
for key, value in results_2d['variance_V'].items():
    params = param_sweep_2d[key]
    grid[F_GRID.index(params['F']), K_GRID.index(params['k'])] = float(value.value)

plot_variance_heatmap(grid, F_GRID, K_GRID, dead_threshold=1e-6)
plt.show()
```
:::

```{image} https://raw.githubusercontent.com/aiidateam/gsrd/v0.2.0/gallery/heatmap.png
:width: 90%
:align: center
:alt: Heatmap of variance(V) over a 5x5 feed-rate-by-kill-rate grid
```

The heatmap shows the **pattern-forming band** of the classic Gray-Scott phase diagram: a bright vertical strip of high variance, where the spots, stripes, and labyrinths the system is famous for develop, flanked by dark dead zones on either side where the field decays to a flat steady state.

## Next steps

You now have the core building blocks for your work with AiiDA: tracked external codes, structured data, calcfunctions, and reusable workflows.
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
