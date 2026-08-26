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
# Module 1: Calculations with AiiDA

{bdg-secondary}`⏱️ ~60 min read` {bdg-success}`Beginner`

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module1.ipynb` {octicon}`download`
:::

## What you will learn

After this module, you will be able to:

- Set up an AiiDA profile for storing your data and provenance
- Run an external code as a tracked AiiDA process
- Inspect calculations with AiiDA's `verdi` CLI
- Explore and visualize the provenance graph
- Dump calculation data to disk with `verdi process dump`

:::{note}
This module needs AiiDA and `aiida-shell`:

```bash
uv pip install "aiida-core>=2.9" "aiida-shell>=0.9.0" matplotlib git+https://github.com/aiidateam/gsrd.git

# or, without uv:

pip install "aiida-core>=2.9" "aiida-shell>=0.9.0" matplotlib git+https://github.com/aiidateam/gsrd.git
```

It also uses the small `gsrd` simulator introduced in {ref}`Module 0 <tutorial:module0>`.
:::

:::{dropdown} System dependency: Graphviz
The provenance-graph plots need the Graphviz `dot` binary, a system package (not a Python one). Install it through your operating system's package manager if the graph cells report it as missing.
:::

(tutorial:module1:setup)=
## Setting up your AiiDA profile

An AiiDA **profile** defines the configuration for an AiiDA instance:

- The **database** that stores the provenance graph
- The **file repository** that stores file contents and other binary data
- The **process broker** that coordinates running calculations

Before running any calculations, you need one.

AiiDA comes with a command-line interface, `verdi`, which you will use throughout the tutorial to inspect and manage your data.
We recommend running this tutorial in its own **isolated sandbox profile**, kept separate from any profile you may already have, so the data you create here never mixes with your real work and every module reproduces exactly.

For the documentation build, we use the setup cell below, which is also included in the downloaded notebooks.

:::{dropdown} What the setup cell does
The cell below runs tutorial-specific machinery that creates the profile in an isolated `.aiida-tutorial/` sandbox (so it never touches your real `~/.aiida`), registers the `gsrd` code, starts the daemon, and loads the `%verdi` magic (contained in `include/tutorial_plumbing.py`). You do not need to run it yourself, or even read it; the handful of commands it comes down to, the ones you would actually run yourself, are shown right after.

If you are running outside the tutorial repository (for example, cells pasted into your own notebook), it first downloads that script; inside the repo, or once Module 0's fetch cell has run, that step is skipped.

Module 1 creates the profile; the later modules reconnect to it, so the data you create now stays available throughout.
:::

```{code-cell} ipython3
:tags: [hide-cell]
:mystnb:
:    code_prompt_show: 'Show the setup cell (tutorial plumbing you can ignore)'
:    code_prompt_hide: 'Hide the setup cell'

# Fetch tutorial_plumbing.py if missing, then run it to set up the profile.
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

For your own work, outside the tutorial's sandbox, setting up your AiiDA profile for the tutorial is just three commands:

```console
$ verdi presto --profile-name tutorial --use-zeromq
$ verdi daemon start
$ verdi code create core.code.installed --config include/gsrd_code.yaml -X $(which gsrd)
```

`verdi presto` creates a profile with sensible defaults for all three components above: **SQLite** for the database, [disk-objectstore](https://github.com/aiidateam/disk-objectstore) for file storage, and the built-in **ZeroMQ broker** (`--use-zeromq` keeps it dependency-free; without it, `verdi presto` uses RabbitMQ whenever it detects it running).

`verdi daemon start` then brings up the daemon that runs your calculations. For more advanced, high-throughput production setups, see the {ref}`installation guide <installation>`.

:::{note}
AiiDA keeps all of its configuration, your profiles, their databases, and the daemon's state, in its **configuration directory**, which defaults to `~/.aiida`.
Where AiiDA looks for (and creates) that directory is controlled by the `AIIDA_PATH` environment variable.
To keep the tutorial self-contained, the hidden setup cell above points `AIIDA_PATH` at a local `.aiida-tutorial/` directory in your working directory, so this profile, its database, and its daemon live there instead of in your usual `~/.aiida`.
Nothing here touches any AiiDA profile you already have, and deleting `.aiida-tutorial/` removes every trace of the tutorial.
:::

You can verify that the profile is set up correctly with `verdi status`:

```{code-cell} ipython3
# Check that the AiiDA profile is configured and all services are reachable.
%verdi status
```

:::{note}
We use IPython magic commands like `%verdi <cmd>` in Code cells (`%verdi` runs a `verdi` CLI command from the notebook).
To execute in a terminal, drop the `%` prefix.
:::

With the profile up and verified, the last step is registering the code you will run. `verdi code create` registers the `gsrd` CLI as an AiiDA `Code` object from a small config file, `include/gsrd_code.yaml`, setting just its `label`, `computer`, and default calculation plugin (`-X` gives the executable path, which depends on where `gsrd` is installed; everything else stays at its defaults):

```{literalinclude} include/gsrd_code.yaml
:language: yaml
```

:::{dropdown} Inspecting the&nbsp;`gsrd@localhost`&nbsp;Code
The setup cell registered this Code for you, but there is nothing magic about it: a Code is a normal, portable AiiDA object. You can export its configuration to YAML with `verdi code export <label>`. Where the `gsrd_code.yaml` above set only the few fields that differ from the defaults, the export lists them all:

```console
$ verdi code export gsrd@localhost
```

```yaml
append_text: ''
computer: localhost
default_calc_job_plugin: core.shell
description: ''
filepath_executable: /path/to/your/environment/bin/gsrd
label: gsrd
prepend_text: ''
use_double_quotes: false
wrap_cmdline_params: false
```

The `filepath_executable` points wherever `gsrd` is installed in your environment; everything else is the default `InstalledCode` configuration. You can recreate the same Code from such a file with:

```console
$ verdi code create core.code.installed --config gsrd.yml
```
:::

## Running the simulation with `aiida-shell`

In {ref}`Module 0 <tutorial:module0>`, we ran `gsrd` directly from the command line.
Now let's run it through AiiDA, so the inputs, outputs, and execution metadata get captured in the provenance graph.

AiiDA uses the **{ref}`CalcJob <topics:calculations:concepts:calcjobs>`** class to manage external executables by preparing input files, executing the code (locally or on a remote cluster), retrieving output files, and parsing the results.

The fastest way to run a CalcJob is with [`aiida-shell`](https://aiida-shell.readthedocs.io), which wraps any shell command without requiring additional plugin code.
Below, we use its `launch_shell_job` helper with the same input file as in {ref}`Module 0 <tutorial:module0>` and a pre-registered `gsrd_code` object: an `InstalledCode` pointing at the `gsrd` CLI binary, set up by the setup cell above and registered under the AiiDA label `gsrd@localhost` (which is what you will see in `verdi` output later on; the Python variable `gsrd_code` is just a local handle for the same Code object).

```{code-cell} ipython3
# Run the simulation through AiiDA using aiida-shell's launch_shell_job.
from aiida_shell import launch_shell_job

# aiida-shell accepts a path to the input file, relative to this notebook.
input_path = 'include/input.yaml'

results, node = launch_shell_job(
    gsrd_code,
    arguments='{input}',
    nodes={'input': input_path},
    outputs=['results.npz'],
)

print(f"Process PK: {node.pk}")
print(f"Exit status: {node.exit_status}")
```

### What just happened?

When you called `launch_shell_job(...)`, AiiDA ran a `ShellJob` (`aiida-shell`'s built-in `CalcJob` implementation).
The call returns two things, which we unpacked as `results, node`: `results` is a dict of the output data nodes, and `node` is the `CalcJobNode` that records the run itself, its inputs, outputs, and status in the provenance graph.
Here is the {ref}`lifecycle <topics:calculations:concepts:calcjobs_transport_tasks>` it went through:

1. **Upload**: AiiDA copied your input files into a working directory and generated a run script
2. **Submit**: The script was executed on a **Computer** (your local machine, in this case)
3. **Retrieve**: AiiDA collected the output files from the working directory
4. **Parse**: The outputs were registered as AiiDA nodes with full provenance

Every CalcJob needs two things to run:

- A **{ref}`Computer <how-to:run-codes:computer>`** defines *where* calculations run, specifying the hostname, transport, and scheduler.
  When you set up a profile with `verdi presto`, a `localhost` Computer is created automatically.
- A **{ref}`Code <how-to:run-codes:code>`** wraps an executable bound to a specific Computer. `aiida-shell` creates one automatically from the command you pass to `launch_shell_job`.

In day-to-day use you only ever pass the `Code` to a process; the `Computer` is resolved implicitly through the `Code`, which already references it.

:::{note}
Every node stored by AiiDA gets two identifiers: a **PK** (primary key, an integer that is unique within this profile) and a **UUID** (universally unique, useful when sharing data). PKs are short and convenient, so we will use them throughout the tutorial. You can always load a node back by PK or UUID:

```python
from aiida.orm import load_node
my_node = load_node(<PK or UUID>)
```
:::

## Exploring the provenance graph

AiiDA automatically builds a **provenance graph** that records exactly how each piece of data was produced:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
# Generate and display the provenance graph for this calculation.
from include.plotting import plot_provenance

plot_provenance(node)
```

In the graph:
- **Green ellipses** are data nodes (inputs and outputs)
- **Rectangles** are process nodes (the computation)
- **Arrows** show the data flow, annotated with a **link type** (`INPUT_CALC` from data to a calculation, `CREATE` from a calculation to its output data) and a **link label** (e.g. `input`, `results_npz`, `stdout`). These are the same names you use to access the nodes in Python via `node.inputs.<label>` / `node.outputs.<label>`.

This graph answers questions like *"Where did this number come from?"* and *"What parameters produced this result?"*, even months later.

:::{tip}
Open the image in a new tab for a larger view.
You can also generate provenance graphs from the command line with `verdi node graph generate <PK or UUID>`.
:::

:::{dropdown} About the&nbsp;`plot_provenance`&nbsp;helper
`plot_provenance` is a thin wrapper we ship in {download}`include/plotting.py`, where all of the tutorial's `plot_*` helpers live. Plotting is not the focus here, so we keep that boilerplate out of the way; open the file if you are curious.
:::

## Inspecting the calculation

AiiDA records the full lifecycle of every CalcJob (the process moves through the states `Created` → `Running` → `Waiting` → `Finished`/`Excepted`/`Killed`).
Two ways to look at it: from the command line, and from Python.

### From the command line

For a quick status check of our calculation:

```{code-cell} ipython3
# Quick status check for the calculation.
%verdi process status {node.pk}
```

For a broader overview of all processes that have been run so far:

```{code-cell} ipython3
# List all processes that have been run in this profile.
%verdi process list -a
```

And, for full details on a specific calculation (inputs, outputs, exit code, attributes):

```{code-cell} ipython3
# Show detailed information about the calculation node.
%verdi process show {node.pk}
```

### From Python

`verdi process show` above already lists the output nodes by label.
We can, of course, also access them programmatically through the Python API.
The `results` dict that `launch_shell_job` returned holds the parsed data outputs, while `node.outputs` exposes those *plus* the engine-level outputs AiiDA adds automatically. Access either by name, whichever feels natural:

```{code-cell} ipython3
# The `results` dict holds the parsed data outputs of the CalcJob.
for label, output_node in sorted(results.items()):
    print(f"{label + ':':<13} {type(output_node).__name__} (PK={output_node.pk})")

# node.outputs also carries the engine outputs that aren't in `results`,
# such as the remote working folder.
print(f"\nRemote folder: {node.outputs.remote_folder.get_remote_path()}")
```

:::{note}
The output label `results_npz` corresponds to the file we declared as `results.npz` in the `outputs=` argument to `launch_shell_job`.
AiiDA replaces dots and other special characters with underscores because the resulting link labels must be valid Python identifiers.
:::

Each output plays a different role:

- `results_npz`: the main output file we declared via `outputs=`.
- `stdout` / `stderr`: the captured standard streams of the `gsrd` invocation.
- `retrieved`: a `FolderData` containing everything AiiDA fetched back from the working directory.
- `remote_folder`: a `RemoteData` pointing to the working directory on the Computer where the job ran (typically a remote HPC); the path we just printed above.

:::{tip}
From the command line, `verdi calcjob gotocomputer <PK>` SSHes into the Computer and drops you directly into that working directory.
:::

Now to the actual numbers.
Recall from {ref}`Module 0 <tutorial:module0>` that `gsrd` splits its output across two places: the arrays go into `results.npz`, but the scalar diagnostics (`variance(V)`, `mean(V)`) appear *only* on stdout.
Both are now tracked by AiiDA as {py:class}`~aiida.orm.SinglefileData` nodes (`aiida-shell` captures stdout as a file just like any other output), so we can open either of them the same way.

The full raw stdout text we already saw printed inline in {ref}`Module 0 <tutorial:module0>` is still retrievable via `node.outputs.stdout.get_content()`.
We collapse the cell output here, since it is the same wall of text as before:

```{code-cell} ipython3
:tags: ["hide-output"]

# Same banner+progress+diagnostics block as in Module 0, now retrieved from
# the provenance graph rather than scraped from a terminal log.
print(node.outputs.stdout.get_content())
```

In later modules we extract just the diagnostics block from this text, so the banner and progress lines are folded out of the displayed output. They are always present in the captured stdout node, just collapsed for readability.

Turning a code's raw output into structured values like this is a **parsing** step: the kind of code you write once and reuse across runs. Here we do it by hand:

```{code-cell} ipython3
:tags: [hide-input]
:mystnb:
:    code_prompt_show: 'Show the parsing code'
:    code_prompt_hide: 'Hide the parsing code'

# Pull the final V field out of the .npz, and read the scalars from stdout.
import io
import re

import numpy as np

# gsrd prints its two summary numbers only to stdout, so we read them with a
# small regex. (Module 2 turns this hand-parsing into a tracked calcfunction.)
VARIANCE_RE = re.compile(r'Variance of V field\s*:\s*([\d.eE+-]+)')
MEAN_RE = re.compile(r'Mean\s+of V field\s*=\s*([\d.eE+-]+)')

with node.outputs.results_npz.open(mode='rb') as fh:
    arrays = np.load(io.BytesIO(fh.read()))
    v_field = arrays['V_final']

print(f"{'V field shape':<13} = {v_field.shape}")

stdout_text = node.outputs.stdout.get_content()
var_v = float(VARIANCE_RE.search(stdout_text).group(1))
mean_v = float(MEAN_RE.search(stdout_text).group(1))
print(f"{'variance(V)':<13} = {var_v:.4e}")
print(f"{'mean(V)':<13} = {mean_v:.4e}")
```

In the folded parsing code above, we use regex to extract the relevant values. This is the price of admission for a code that reports its summary scalars as free-form text rather than a structured format we could load directly. In {ref}`Module 0 <tutorial:module0>` we read these same two numbers off the log by eye; here we pull them out programmatically. The difference now is that the stdout text and the input file that produced it are tracked nodes in the provenance graph, so we can re-run this extraction against any past run, at any point, without re-running the simulation.

The `stdout` node the two floats came from *is* a tracked `SinglefileData` in the provenance graph, but the two numbers we just pulled out of it are *not*: they are transient Python locals. To capture them as proper queryable nodes, {ref}`Module 2 <tutorial:module2>` turns this hand-written extraction into a {func}`@calcfunction <aiida.engine.processes.functions.calcfunction>` that becomes a first-class step in the pipeline.

:::{dropdown} Interactive exploration with&nbsp;`verdi shell`
:icon: info

For quick, one-off inspection outside a notebook, `verdi shell` drops you into an IPython session with your active profile already loaded, plus a handful of convenience symbols imported:

```bash
verdi shell
```

```pycon
>>> node = load_node(<PK>)            # load any node by PK or UUID
>>> node.outputs.stdout.get_content() # read the content of an output node
>>> node.inputs                       # inspect inputs
>>> load_code('gsrd@localhost')       # load a Code by its label
```

Common helpers like `load_node`, `load_code`, `Dict`, etc. are pre-imported, so you do not need `from aiida import ...` boilerplate.
It is the same Python environment as `%load_ext aiida` gives you inside Jupyter; pick whichever feels right.
:::

## Dumping calculation data

AiiDA stores everything in its internal database and file repository (efficient for machines, opaque for humans).
`verdi process dump` writes the same data out as a human-readable directory tree of inputs, outputs, and logs:

```{code-cell} ipython3
:tags: ["hide-output"]

# Export the full calculation (inputs, outputs, logs) to `/tmp/aiida-tutorial/dump/`.
%verdi process dump {node.pk} --path /tmp/aiida-tutorial/dump -o
```

```{code-cell} ipython3
:tags: [hide-input]
:mystnb:
:    code_prompt_show: 'Show the tree-printing code'
:    code_prompt_hide: 'Hide the tree-printing code'

# Show the directory tree of the dumped data (pure Python, no `tree` binary needed).
from pathlib import Path

dump_dir = Path('/tmp/aiida-tutorial/dump')
for path in sorted(dump_dir.rglob('*')):
    indent = '    ' * (len(path.relative_to(dump_dir).parts) - 1)
    print(f'{indent}{path.name}{"/" if path.is_dir() else ""}')
```

All the relevant entities of the calculation are there: the input file, the simulation script, the submission script, captured stdout and stderr, and AiiDA metadata.
This is useful for debugging or sharing calculation data outside of AiiDA.

## Next steps

You can now run external codes through AiiDA with full provenance tracking.
In {ref}`Module 2 <tutorial:module2>`, both preparing the inputs and parsing the outputs (the regex we just wrote by hand) become tracked steps, so each run's input parameters and results turn into queryable database entries, searchable across runs without opening any file.

## Further reading

- AiiDA's database layer: {ref}`topics:database`
- File storage: {ref}`topics:repository`
- The message broker: {ref}`internal_architecture:broker`
- Writing a CalcJob plugin for an external code: {ref}`how-to:plugin-codes`
- Process state machine: {ref}`topics:processes:concepts:state`
- Exit code semantics: {ref}`topics:processes:concepts:exit_codes`
- Built-in data nodes: {ref}`topics:data_types:core:singlefile`, {ref}`topics:data_types:core:folder`, {ref}`topics:data_types:core:remote`
- `verdi process dump`: {ref}`how-to:data:dump`
