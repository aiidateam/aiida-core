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

## Setting up your AiiDA profile

An AiiDA **profile** defines the configuration for an AiiDA instance:

- The **database** that stores the provenance graph[^profile-db]
- The **file repository** that stores file contents and other binary data[^profile-repo]
- The **process broker** that coordinates running calculations[^profile-broker]

Before running any calculations, you need one.

[^profile-db]: See {ref}`topics:database` for more on AiiDA's database layer.
[^profile-repo]: See {ref}`topics:repository` for more on file storage.
[^profile-broker]: See {ref}`internal_architecture:broker` for more on the message broker.

If you are working on your own machine, the easiest way is:

```console
$ verdi presto
```

This creates a lightweight local profile with sensible defaults for all three: SQLite for the database, [disk-objectstore](https://github.com/aiidateam/disk-objectstore) for file storage, and the built-in **ZMQ message broker**.
For more advanced high-throughput production setups (PostgreSQL, RabbitMQ), see the {ref}`installation guide <installation>`.

```{code-cell} ipython3
:tags: ["remove-cell"]

# Auto-generated tutorial profile for docs build.
# If running locally with your own profile (e.g. from ``verdi presto``),
# replace this cell with:
#
#     from aiida import load_profile
#     load_profile()

%load_ext aiida

# Stop any leftover daemon and delete any existing tutorial profile,
# so each docs build starts fresh. Modules 2+ reuse the profile created here.
from aiida.engine.daemon.client import get_daemon_client
from aiida.manage.configuration import get_config
_config = get_config()
if 'tutorial' in _config.profile_names:
    _daemon_client = get_daemon_client('tutorial')
    if _daemon_client.is_daemon_running:
        _daemon_client.stop_daemon(wait=True)
    _config.delete_profile('tutorial', delete_storage=True)

%run -i include/setup_tutorial.py
```

You can verify that the profile is set up correctly with `verdi status`:

```{code-cell} ipython3
# Check that the AiiDA profile is configured and all services are reachable.
%verdi status
```

:::{note}
We use IPython magic commands like `%verdi <cmd>` in Code cells (`%verdi` runs a `verdi` CLI command from the notebook).[^magics] To execute in a terminal, drop the `%` prefix.
:::

[^magics]: `%load_ext aiida` (in the hidden setup cell) registers the `%verdi` magic. `%run -i script.py` executes a Python file in the current namespace, equivalent to pasting its contents into the cell. The `from include.constants import ...` lines pull shared parameters from {download}`include/constants.py` so the code cells stay focused on AiiDA concepts.

## Running the simulation with `aiida-shell`

In {ref}`Module 0 <tutorial:module0>`, we ran the simulation directly from the command line.
Now let's run it through AiiDA, so the inputs, outputs, and execution metadata get captured in the provenance graph.

AiiDA uses the **{ref}`CalcJob <topics:calculations:concepts:calcjobs>`** class to manage external executables by preparing input files, executing the code (locally or on a remote cluster), retrieving output files, and optionally parsing the results.

The fastest way to run a CalcJob is with [`aiida-shell`](https://aiida-shell.readthedocs.io), which wraps any shell command without requiring additional plugin code.[^plugin-codes]
Below, we use its `launch_shell_job` helper with the same input file as in {ref}`Module 0 <tutorial:module0>`:

[^plugin-codes]: For writing your own CalcJob plugin (custom input preparation, exit codes, parsing), see {ref}`how to write a plugin for an external code <how-to:plugin-codes>`.

```{code-cell} ipython3
# Run the simulation through AiiDA using aiida-shell's launch_shell_job.
from pathlib import Path

from aiida_shell import launch_shell_job

from include.constants import SCRIPT_PATH

input_path = Path('include/input.yaml').resolve()

results, node = launch_shell_job(
    python_code,
    arguments='{script} --input {input} --output results.yaml',
    nodes={'script': SCRIPT_PATH, 'input': input_path},
    outputs=['results.yaml'],
)

print(f"Process PK: {node.pk}")
print(f"Exit status: {node.exit_status}")
print(f"Stdout: {results['stdout'].get_content()}")
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
- A **{ref}`Code <how-to:run-codes:code>`** defines *what* executable runs on that computer. `aiida-shell` creates this automatically from the command you pass to `launch_shell_job`.

## Exploring the provenance graph

AiiDA automatically builds a **provenance graph** that records exactly how each piece of data was produced:

```{code-cell} ipython3
---
mystnb:
    image:
        width: 100%
---
# Generate and display the provenance graph for this calculation.
%run -i include/plot_provenance.py
plot_provenance(node)
```

In the graph:
- **Green ellipses** are data nodes (inputs and outputs)
- **Rectangles** are process nodes (the computation)
- **Arrows** show the data flow

This graph answers questions like *"Where did this number come from?"* and *"What parameters produced this result?"*, even months later.

:::{tip}
Open the image in a new tab for a larger view. You can also generate provenance graphs from the command line with `verdi node graph generate <PK>`.
:::

## Inspecting the calculation

AiiDA records the full lifecycle of every CalcJob.
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
We can also access them programmatically:

```{code-cell} ipython3
# List all output nodes returned by the CalcJob.
for label, output_node in sorted(results.items()):
    print(f"{label + ':':<13} {type(output_node).__name__} (PK={output_node.pk})")
```

:::{note}
The output label `results_yaml` corresponds to the file we declared as `results.yaml` in the `outputs=` argument to `launch_shell_job`. AiiDA replaces dots with underscores because link labels must be valid Python identifiers.
:::

Each output plays a different role:

- `results_yaml`: the main output file we declared via `outputs=`.
- `stdout` / `stderr`: the captured standard streams of the script.
- `retrieved`: a `FolderData` containing everything AiiDA fetched back from the working directory.
- `remote_folder`: a `RemoteData` pointing to the working directory on the Computer where the job ran (typically a remote HPC):

```{code-cell} ipython3
# Print the path of the remote working directory.
print(f"Remote folder: {node.outputs.remote_folder.get_remote_path()}")
```

From the command line, `verdi calcjob gotocomputer <PK>` SSHes into the Computer and drops you directly into that working directory.

The YAML results file itself is a `SinglefileData` node.
We can open it and extract the scalar results from our simulation:

```{code-cell} ipython3
# Open the YAML output node and extract scalar results.
import yaml

result_file = node.outputs.results_yaml

with result_file.open(mode='r') as f:
    data = yaml.safe_load(f)
    print(f"variance(V) = {data['variance_V']:.4e}")
    print(f"mean(V)     = {data['mean_V']:.4e}")
```

<!-- TODO: Add `verdi shell` subsection — interactive exploration of the database
     (load nodes, inspect attributes, follow links). From meeting notes. -->

## Dumping calculation data

AiiDA stores everything in its internal database and file repository (efficient for machines, opaque for humans).
`verdi process dump` writes the same data out as a human-readable directory tree of inputs, outputs, and logs:

```{code-cell} ipython3
:tags: ["hide-output"]

# Export the full calculation (inputs, outputs, logs) to a directory.
import tempfile

dump_path = tempfile.mkdtemp(prefix='aiida_tut_dump_')
%verdi process dump {node.pk} --path {dump_path} -o
```

```{code-cell} ipython3
# Show the directory tree of the dumped calculation data.
!tree {dump_path}
```

All the relevant entities of the calculation are there: the input file, the simulation script, the submission script, captured stdout and stderr, and AiiDA metadata.
This is useful for debugging or sharing calculation data outside of AiiDA.

<!-- TODO: Add "Handling failures" section — re-run with bad params (F=0.1),
     show how AiiDA records the failed CalcJob (exit code, stderr in provenance),
     contrast with Module 0 where the failure left no trace. From meeting notes. -->

## Summary

In this module you learned to:

- **Set up** an AiiDA profile with `verdi presto`
- **Run** an external code via `aiida-shell`'s `launch_shell_job`
- **Visualize** the provenance graph of the calculation
- **Inspect** the calculation from the `verdi` CLI and the Python API
- **Export** calculation data as a human-readable directory with `verdi process dump`

## Next steps

You can now run external codes through AiiDA with full provenance tracking.
In {ref}`Module 2 <tutorial:module2>`, the result values from each simulation become individual database entries, searchable across runs without opening any output file.
The Python that prepares inputs and parses outputs gets tracked as part of the same provenance.

## Footnotes
