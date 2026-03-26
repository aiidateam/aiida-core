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

(tutorial:module1)=
# Module 1: Running a Simulation in AiiDA

## What you will learn

After this module, you will be able to:

- Set up an AiiDA profile for storing your data and provenance
- Store data in the AiiDA database and retrieve it
- Wrap a computation as an AiiDA `calcfunction`
- Run and monitor the status of processes
- Explore and visualize the provenance graph

## What you will not learn yet

You cannot yet automatically extract structured data from external code outputs or handle errors — these capabilities will be introduced in {ref}`Module 2 <tutorial:module2>` and {ref}`Module 5 <tutorial:module5>`.

## Setting up your AiiDA profile

An AiiDA **profile** is where all your data, calculations, and provenance are stored.
Before running any calculations, you need one.

If you are working on your own machine, the easiest way is:

```console
$ verdi presto
```

This creates a lightweight local profile using SQLite storage — no PostgreSQL or other external services required.
You can verify that your profile is set up correctly with:

```console
$ verdi status
```

For production use or more advanced setups, see the {ref}`installation guide <installation>`.

:::{tip}
Use `verdi profile list` to see all your profiles and `verdi profile show` to inspect the active one.
:::

The cell below creates a tutorial profile for automated execution of this tutorial.
If you are running locally with your own profile, you can skip it.

```{code-cell} ipython3
:tags: ["hide-cell"]

# Auto-generated tutorial profile for docs build.
# If running locally with your own profile (e.g. from ``verdi presto``),
# replace this cell with:
#
#     from aiida import load_profile
#     load_profile()

import os

from aiida.manage.configuration import create_profile, get_config

%load_ext aiida

profile_name = 'tutorial'
config = get_config()

if profile_name not in config.profile_names:
    create_profile(
        config,
        name=profile_name,
        email='tutorial@aiida.net',
        storage_backend='core.sqlite_dos',
        storage_config={},
        broker_backend=None,
        broker_config=None,
    )
    config.set_option('runner.poll.interval', 1, scope=profile_name)
    config.set_option('warnings.development_version', False, scope=profile_name)
    config.set_default_profile(profile_name, overwrite=True)
    config.store()

from aiida import load_profile

load_profile(profile_name, allow_switch=True)
os.environ['AIIDA_PROFILE'] = profile_name
```

## The simulation code

Throughout this tutorial we use a **reaction–diffusion simulation** (Gray–Scott model) as our running example — see the {ref}`introduction <tutorial:intro>` for the scientific background.

Think of the simulation code as an **external binary** that you would normally run on an HPC cluster (like Quantum ESPRESSO, VASP, or LAMMPS).
You don't need to understand its internals — only its interface:

- **Input**: a dictionary of parameters (`grid_size`, `F`, `k`, `du`, `dv`, `dt`, `n_steps`, `seed`)
- **Output**: a dictionary with the final fields (`U_final`, `V_final`) and scalar diagnostics (`variance_V`, `mean_V`)

The cell below defines the `simulate()` function that we treat as our black-box code.
Click the toggle to inspect it if you are curious — otherwise just move on.

```{code-cell} ipython3
:tags: ["hide-cell"]

# Gray-Scott reaction-diffusion simulation.
# Treat this as a black-box binary — you only need to know its inputs and outputs.

import numpy as np


def _laplacian(Z):
    return (
        -4 * Z
        + np.roll(Z, 1, axis=0)
        + np.roll(Z, -1, axis=0)
        + np.roll(Z, 1, axis=1)
        + np.roll(Z, -1, axis=1)
    )


def simulate(params):
    """Run a Gray-Scott reaction-diffusion simulation."""
    n = params['grid_size']
    du, dv = params['du'], params['dv']
    F, k = params['F'], params['k']
    dt, steps = params['dt'], params['n_steps']

    rng = np.random.default_rng(params.get('seed'))

    U = np.ones((n, n))
    V = np.zeros((n, n))
    r = n // 10
    c = n // 2
    U[c - r : c + r, c - r : c + r] = 0.50
    V[c - r : c + r, c - r : c + r] = 0.25

    for _ in range(steps):
        Lu, Lv = _laplacian(U), _laplacian(V)
        uvv = U * V * V
        U += dt * (du * Lu - uvv + F * (1 - U))
        V += dt * (dv * Lv + uvv - (F + k) * V)

    return {
        'U_final': U,
        'V_final': V,
        'variance_V': float(np.var(V)),
        'mean_V': float(np.mean(V)),
    }
```

## Running the simulation without AiiDA

Let's call the simulation and look at the result:

```{code-cell} ipython3
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

result_raw = simulate(params)

print(f"variance(V) = {result_raw['variance_V']:.4e}")
print(f"mean(V)     = {result_raw['mean_V']:.4e}")
```

```{code-cell} ipython3
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(8, 4))
axes[0].imshow(result_raw['U_final'], cmap='viridis', origin='lower')
axes[0].set_title('U (substrate)')
axes[0].axis('off')
axes[1].imshow(result_raw['V_final'], cmap='inferno', origin='lower')
axes[1].set_title('V (activator)')
axes[1].axis('off')
plt.tight_layout()
plt.show()
```

The simulation works — but the result lives only in local Python variables.
If we close this session, everything is lost: there is no record of *what* parameters were used, *what* code was run, or *what* results were obtained.

## Storing data in AiiDA

AiiDA stores all data as **nodes** in a database.
Let's store our simulation parameters as a {py:class}`~aiida.orm.Dict` node:

```{code-cell} ipython3
from aiida import orm

parameters = orm.Dict(params)
parameters.store()
parameters
```

The node now has a **PK** (primary key, unique within this database) and a **UUID** (universally unique identifier).
We can inspect it with the `verdi` CLI:

```{code-cell} ipython3
!verdi node show {parameters.pk}
```

We can also retrieve the stored dictionary contents through the Python API:

```{code-cell} ipython3
parameters.get_dict()
```

## Wrapping the simulation as a `calcfunction`

A plain Python function produces results, but AiiDA cannot track it.
By adding the {func}`@calcfunction <aiida.engine.processes.functions.calcfunction>` decorator, AiiDA automatically:

1. Stores all input nodes (if not already stored)
2. Creates a **process node** that records the computation
3. Stores all output nodes
4. Links everything in a **provenance graph**

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

Now let's run it:

```{code-cell} ipython3
result = run_simulation(orm.Dict(params))
print(f"variance(V) = {result['variance_V'].value:.4e}")
print(f"mean(V)     = {result['mean_V'].value:.4e}")
```

## Inspecting the process with `verdi`

Unlike a plain function call, AiiDA has recorded everything.
Let's see what processes have been run:

```{code-cell} ipython3
%verdi process list -a
```

We can get more detail on the calculation, including all its inputs and outputs:

```{code-cell} ipython3
calc_pk = result['variance_V'].creator.pk
!verdi process show {calc_pk}
```

We can also inspect individual output nodes:

```{code-cell} ipython3
!verdi node show {result['variance_V'].pk}
```

Other useful inspection commands include `verdi calcjob inputcat <PK>` and `verdi calcjob outputcat <PK>` for viewing the input and output files of CalcJob calculations.

## Exploring the provenance graph

AiiDA automatically builds a **provenance graph** that records exactly how each piece of data was produced:

```{code-cell} ipython3
---
mystnb:
    image:
        align: center
        width: 400px
    figure:
        caption: "Provenance graph of the `run_simulation` calcfunction."
        name: fig_module1_provenance
---
from aiida.tools.visualization import Graph

graph = Graph()
calc_node = orm.load_node(calc_pk)
graph.add_incoming(calc_node, annotate_links="both")
graph.add_outgoing(calc_node, annotate_links="both")
graph.graphviz
```

In the graph:
- **Green ellipses** are data nodes (inputs and outputs)
- **Rectangles** are process nodes (the computation)
- **Arrows** show the data flow

This graph answers questions like *"Where did this number come from?"* and *"What parameters produced this result?"* — even months later.

## Running a second simulation

Let's run with a different feed rate to see how the pattern changes:

```{code-cell} ipython3
params_2 = params.copy()
params_2['F'] = 0.055

result_2 = run_simulation(orm.Dict(params_2))
print(f"F = 0.055: variance(V) = {result_2['variance_V'].value:.4e}")
```

```{code-cell} ipython3
%verdi process list -a
```

Both calculations are recorded in the database, with full provenance.

## Summary

In this module you learned to:

- **Set up a profile** using `verdi presto` (or a temporary profile for testing)
- **Store data** as AiiDA nodes (`Dict`, `Float`)
- **Track computations** using `@calcfunction`
- **Inspect results** with `verdi process list`, `verdi process show`, `verdi node show`
- **Visualize provenance** to understand how data was produced

:::{important}
Here we ran the simulation *inside* the AiiDA Python process using a `calcfunction`.
This is fine for lightweight computations, but real scientific codes (Quantum ESPRESSO, VASP, LAMMPS, …) run as **external executables** on remote computers.
For those, AiiDA provides **CalcJobs** — a mechanism to prepare input files, submit to a scheduler, and retrieve the results.
CalcJobs will be introduced in later modules.
:::

## Next steps

We've run a simulation and stored scalar results with full provenance.
In {ref}`Module 2 <tutorial:module2>`, you'll learn how to write a **parser** to automatically extract structured data from simulation outputs and handle different exit codes.
