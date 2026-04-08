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
# Module 1: Running with AiiDA

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module1.ipynb` {octicon}`download`
:::

## What you will learn

After this module, you will be able to:

- Set up an AiiDA profile for storing your data and provenance
- Run an external code through AiiDA using `aiida-shell` and CalcJobs
- Inspect calculations with `verdi` CLI commands
- Explore and visualize the provenance graph
- Dump calculation data to disk with `verdi process dump`

## What you will not learn yet

You cannot yet store structured data types, write calcfunctions, or run parameter sweeps -- those capabilities come in {ref}`Module 2 <tutorial:module2>`.

## Setting up your AiiDA profile

An AiiDA **profile** is where all your data, calculations, and provenance are stored.
Before running any calculations, you need one.

If you are working on your own machine, the easiest way is:

```console
$ verdi presto
```

This creates a lightweight local profile using SQLite storage -- no PostgreSQL or other external services required.
You can verify that your profile is set up correctly with:

```console
$ verdi status
```

For production use or more advanced setups, see the {ref}`installation guide <installation>`.

:::{tip}
Use `verdi profile list` to see all your profiles and `verdi profile show` to inspect the active one.
:::

The cell below creates a tutorial profile for automated execution of this tutorial ({download}`include/setup_tutorial.py`).
It loads the AiiDA profile and makes a `python_code` variable available -- an AiiDA `Code` object pointing to the Python interpreter on `localhost`, which we use with `aiida-shell` throughout.
If you are running locally with your own profile, you can skip it.

```{code-cell} ipython3
:tags: ["hide-cell"]

# Auto-generated tutorial profile for docs build.
# If running locally with your own profile (e.g. from ``verdi presto``),
# replace this cell with:
#
#     from aiida import load_profile
#     load_profile()

%load_ext aiida
%run -i include/setup_tutorial.py
```

:::{admonition} About the code cells in this tutorial
:class: note

This tutorial uses [IPython magic commands](https://ipython.readthedocs.io/en/stable/interactive/magics.html) that you will see throughout:

- **`%run -i script.py`** -- executes a Python file in the current namespace (like pasting its contents into the cell). If you are working locally, you can instead `import` from the file or copy the code directly.
- **`%verdi ...`** -- runs a `verdi` CLI command from within the notebook. In a terminal, you would run the same command without the `%` prefix, e.g. `verdi process list -a`.
- **`%load_ext aiida`** -- loads the AiiDA IPython extension, which enables the `%verdi` magic.
- **`from include.constants import ...`** -- shared constants (`BASE_PARAMS`, `F_VALUES`, `SCRIPT_PATH`) are defined in {download}`include/constants.py` to keep code cells focused on AiiDA concepts rather than parameter definitions.
:::

## Running the simulation with `aiida-shell`

In {ref}`Module 0 <tutorial:module0>`, we ran the simulation directly with `subprocess`.
Now let's run it through AiiDA, which will automatically track everything.

AiiDA uses a **{ref}`CalcJob <topics:calculations:concepts:calcjobs>`** to manage external executables -- preparing input files, executing the code (locally or on a remote cluster), retrieving output files, and optionally parsing the results.

The fastest way to run a CalcJob is with [`aiida-shell`](https://aiida-shell.readthedocs.io), which wraps any shell command -- no plugin code required.

Let's prepare the input file and run the simulation:

```{code-cell} ipython3
# Write the simulation input parameters to a YAML file on disk.
import tempfile
from pathlib import Path

import yaml

from include.constants import BASE_PARAMS, SCRIPT_PATH

work_dir = Path(tempfile.mkdtemp())
input_path = work_dir / 'input.yaml'
input_path.write_text(yaml.dump(BASE_PARAMS));
```

```{code-cell} ipython3
# Run the simulation through AiiDA using aiida-shell's launch_shell_job.
from aiida_shell import launch_shell_job

results, node = launch_shell_job(
    python_code,
    arguments='{script} {input} --output results.npz',
    nodes={'script': SCRIPT_PATH, 'input': input_path},
    outputs=['results.npz'],
)

print(f"Process PK: {node.pk}")
print(f"Exit status: {node.exit_status}")
print(f"Stdout: {results['stdout'].get_content()}")
```

The simulation ran successfully and AiiDA recorded everything.
Let's check what outputs we got:

```{code-cell} ipython3
# List all output nodes returned by the CalcJob.
for label, output_node in sorted(results.items()):
    print(f"  {label}: {output_node.__class__.__name__} (PK={output_node.pk})")
```

The output file is stored as a `SinglefileData` node in AiiDA's provenance graph.
We can access it through the calculation node's outputs:

```{code-cell} ipython3
# Open the .npz output node and extract scalar results.
import numpy as np

output_node = node.outputs.results_npz
print(f"Output node: {output_node.__class__.__name__} (PK={output_node.pk})")

with output_node.open(mode='rb') as f:
    data = np.load(f)
    print(f"variance(V) = {float(data['variance_V']):.4e}")
    print(f"mean(V)     = {float(data['mean_V']):.4e}")
```

## What just happened?

When you called `launch_shell_job(...)`, AiiDA ran a CalcJob (specifically, a `ShellJob` -- aiida-shell's built-in CalcJob implementation).
Here is the {ref}`lifecycle <topics:calculations:concepts:calcjobs_transport_tasks>` it went through:

1. **Upload**: AiiDA copied your input files into a working directory and generated a run script
2. **Submit**: The script was executed on a **Computer** (your local machine)
3. **Retrieve**: AiiDA collected the output files from the working directory
4. **Parse**: The outputs were registered as AiiDA nodes with full provenance

Every CalcJob needs two things to run:

- A **{ref}`Computer <how-to:run-codes:computer>`** -- defines *where* calculations run (hostname, scheduler, transport). When you set up a profile with `verdi presto`, a `localhost` Computer is created automatically.
- A **{ref}`Code <how-to:run-codes:code>`** -- defines *what* executable runs on that computer. `aiida-shell` creates this automatically from the command you pass to `launch_shell_job`.

For remote HPC clusters, you would set these up explicitly -- see the {ref}`how-to guide <how-to:run-codes>`.
For writing your own CalcJob plugin (with custom input preparation, exit codes, and parsing), see {ref}`how to write a plugin for an external code <how-to:plugin-codes>`.

:::{note}
When you use `launch_shell_job()`, aiida-shell creates a temporary Code behind the scenes.
For production work on remote HPC clusters, you would register a Computer and Code explicitly with `verdi computer setup` and `verdi code create`.
:::

## Inspecting the calculation

AiiDA records the full lifecycle of every CalcJob. Let's inspect what happened:

```{code-cell} ipython3
# Show detailed information about the calculation node.
%verdi process show {node.pk}
```

We can see all processes that have been run so far:

```{code-cell} ipython3
# List all processes that have been run in this profile.
%verdi process list -a
```

## Exploring the provenance graph

AiiDA automatically builds a **provenance graph** that records exactly how each piece of data was produced:

```{code-cell} ipython3
---
mystnb:
    image:
        align: center
        width: 500px
    figure:
        caption: "Provenance graph of the ShellJob calculation."
        name: fig_module1_shelljob
---
# Generate and display the provenance graph for this calculation.
%run -i include/plot_provenance.py
plot_provenance(node)
```

In the graph:
- **Green ellipses** are data nodes (inputs and outputs)
- **Rectangles** are process nodes (the computation)
- **Arrows** show the data flow

This graph answers questions like *"Where did this number come from?"* and *"What parameters produced this result?"* -- even months later.

:::{tip}
You can also generate provenance graphs from the command line with `verdi node graph generate <PK>`.
:::

## Dumping calculation data

You can export the full calculation -- inputs, outputs, logs -- to a directory on disk:

```{code-cell} ipython3
# Export the full calculation (inputs, outputs, logs) to a directory.
%verdi process dump {node.pk} --path /tmp/tutorial_dump -o
```

```{code-cell} ipython3
# Print the directory tree of the dumped calculation data.
import os

dump_path = Path('/tmp/tutorial_dump')
for root, dirs, files in os.walk(dump_path):
    level = root.replace(str(dump_path), '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{Path(root).name}/")
    sub_indent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{sub_indent}{file}")
```

This is useful for debugging, archival, or sharing calculation data outside of AiiDA.

## Summary

In this module you learned to:

- **Set up a profile** using `verdi presto` (or a temporary profile for testing)
- **Run external codes** with `aiida-shell` -- no plugin code needed
- **Inspect results** with `verdi process list`, `verdi process show`
- **Visualize provenance** to understand how data was produced
- **Dump calculation data** to disk with `verdi process dump`

:::{seealso}
- {ref}`Topic: calculation jobs <topics:calculations:concepts:calcjobs>` -- concepts in depth
- {ref}`How-to: run external codes <how-to:run-codes>` -- setting up Computers and Codes
- {ref}`How-to: write a CalcJob plugin <how-to:plugin-codes>` -- for custom input preparation, exit codes, and parsing
- [`aiida-shell` documentation](https://aiida-shell.readthedocs.io) -- full reference for `launch_shell_job`
:::

## Next steps

We can now run simulations through AiiDA with full provenance tracking.
But the outputs are opaque files -- we can't search or query individual values.
In {ref}`Module 2 <tutorial:module2>`, you'll learn how to work with AiiDA's data types, write calcfunctions, and run parameter sweeps with structured, queryable results.
