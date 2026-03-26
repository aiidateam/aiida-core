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

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module2.ipynb` {octicon}`download`
:::

## What you will learn

After this module, you will be able to:

- Understand what a CalcJob is and how it differs from a `calcfunction`
- Run an external code through AiiDA using `aiida-shell`
- Understand the Computer and Code concepts
- Inspect calculations with `verdi process show`
- Parse output files into structured AiiDA nodes
- Handle calculation failures

## What you will not learn yet

You cannot yet query the database, organize data into groups, or export archives — those capabilities come in {ref}`Module 3 <tutorial:module3>`.

The cell below loads the shared tutorial profile.
If you are running locally with your own profile (e.g. from `verdi presto`), replace it with:

```python
from aiida import load_profile
load_profile()
```

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

# Pre-register a Code with a short label so that `verdi process list`
# shows "python3@localhost" instead of the full virtualenv path.
import sys

from aiida.common.exceptions import NotExistent
from aiida.orm import InstalledCode, load_code, load_computer

try:
    python_code = load_code('python3@localhost')
except NotExistent:
    python_code = InstalledCode(
        label='python3',
        computer=load_computer('localhost'),
        filepath_executable=sys.executable,
        default_calc_job_plugin='core.shell',
    ).store()
```

## The simulation as an external code

In {ref}`Module 1 <tutorial:module1>`, we ran a simulation directly inside Python using a `calcfunction`.
But real scientific codes — Quantum ESPRESSO, VASP, LAMMPS — are **external executables** that read input files and produce output files.

For this module, we use a reaction–diffusion simulation script that mimics this pattern:

- **Input**: a YAML file with simulation parameters
- **Output**: a `.npz` file containing the final fields and scalar diagnostics
- **Exit codes**: `0` (success), `10`/`11` (invalid parameters), `20` (numerical instability), `30` (trivial steady state)

The script is called like a typical command-line tool:

```console
$ python3 reaction-diffusion.py input.yaml --output results.npz
JOB DONE
```

The script is provided as {download}`include/reaction-diffusion.py` — expand the box below to inspect it, or just move on.

:::{dropdown} Inspect the simulation script
```{literalinclude} include/reaction-diffusion.py
:language: python
```
:::

```{code-cell} ipython3
from pathlib import Path

script_path = Path('include/reaction-diffusion.py').resolve()
```

## Running with `aiida-shell`

In {ref}`Module 1 <tutorial:module1>`, we used a `calcfunction` — a Python function decorated to record provenance.
But external codes can't run inside Python like that.
AiiDA uses a **{ref}`CalcJob <topics:calculations:concepts:calcjobs>`** for this: a process that manages the full lifecycle of running an external executable — preparing input files, executing the code (locally or on a remote cluster), retrieving output files, and optionally parsing the results.

The fastest way to run a CalcJob is with [`aiida-shell`](https://aiida-shell.readthedocs.io), which wraps any shell command — no plugin code required.

Let's prepare the input file and run the simulation:

```{code-cell} ipython3
import tempfile
import yaml

work_dir = Path(tempfile.mkdtemp())

input_params = {
    'grid_size': 64,
    'du': 0.16, 'dv': 0.08,
    'F': 0.04, 'k': 0.065,
    'dt': 1.0, 'n_steps': 3000,
    'seed': 42,
}

input_path = work_dir / 'input.yaml'
input_path.write_text(yaml.dump(input_params));
```

```{code-cell} ipython3
from aiida_shell import launch_shell_job

results, node = launch_shell_job(
    python_code,
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

The output file is stored as a `SinglefileData` node in AiiDA's provenance graph.
We can access it through the calculation node's outputs:

```{code-cell} ipython3
import numpy as np

output_node = node.outputs.results_npz
print(f"Output node: {output_node.__class__.__name__} (PK={output_node.pk})")

with output_node.open(mode='rb') as f:
    data = np.load(f)
    print(f"variance(V) = {float(data['variance_V']):.4e}")
    print(f"mean(V)     = {float(data['mean_V']):.4e}")
```

## What just happened?

When you called `launch_shell_job(...)`, AiiDA ran a CalcJob (specifically, a `ShellJob` — aiida-shell's built-in CalcJob implementation).
Here is the {ref}`lifecycle <topics:calculations:concepts:calcjobs_transport_tasks>` it went through:

1. **Upload**: AiiDA copied your input files into a working directory and generated a run script
2. **Submit**: The script was executed on a **Computer** (your local machine)
3. **Retrieve**: AiiDA collected the output files from the working directory
4. **Parse**: The outputs were registered as AiiDA nodes with full provenance

Every CalcJob needs two things to run:

- A **{ref}`Computer <how-to:run-codes:computer>`** — defines *where* calculations run (hostname, scheduler, transport). When you set up a profile with `verdi presto`, a `localhost` Computer is created automatically.
- A **{ref}`Code <how-to:run-codes:code>`** — defines *what* executable runs on that computer. `aiida-shell` creates this automatically from the command you pass to `launch_shell_job`.

For remote HPC clusters, you would set these up explicitly — see the {ref}`how-to guide <how-to:run-codes>`.
For writing your own CalcJob plugin (with custom input preparation, exit codes, and parsing), see {ref}`how to write a plugin for an external code <how-to:plugin-codes>`.

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
%run -i include/plot_provenance.py
plot_provenance(node)
```

Notice how AiiDA tracked the full data flow — from the input files and parameters, through the calculation, to the output files.

## Parsing outputs

The simulation produced a `.npz` file, but we had to manually load and extract the numbers.
A **parser** automates this: it reads the raw output files and stores the results as structured AiiDA nodes.

With `aiida-shell`, you can pass a custom parser function.
Ours reads the `.npz` output and returns `Float` nodes ({download}`include/parse_gray_scott.py`):

:::{dropdown} Inspect the parser function
```{literalinclude} include/parse_gray_scott.py
:language: python
```
:::

```{code-cell} ipython3
%run -i include/parse_gray_scott.py
```

Now let's run the simulation again, this time with the parser:

```{code-cell} ipython3
results_parsed, node_parsed = launch_shell_job(
    python_code,
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

What happens when a simulation fails?
Let's try parameters that produce no pattern — the simulation detects a trivial steady state and exits with an error:

```{code-cell} ipython3
bad_params = input_params.copy()
bad_params['F'] = 0.1  # Too high — no pattern forms

bad_input_path = work_dir / 'input_bad.yaml'
bad_input_path.write_text(yaml.dump(bad_params));

results_bad, node_bad = launch_shell_job(
    python_code,
    arguments='{script} {input} --output results.npz',
    nodes={
        'script': script_path,
        'input': bad_input_path,
    },
)

print(f"Success: {node_bad.is_finished_ok}")
print(f"Exit status: {node_bad.exit_status}")
print(f"Exit message: {node_bad.exit_message}")
```

The calculation **failed** — `aiida-shell` detected the non-zero exit status from the simulation.
The error details are in stderr:

```{code-cell} ipython3
print(results_bad['stderr'].get_content())
```

```{code-cell} ipython3
%verdi process show {node_bad.pk}
```

AiiDA recorded the failure with full context: the exit status, the inputs that caused it, and the error output.
In a full CalcJob plugin, you would define your own exit codes that map directly to the simulation's failure modes — see the {ref}`how-to guide <how-to:run-codes>`.
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

- **Understand** the CalcJob concept and its lifecycle: upload → submit → retrieve → parse
- **Run external codes** with `aiida-shell` — no plugin code needed
- **Inspect** calculations with `verdi process show`
- **Parse** raw output files into structured AiiDA nodes
- **Handle failures** through exit codes and error messages
- **Distinguish** `run()` (synchronous) from `submit()` (asynchronous via daemon)

:::{seealso}
- {ref}`Topic: calculation jobs <topics:calculations:concepts:calcjobs>` — concepts in depth
- {ref}`How-to: run external codes <how-to:run-codes>` — setting up Computers and Codes
- {ref}`How-to: write a CalcJob plugin <how-to:plugin-codes>` — for custom input preparation, exit codes, and parsing
- [`aiida-shell` documentation](https://aiida-shell.readthedocs.io) — full reference for `launch_shell_job`
:::

## Next steps

We can now run external codes and parse their outputs.
In {ref}`Module 3 <tutorial:module3>`, you'll learn how to work with AiiDA's data types, query the database, and organize your results.
