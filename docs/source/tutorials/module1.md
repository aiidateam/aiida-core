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

<!-- TODO: re-enable once the md->ipynb conversion script is verified
:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module1.ipynb` {octicon}`download`
:::
-->

## What you will learn

After this module, you will be able to:

- Set up an AiiDA profile for storing your data and provenance
- Run an external code as a tracked AiiDA process
- Inspect calculations with AiiDA's `verdi` CLI
- Explore and visualize the provenance graph
- Dump calculation data to disk with `verdi process dump`

## Setting up your AiiDA profile

An AiiDA **profile** defines the configuration for an AiiDA instance:

- The **database** that stores the provenance graph
- The **file repository** that stores file contents and other binary data
- The **process broker** that coordinates running calculations

Before running any calculations, you need one.

If you are working on your own machine, the easiest way is:

```console
$ verdi presto
```

This creates a lightweight local profile with sensible defaults for all three: SQLite for the database, [disk-objectstore](https://github.com/aiidateam/disk-objectstore) for file storage, and the built-in **ZMQ message broker**.
For more advanced high-throughput production setups, see the {ref}`installation guide <installation>`.

```{code-cell} ipython3
:tags: ["remove-cell"]

# Auto-generated tutorial profile for docs build.
# If running locally with your own profile (e.g. from ``verdi presto``),
# replace this cell with:
#
#     from aiida import load_profile
#     load_profile()

%load_ext aiida

# Stop any leftover daemon and delete any past tutorial profiles created by
# this script, so each docs build starts fresh. Modules 2+ reuse the profile
# created here. Legacy bare `tutorial` profiles (without a hash suffix) are
# left alone, since they predate the current setup and should be cleaned up
# manually with `verdi profile delete tutorial`.
from contextlib import suppress

from aiida.engine.daemon.client import DaemonNotRunningException, get_daemon_client
from aiida.manage.configuration import get_config
_config = get_config()
for _stale_name in [n for n in _config.profile_names if n.startswith('tutorial-')]:
    _daemon_client = get_daemon_client(_stale_name)
    if _daemon_client.is_daemon_running:
        # Tolerate the case where the daemon's PID file is stale: `is_daemon_running`
        # checks pidfile presence, but the underlying circus process may already be
        # gone, in which case `stop_daemon` cleans the pidfile and then raises.
        with suppress(DaemonNotRunningException):
            _daemon_client.stop_daemon(wait=True)
    _config.delete_profile(_stale_name, delete_storage=True)

%run -i include/setup_tutorial.py
```

You can verify that the profile is set up correctly with `verdi status`:

```{code-cell} ipython3
# Check that the AiiDA profile is configured and all services are reachable.
%verdi status
```

:::{note}
We use IPython magic commands like `%verdi <cmd>` in Code cells (`%verdi` runs a `verdi` CLI command from the notebook).
To execute in a terminal, drop the `%` prefix.
:::

## Running the simulation with `aiida-shell`

In {ref}`Module 0 <tutorial:module0>`, we ran `gsrd` directly from the command line.
Now let's run it through AiiDA, so the inputs, outputs, and execution metadata get captured in the provenance graph.

AiiDA uses the **{ref}`CalcJob <topics:calculations:concepts:calcjobs>`** class to manage external executables by preparing input files, executing the code (locally or on a remote cluster), retrieving output files, and optionally parsing the results.

The fastest way to run a CalcJob is with [`aiida-shell`](https://aiida-shell.readthedocs.io), which wraps any shell command without requiring additional plugin code.
Below, we use its `launch_shell_job` helper with the same input file as in {ref}`Module 0 <tutorial:module0>` and a pre-registered `gsrd_code` object: an `InstalledCode` pointing at the `gsrd` CLI binary, set up by a hidden cell above (see {download}`include/setup_tutorial.py`) and registered under the AiiDA label `gsrd@localhost` (which is what you will see in `verdi` output later on; the Python variable `gsrd_code` is just a local handle for the same Code object).

```{code-cell} ipython3
# Run the simulation through AiiDA using aiida-shell's launch_shell_job.
from pathlib import Path

from aiida_shell import launch_shell_job

input_path = Path('include/input.yaml').resolve()

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
Here is the {ref}`lifecycle <topics:calculations:concepts:calcjobs_transport_tasks>` it went through:

1. **Upload**: AiiDA copied your input files into a working directory and generated a run script
2. **Submit**: The script was executed on a **Computer** (your local machine)
3. **Retrieve**: AiiDA collected the output files from the working directory
4. **Parse**: The outputs were registered as AiiDA nodes with full provenance

Every CalcJob needs two things to run:

- A **{ref}`Computer <how-to:run-codes:computer>`** defines *where* calculations run, specifying the hostname, transport, and scheduler.
  When you set up a profile with `verdi presto`, a `localhost` Computer is created automatically.
- A **{ref}`Code <how-to:run-codes:code>`** wraps an executable bound to a specific Computer. `aiida-shell` creates one automatically from the command you pass to `launch_shell_job`.

In day-to-day use you only ever pass the `Code` to a process; the `Computer` is resolved implicitly through the `Code`, which already references it.

:::{note}
Every node stored by AiiDA gets two identifiers: a **PK** (primary key, an integer that is unique within this profile) and a **UUID** (universally unique, useful when sharing data). PKs are short and convenient, so we will use them throughout the tutorial. You can always load a node back with `load_node(<PK or UUID>)`.
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
- **Arrows** show the data flow, annotated with a **link type** (`INPUT_CALC` from data to a calculation, `CREATE` from a calculation to its output data; `INPUT_WORK`, `RETURN`, `CALL_CALC` appear once we move to workflows in {ref}`Module 3 <tutorial:module3>`) and a **link label** (e.g. `input`, `results_npz`, `stdout`). These are the same names you use to access the nodes in Python via `node.inputs.<label>` / `node.outputs.<label>`.

This graph answers questions like *"Where did this number come from?"* and *"What parameters produced this result?"*, even months later.

:::{tip}
Open the image in a new tab for a larger view.
You can also generate provenance graphs from the command line with `verdi node graph generate <PK or UUID>`.
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
The `results` dict that `launch_shell_job` returned and the `node.outputs` namespace expose the same set of outputs, so you can pick whichever feels natural:

```{code-cell} ipython3
# List all output nodes returned by the CalcJob (via the `results` dict).
for label, output_node in sorted(results.items()):
    print(f"{label + ':':<13} {type(output_node).__name__} (PK={output_node.pk})")

# Same set of outputs, accessed by name through the node.
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

In later modules we extract just the diagnostics block from this text, so the banner and progress lines are hidden from the displayed output. They are always present in the captured stdout node, just collapsed for readability.

Here is how we extract the actual values:

```{code-cell} ipython3
:tags: ["hide-input"]

# Pull the final V field out of the .npz, and grep the scalars out of stdout.
import io

import numpy as np

from include.constants import MEAN_RE, VARIANCE_RE

with node.outputs.results_npz.open(mode='rb') as fh:
    arrays = np.load(io.BytesIO(fh.read()))
    v_field = arrays['V_final']

print(f"V field shape: {v_field.shape}")

stdout_text = node.outputs.stdout.get_content()
var_v = float(VARIANCE_RE.search(stdout_text).group(1))
mean_v = float(MEAN_RE.search(stdout_text).group(1))
print(f"variance(V) = {var_v:.4e}")
print(f"mean(V)     = {mean_v:.4e}")
```

The regex above is the price of admission for a code that prints its summary scalars only to stdout.
We did exactly the same thing manually in {ref}`Module 0 <tutorial:module0>`. The difference is that the stdout text and the input file that produced it are now tracked nodes in the provenance graph, so we can re-run this extraction against any past run, at any point, without re-running the simulation. The two floats we computed here, however, are *not* part of the graph. They are just transient Python locals. To capture them as proper queryable nodes we would need a parser; {ref}`Module 2 <tutorial:module2>` turns this hand-written extraction into exactly that, a {func}`@calcfunction <aiida.engine.processes.functions.calcfunction>` that becomes a first-class step in the pipeline.

:::{dropdown} Interactive exploration with&nbsp;`verdi shell`
:icon: info

Notebooks are great for tutorials, but day-to-day debugging often happens in a shell.
`verdi shell` drops you into an IPython session with your active profile already loaded, plus a handful of convenience symbols imported:

```bash
verdi shell
```

```pycon
>>> node = load_node(<PK>)            # load any node by PK or UUID
>>> node.outputs.stdout.get_content() # read the content of an output node
>>> node.inputs                       # inspect inputs
>>> QueryBuilder().append(...).all()  # query the provenance graph
```

Common helpers like `load_node`, `Dict`, `QueryBuilder`, etc. are pre-imported, so you do not need `from aiida import ...` boilerplate.
It is the same Python environment as `%load_ext aiida` gives you inside Jupyter; pick whichever feels right.
:::

## Dumping calculation data

AiiDA stores everything in its internal database and file repository (efficient for machines, opaque for humans).
`verdi process dump` writes the same data out as a human-readable directory tree of inputs, outputs, and logs:

```{code-cell} ipython3
:tags: ["hide-output"]

# Export the full calculation (inputs, outputs, logs) to a directory.
import tempfile

dump_path = tempfile.mkdtemp(prefix='aiida_tutorial_dump_')
%verdi process dump {node.pk} --path {dump_path} -o
```

```{code-cell} ipython3
# Show the directory tree of the dumped calculation data.
!tree {dump_path}
```

All the relevant entities of the calculation are there: the input file, the simulation script, the submission script, captured stdout and stderr, and AiiDA metadata.
This is useful for debugging or sharing calculation data outside of AiiDA.

<!-- TODO: Add "Handling failures" section: re-run with bad params (F=0.1),
     show how AiiDA records the failed CalcJob (exit code, stderr in provenance),
     contrast with Module 0 where the failure left no trace. From meeting notes. -->

## Next steps

You can now run external codes through AiiDA with full provenance tracking.
In {ref}`Module 2 <tutorial:module2>`, we will turn the regex we just wrote by hand into a tracked parsing step, so the scalar results from each simulation become individual database entries searchable across runs without opening any output file, and the Python that prepares inputs and parses outputs gets tracked as part of the same provenance.

## Further reading

- AiiDA's database layer: {ref}`topics:database`
- File storage: {ref}`topics:repository`
- The message broker: {ref}`internal_architecture:broker`
- Writing a CalcJob plugin for an external code: {ref}`how-to:plugin-codes`
- Process state machine: {ref}`topics:processes:concepts:state`
- Exit code semantics: {ref}`topics:processes:concepts:exit_codes`
- Built-in data nodes: {ref}`topics:data_types:core:singlefile`, {ref}`topics:data_types:core:folder`, {ref}`topics:data_types:core:remote`
- `verdi process dump` (workflows, profiles, groups): {ref}`how-to:data:dump`
