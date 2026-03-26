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
# Module 2: Running External Codes

## What you will learn

After this module, you will be able to:

- Run an external code through AiiDA using `aiida-shell`
- Understand the Computer, Code, and CalcJob concepts
- Inspect calculation inputs and outputs with `verdi calcjob inputcat` / `outputcat`
- Write a custom parser to extract structured data from output files
- Handle different exit codes for failure modes

## What you will not learn yet

You cannot yet query the database, organize data into groups, or export archives — those capabilities come in {ref}`Module 3 <tutorial:module3>`.

The cell below loads the shared tutorial profile.
If you are running locally with your own profile (e.g. from `verdi presto`), replace it with `from aiida import load_profile; load_profile()`.

```{code-cell} ipython3
:tags: ["hide-cell"]

# Shared tutorial profile — see Module 1 for details.
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

## The simulation as an external code

In {ref}`Module 1 <tutorial:module1>`, we ran a simulation directly inside Python using a `calcfunction`.
But real scientific codes — Quantum ESPRESSO, VASP, LAMMPS — are **external executables** that read input files and produce output files.

For this module, we have a reaction–diffusion simulation script that mimics this pattern:

- **Input**: a YAML file with simulation parameters
- **Output**: a `.npz` file containing the final fields and scalar diagnostics
- **Exit codes**: `0` (success), `10`/`11` (invalid parameters), `20` (numerical instability), `30` (trivial steady state)

The script is called like a typical command-line tool:

```console
$ python3 reaction-diffusion.py input.yaml --output results.npz
JOB DONE
```

The cell below writes the simulation script to disk.
Click the toggle to inspect it — or just move on.

```{code-cell} ipython3
:tags: ["hide-cell"]

# Write the external simulation code to a temporary directory.
# Treat this as a pre-existing scientific code — you don't need to read it.

import tempfile
from pathlib import Path

tutorial_dir = Path(tempfile.mkdtemp())

SCRIPT = r'''
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml


def fail(code, message):
    print(f"ERROR[{code}]: {message}", file=sys.stderr)
    sys.exit(code)


def laplacian(Z):
    return (
        -4 * Z
        + np.roll(Z, 1, axis=0)
        + np.roll(Z, -1, axis=0)
        + np.roll(Z, 1, axis=1)
        + np.roll(Z, -1, axis=1)
    )


def simulate(params):
    n = params["grid_size"]
    du, dv = params["du"], params["dv"]
    F, k = params["F"], params["k"]
    dt, steps = params["dt"], params["n_steps"]
    seed = params.get("seed", None)

    if du <= 0 or dv <= 0:
        fail(10, "Diffusion constants must be positive")
    if dt <= 0:
        fail(11, "Time step must be positive")
    if seed is not None:
        np.random.seed(seed)

    U = np.ones((n, n))
    V = np.zeros((n, n))
    r = n // 10
    c = n // 2
    U[c - r:c + r, c - r:c + r] = 0.50
    V[c - r:c + r, c - r:c + r] = 0.25

    for step in range(steps):
        Lu, Lv = laplacian(U), laplacian(V)
        uvv = U * V * V
        U += dt * (du * Lu - uvv + F * (1 - U))
        V += dt * (dv * Lv + uvv - (F + k) * V)
        if not np.isfinite(U).all() or not np.isfinite(V).all():
            fail(20, f"Numerical instability detected at step {step}")

    var_v = float(np.var(V))
    mean_v = float(np.mean(V))
    if var_v < 1e-8:
        fail(30, "Trivial steady state (no pattern formed)")

    return U, V, var_v, mean_v


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input YAML file")
    parser.add_argument("--output", required=True, help="Output .npz file")
    parser.add_argument("--dt", type=float, help="Override time step")
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            params = yaml.safe_load(f)
    except Exception as e:
        fail(1, f"Failed to read input file: {e}")

    if args.dt is not None:
        params["dt"] = args.dt

    for key in ["grid_size", "du", "dv", "F", "k", "dt", "n_steps"]:
        if key not in params:
            fail(2, f"Missing required parameter '{key}'")

    try:
        U, V, var_v, mean_v = simulate(params)
    except SystemExit:
        raise
    except Exception as e:
        fail(99, f"Unexpected error: {e}")

    np.savez(
        Path(args.output),
        U_final=U, V_final=V,
        variance_V=var_v, mean_V=mean_v,
        params=json.dumps(params),
    )
    print("JOB DONE")
    sys.exit(0)


if __name__ == "__main__":
    main()
'''

script_path = tutorial_dir / 'reaction-diffusion.py'
script_path.write_text(SCRIPT)
print(f"Script written to {script_path}")
```

## Running with `aiida-shell`

The fastest way to run any external code through AiiDA is with [`aiida-shell`](https://aiida-shell.readthedocs.io).
It wraps any shell command as an AiiDA CalcJob — no plugin code required.

Let's prepare the input file and run the simulation:

```{code-cell} ipython3
import yaml

input_params = {
    'grid_size': 64,
    'du': 0.16, 'dv': 0.08,
    'F': 0.04, 'k': 0.065,
    'dt': 1.0, 'n_steps': 3000,
    'seed': 42,
}

input_path = tutorial_dir / 'input.yaml'
input_path.write_text(yaml.dump(input_params))
```

```{code-cell} ipython3
import sys
from aiida_shell import launch_shell_job

results, node = launch_shell_job(
    sys.executable,
    arguments='{script} {input} --output results.npz',
    nodes={
        'script': script_path,
        'input': input_path,
    },
    outputs=['results.npz'],
)

print(f"Process PK: {node.pk}")
print(f"Exit status: {node.exit_status}")
print(f"Stdout: {results['stdout'].get_content()}")
```

The simulation ran successfully and AiiDA recorded everything.
Let's check what outputs we got:

```{code-cell} ipython3
for label, output_node in sorted(results.items()):
    print(f"  {label}: {output_node.__class__.__name__} (PK={output_node.pk})")
```

The output file is stored as a `SinglefileData` node.
We can load the raw data from it:

```{code-cell} ipython3
import numpy as np

with results['results_npz'].open(mode='rb') as f:
    data = np.load(f)
    print(f"variance(V) = {float(data['variance_V']):.4e}")
    print(f"mean(V)     = {float(data['mean_V']):.4e}")
```

## What just happened?

When you called `launch_shell_job(...)`, AiiDA ran a **CalcJob** behind the scenes.
Here's what happened:

1. **Prepare**: AiiDA copied your input files into a working directory and generated a run script
2. **Run**: The script was executed on a **Computer** (your local machine)
3. **Retrieve**: AiiDA collected the output files from the working directory
4. **Parse**: The outputs were registered as AiiDA nodes with full provenance

AiiDA automatically set up two things behind the scenes:

- A **Computer** (`localhost`) — defines *where* calculations run (hostname, scheduler, transport protocol)
- A **Code** — defines *what* runs (the Python executable on that computer)

When you use `aiida-shell`, these are created automatically.
For production use with remote HPC clusters, you would set them up explicitly with `verdi computer setup` and `verdi code create` — see the {ref}`how-to guide <how-to:run-codes>`.

## Inspecting the calculation

AiiDA records the full lifecycle of every CalcJob. Let's inspect what happened:

```{code-cell} ipython3
%verdi process show {node.pk}
```

We can look at the provenance to see how everything is connected:

```{code-cell} ipython3
---
mystnb:
    image:
        align: center
        width: 500px
    figure:
        caption: "Provenance graph of the ShellJob calculation."
        name: fig_module2_shelljob
---
from aiida import orm
from aiida.tools.visualization import Graph

graph = Graph()
graph.add_incoming(node, annotate_links="both")
graph.add_outgoing(node, annotate_links="both")
graph.graphviz
```

Notice how AiiDA tracked the full data flow — from the input files and parameters, through the calculation, to the output files.

## Parsing outputs

The simulation produced a `.npz` file, but we had to manually load and extract the numbers.
A **parser** automates this: it reads the raw output files and stores the results as structured AiiDA nodes.

With `aiida-shell`, you can pass a custom parser function:

```{code-cell} ipython3
def parse_gray_scott(dirpath):
    """Extract structured data from the simulation output."""
    import numpy as np
    from aiida.orm import Float

    output_file = dirpath / 'results.npz'
    if not output_file.exists():
        return None

    data = np.load(output_file)
    return {
        'variance_V': Float(float(data['variance_V'])),
        'mean_V': Float(float(data['mean_V'])),
    }
```

Now let's run the simulation again, this time with the parser:

```{code-cell} ipython3
results_parsed, node_parsed = launch_shell_job(
    sys.executable,
    arguments='{script} {input} --output results.npz',
    nodes={
        'script': script_path,
        'input': input_path,
    },
    outputs=['results.npz'],
    parser=parse_gray_scott,
)

print(f"variance(V) = {results_parsed['variance_V'].value:.4e}")
print(f"mean(V)     = {results_parsed['mean_V'].value:.4e}")
```

`variance_V` and `mean_V` are now proper AiiDA `Float` nodes — stored in the database with full provenance, just like when we used `@calcfunction` in Module 1.

```{code-cell} ipython3
%verdi process show {node_parsed.pk}
```

## Handling failures

What happens when the simulation fails?
Let's try parameters that produce a trivial steady state (the simulation's exit code 30):

```{code-cell} ipython3
bad_params = input_params.copy()
bad_params['F'] = 0.1  # Too high — no pattern forms

bad_input_path = tutorial_dir / 'input_bad.yaml'
bad_input_path.write_text(yaml.dump(bad_params))

results_bad, node_bad = launch_shell_job(
    sys.executable,
    arguments='{script} {input} --output results.npz',
    nodes={
        'script': script_path,
        'input': bad_input_path,
    },
    outputs=['results.npz'],
    parser=parse_gray_scott,
)

print(f"Success: {node_bad.is_finished_ok}")
print(f"Exit status: {node_bad.exit_status}")
print(f"Exit message: {node_bad.exit_message}")
```

The calculation **failed** — AiiDA detected the non-zero exit code from the simulation.
We can read the error message from stderr:

```{code-cell} ipython3
print(results_bad['stderr'].get_content())
```

```{code-cell} ipython3
%verdi process show {node_bad.pk}
```

AiiDA recorded the failure with full context: the exit status, the inputs that caused it, and the error output.
In {ref}`Module 5 <tutorial:module5>`, you'll learn how to write **error handlers** that automatically respond to these failures — for example, by adjusting parameters and retrying.

## `submit()` vs `run()` and the daemon

So far, every calculation has been **synchronous** — `launch_shell_job(...)` blocks until the calculation finishes.
This is fine for quick local runs, but for production use on HPC clusters you'll want **asynchronous** execution:

- **`run()`** — blocks until the calculation completes. Simple, but ties up your Python session.
- **`submit()`** — sends the calculation to the AiiDA **daemon** and returns immediately. The daemon manages the calculation lifecycle in the background.

To use `submit()`:

```python
from aiida.engine import submit

# Submit to daemon (non-blocking)
node = submit(MyCalcJob, code=code, parameters=params, ...)

# Check status later
print(node.process_state)
```

The daemon is started with `verdi daemon start` and monitors submitted calculations, retrieving results when they finish.

:::{note}
`submit()` requires a running AiiDA daemon, which needs a message broker (RabbitMQ).
The lightweight tutorial profile doesn't include a broker.
For a full installation with daemon support, see the {ref}`installation guide <installation>`.
:::

For **remote HPC execution**, you would set up a Computer with SSH transport and a job scheduler (SLURM, PBS, etc.):

```console
$ verdi computer setup -L my-cluster -H cluster.example.com -T core.ssh -S core.slurm -w /scratch/user/aiida
$ verdi computer configure core.ssh my-cluster
```

Then submit calculations to that computer — AiiDA handles file transfer, job submission, monitoring, and result retrieval automatically.

## Summary

In this module you learned to:

- **Run external codes** with `aiida-shell` — no plugin code needed
- **Understand** the CalcJob cycle: prepare → run → retrieve → parse
- **Inspect** calculations with `verdi process show` and `verdi calcjob outputcat`
- **Parse** raw output files into structured AiiDA nodes
- **Handle failures** through exit codes and error messages
- **Distinguish** `run()` (synchronous) from `submit()` (asynchronous via daemon)

:::{seealso}
- {ref}`How-to: run external codes <how-to:run-codes>` — for writing custom CalcJob plugins
- [`aiida-shell` documentation](https://aiida-shell.readthedocs.io) — full reference for `launch_shell_job`
:::

## Next steps

We can now run external codes and parse their outputs.
In {ref}`Module 3 <tutorial:module3>`, you'll learn how to work with AiiDA's data types, query the database, and organize your results.
