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

(tutorial:module4)=
# Module 4: Remote submission

<!-- TODO: re-enable once the md->ipynb conversion script is verified
:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module4.ipynb` {octicon}`download`
:::
-->

:::{note}
This module reuses the tutorial profile created in {ref}`Module 1 <tutorial:module1>`.
If you are following along locally, run that module first.
To use your own profile instead, replace the setup cell at the top of the downloaded notebook with:

```python
from aiida import load_profile

load_profile()
```
:::

## What you will learn

After this module, you will be able to:

- Register a remote HPC cluster (setup → configure → test) and a code that lives on it
- Submit a calculation to that cluster and inspect the result with the same commands as for a local run
- Set per-job scheduler options (resources, queue, account, wall-time) via `metadata.options`
- Switch a workflow between local and remote execution without changing the workflow itself

```{code-cell} ipython3
:tags: ["remove-cell"]

# Tutorial profile setup (shared across modules).
%load_ext aiida
%run -i include/setup_tutorial.py
```

```{code-cell} ipython3
:tags: ["remove-cell"]

# SSH plumbing for the SLURM container (key + ~/.ssh/config).
# If running locally, you would configure SSH to your own cluster instead.
%run -i include/setup_slurm.py
```

## Where calculations run

Every calculation so far has run on `localhost`, your own machine.
Real research rarely does: simulations run on **HPC clusters**, shared machines you reach over the network, where jobs wait in a scheduler queue until resources free up.

You do **not** have to rewrite your workflow for that.
In {ref}`Module 1 <tutorial:module1>` we met the two objects AiiDA uses to abstract where work happens:

- A **{ref}`Computer <how-to:run-codes:computer>`** describes *where* to run. It bundles the hostname, a **transport**, and a **scheduler**.
- A **{ref}`Code <how-to:run-codes:code>`** describes *what* runs there: the executable's path on that computer.

The tutorial's `localhost` is just the simplest case: local transport, direct scheduler.
Here is what it looks like from the inside:

```{code-cell} ipython3
%verdi computer show localhost
```

The `transport_type` is `core.local` (copy files on the same filesystem) and the `scheduler_type` is `core.direct` (run immediately, no queue).
A remote HPC cluster differs in exactly these two fields: `core.ssh_async` for the transport, and `core.slurm` (or `core.pbspro`, `core.sge`, etc.) for the scheduler.
The majority of this module is setting those two up.

## Registering a remote computer

Registering a remote computer is a one-time, three-step process: **setup** (describe the machine), **configure** (provide connection credentials), and **test** (verify everything works).
We walk through each step with `verdi` commands, but the same operations are of course also available through the Python API.
We include the relevant code via dropdowns below.

:::{note}
This tutorial uses a SLURM container reachable over SSH so that every cell executes automatically during the docs build.
A hidden cell handles the SSH plumbing (key and `~/.ssh/config`); all `verdi` commands below run live.
In practice, you would register whichever HPC cluster you actually have access to.
:::

### Setup

`verdi computer setup` registers the machine in AiiDA's database:

```{code-cell} ipython3
:tags: ["remove-cell"]

# Clean up any slurm-ssh computer left over from a previous build so the
# live `verdi computer setup` cell is idempotent across rebuilds.
from contextlib import suppress

from aiida.common.exceptions import NotExistent
from aiida.orm import AuthInfo, Computer, Node, QueryBuilder, User, load_computer
from aiida.tools import delete_nodes

with suppress(NotExistent):
    _old = load_computer('slurm-ssh')
    _node_pks = (
        QueryBuilder()
        .append(Computer, filters={'id': _old.pk}, tag='comp')
        .append(Node, with_computer='comp', project='id')
        .all(flat=True)
    )
    if _node_pks:
        delete_nodes(_node_pks, dry_run=False)
    with suppress(NotExistent):
        _ai = _old.get_authinfo(User.collection.get_default())
        AuthInfo.collection.delete(_ai.pk)
    Computer.collection.delete(_old.pk)
```

```{code-cell} ipython3
%verdi computer setup \
    --label slurm-ssh \
    --description 'Containerized SLURM cluster used by the AiiDA tutorial.' \
    --hostname slurm-ssh \
    --transport core.ssh_async \
    --scheduler core.slurm \
    --work-dir /home/{username}/workdir \
    --mpiprocs-per-machine 1 \
    --default-memory-per-machine 1024 \
    --non-interactive
```

The key flags:

- `--transport core.ssh_async`: AiiDA connects and moves files over SSH.
- `--scheduler core.slurm`: jobs go through SLURM (`sbatch`, `squeue`, `scancel`). Other options include `core.pbspro`, `core.sge`, `core.lsf`, and `core.direct` (no scheduler, run immediately).
- `--work-dir`: where AiiDA creates per-calculation working directories on the remote machine. `{username}` is expanded at runtime.
- `--mpiprocs-per-machine` and `--default-memory-per-machine` (the latter in kB): per-node defaults used as fallbacks when a calculation doesn't specify them. Most production HPC schedulers require both, and setting them at the computer level means individual calculations don't have to repeat them. They are easily overridden per submission via `metadata.options` (shown later in this module). We use a tiny `1024` kB (1 MB) here for the tutorial; on a real cluster, raise this to your node's actual per-machine RAM.

On a real HPC cluster, the hostname typically is the cluster's login node and the work directory is on a scratch filesystem.

Instead of providing individual CLI flags, you can also pass a YAML file:

```console
$ verdi computer setup --config slurm-ssh-setup.yaml
```

:::{dropdown} Example:&nbsp;`slurm-ssh-setup.yaml`
```yaml
label: slurm-ssh
description: Containerized SLURM cluster used by the AiiDA tutorial.
hostname: slurm-ssh
transport: core.ssh_async
scheduler: core.slurm
work_dir: /home/{username}/workdir
mpiprocs_per_machine: 1
default_memory_per_machine: 1024  # tutorial container; raise on real clusters
```
:::

This YAML is the equivalent of the CLI invocation in the live cell above (same keys, same values), and is the config we use to register the SLURM container that runs this tutorial's live remote-submission cells.

The [AiiDA resource registry](https://github.com/aiidateam/aiida-resource-registry) maintains ready-made YAML configs for common HPC centres.
Download the one for your cluster and pass it directly.
If your cluster is not listed yet, contributions are more than welcome: open a PR to add your YAML files so others can benefit too.

Going the other way: once you have a working setup, export it back to YAML for sharing, version control, or a registry PR:

```console
$ verdi computer export setup slurm-ssh slurm-ssh-setup.yaml
$ verdi computer export config slurm-ssh slurm-ssh-config.yaml
```

The same works for codes: `verdi code export <code> <file>`.

:::{tip}
Run interactively (no `--non-interactive`), `verdi computer setup` opens an editor at the end where you can set `prepend_text` and `append_text`: shell snippets that run on the remote machine *before* and *after* every job on this computer.
Use them for site-wide setup that applies regardless of which code is running (sourcing a profile, exporting cluster-specific variables, etc.).
These are computer-level; codes can override or extend them with their own `prepend_text` / `append_text` (shown below for `verdi code create`).
:::

:::{dropdown} Python API: computer setup
```python
from aiida.orm import Computer

computer = Computer(
    label='slurm-ssh',
    description='Containerized SLURM cluster used by the AiiDA tutorial.',
    hostname='slurm-ssh',
    transport_type='core.ssh_async',
    scheduler_type='core.slurm',
    workdir='/home/{username}/workdir',
    metadata={
        'default_mpiprocs_per_machine': 1,
        'default_memory_per_machine': 1024,  # 1 MB; raise on real clusters
    },
).store()
```
:::

### Configure

`verdi computer configure` provides the connection details for the chosen transport.

For `core.ssh_async`, AiiDA reads your `~/.ssh/config`, so as long as `ssh <hostname>` works from your terminal, the configure step needs no extra credentials:

```{code-cell} ipython3
%verdi computer configure core.ssh_async slurm-ssh --safe-interval 0 --non-interactive
```

`--safe-interval` is the minimum cooldown, in seconds, between opening successive SSH connections to this computer.
AiiDA uses it to space out concurrent tasks so they don't overwhelm the login node or the shared SSH daemon.
The default for SSH-based transports (`core.ssh`, `core.ssh_async`) is `15` seconds.
We use `0` here so the tutorial cells return quickly against the local SLURM container. **Do not do this on a real cluster**: no cooldown can get your account flagged or banned.
Leave the default in place unless the cluster's documentation recommends otherwise (see {ref}`how-to:run-codes:computer:connection`).

:::{dropdown} Python API: computer configure
```python
computer.configure(safe_interval=0)
```

`configure()` accepts the same keyword arguments as the `verdi computer configure` prompts; valid keys are whatever `transport_cls.get_valid_auth_params()` returns for the chosen transport (for `core.ssh_async`: `safe_interval`, `host`, `port`, `username`, ...).
:::

:::{warning}
The older `core.ssh` transport is **deprecated and will be removed in v3.0**.
It requires configuring username, port, key path, and other SSH parameters through `verdi` prompts.
`core.ssh_async` replaces it: it is significantly faster and delegates connection settings to your `~/.ssh/config`, which is simpler and more consistent with how you already manage SSH connections.
:::

```{code-cell} ipython3
:tags: ["remove-cell"]

# Hidden: drop the scheduler-poll interval to 1s so the SLURM-container
# round-trip below finishes quickly during the docs build. Not something
# you would normally tweak; the default value is fine on real clusters.
from aiida.orm import load_computer
load_computer('slurm-ssh').set_minimum_job_poll_interval(1)
```

Let's inspect the computer we just registered:

```{code-cell} ipython3
%verdi computer show slurm-ssh
```

### Test

`verdi computer test` runs a series of connection and scheduler checks.
All checks must pass before the computer is usable:

```{code-cell} ipython3
%verdi computer test slurm-ssh
```

```{code-cell} ipython3
:tags: ["remove-cell"]

# Fail-fast assertion: `verdi computer test` only WARNS on failure, so a
# broken connection sails past that cell and any later cell that actually
# uses the transport (e.g. `launch_shell_job` below) hangs until the
# notebook execution timeout fires, masking the real cause. Open the
# transport directly here so a connection failure raises with a real
# traceback at the cell where the diagnosis actually lives.
from aiida.orm import load_computer
with load_computer('slurm-ssh').get_transport() as _t:
    _t.whoami()
```

You now have two computers in your profile:

```{code-cell} ipython3
%verdi computer list
```

A profile is not tied to a single cluster.
Register as many computers as you have access to, once each, and any subsequent submission picks one by label. The workflow code stays the same regardless of how many clusters are configured.

:::{tip}
AiiDA itself runs on your local machine, not on the HPC.
The cluster only ever sees standard SSH connections and scheduler commands (`sbatch`, `squeue`, ...), so **nothing needs to be installed on the HPC and no sudo rights are required** (neither of which most users would have anyway).
From a single local installation you can drive jobs against several heterogeneous clusters at the same time (different schedulers, different work directories, different codes), each registered as its own `Computer`.
The same workflow, unchanged, can submit some calculations to one cluster and others to another.
:::

## Registering a remote code

With the computer in place, you can now register executables that are available on the cluster.
AiiDA supports three code types:

- **{ref}`InstalledCode <topics:data_types:core:code:installed>`**: the executable is already present on the computer. This is the common case: your simulation code is installed on the cluster.
- **{ref}`PortableCode <topics:data_types:core:code:portable>`**: AiiDA stores the code in its repository and uploads it to the computer at run time. Useful for small scripts or tools you want to keep versioned in AiiDA.
- **{ref}`ContainerizedCode <topics:data_types:core:code:containerized>`**: the executable runs inside a container (Singularity, Docker) on the computer.

For an `InstalledCode`, you specify the path to the executable on the remote machine.
Let's register `gsrd` on the tutorial's SLURM container:

```{code-cell} ipython3
%verdi code create core.code.installed \
    --label gsrd \
    --computer slurm-ssh \
    --filepath-executable /opt/gsrd/bin/gsrd \
    --default-calc-job-plugin core.shell \
    --non-interactive
```

The code is now addressable as `gsrd@slurm-ssh`, just like the local code is `gsrd@localhost`.

Just as `verdi computer test` checks the connection, `verdi code test` verifies the code is usable.
For an `InstalledCode`, it checks that the computer is reachable and that the specified executable exists at the given path:

```{code-cell} ipython3
%verdi code test gsrd@slurm-ssh
```

:::{dropdown} Python API: code registration
```python
from aiida.orm import InstalledCode

code = InstalledCode(
    label='gsrd',
    computer=computer,
    filepath_executable='/opt/gsrd/bin/gsrd',
    default_calc_job_plugin='core.shell',
).store()
```
:::

:::{tip}
On a real cluster, the executable is usually activated through a module system.
The `--prepend-text` flag adds lines to the job script *before* the executable, typically `module load` commands:

```console
$ verdi code create core.code.installed \
    --label gsrd \
    --computer daint \
    --filepath-executable /apps/gsrd/bin/gsrd \
    --default-calc-job-plugin core.shell \
    --prepend-text 'module load gsrd/1.0'
```

This is the single most common customization for HPC codes: the executable exists, but the environment must be set up first.
:::

Here are all codes registered in this profile:

```{code-cell} ipython3
%verdi code list -A
```


## Running on the cluster

The only thing that changes between running locally and running on a cluster is a single string: `'gsrd@localhost'` becomes `'gsrd@slurm-ssh'`.
Everything else stays exactly the same: same arguments, same inputs, same outputs, same provenance graph.

:::{important}
That swap is so cheap because **AiiDA abstracts away the transport and scheduler layers** that normally make HPC submission painful.
The user-facing API is the same regardless of where work actually runs, so changing target cluster amounts to swapping a label (or a `Code` node).

The trade is that you pay an upfront, one-time cost for each cluster you want to use (computer setup → configure → test → code create), and from then on every calculation or workflow targets it by label.
:::

Concretely, the only line of the {ref}`Module 1 <tutorial:module1>` example that differs is the code we load:

```{code-cell} ipython3
from aiida.orm import load_code

# The only line that changes vs Module 1: the @-suffix points to the
# remote cluster (`@slurm-ssh`) instead of the local machine (`@localhost`).
gsrd_remote = load_code('gsrd@slurm-ssh')
```

The submission itself is then byte-for-byte identical to the local run from {ref}`Module 1 <tutorial:module1>`. We just pass `gsrd_remote` as the code argument to `launch_shell_job`.
Expand the cell below to see the call and its output:

```{code-cell} ipython3
:tags: ["hide-cell"]

from pathlib import Path

from aiida_shell import launch_shell_job

input_path = Path('include/input.yaml').resolve()

results, node = launch_shell_job(
    gsrd_remote,
    arguments='{input}',
    nodes={'input': input_path},
    outputs=['results.npz'],
)

print(f"Process PK:  {node.pk}")
print(f"Computer:    {node.computer.label}")
print(f"Exit status: {node.exit_status}")
```

In the printed output, `Computer` now reads `slurm-ssh` instead of `localhost`.
That single change in the output mirrors the single change in the call.
Everything in between, the full remote-job lifecycle, was driven by AiiDA on your behalf; you have to do none of it manually:

- Opening the SSH connection to the cluster.
- Transporting the input files to the remote working directory.
- Submitting the job to the scheduler (`sbatch` under the hood).
- Monitoring it until it finishes (`squeue` polling).
- Pulling the outputs back to your local repository.

:::{note}
We used `launch_shell_job(...)`, which blocks until the job finishes.
For real work, you would `submit()` the calculation (or a workflow wrapping it) to the AiiDA daemon, as shown in {ref}`Module 3 <tutorial:module3>`, and let it run in the background.
While a job sits in the cluster queue, it shows up as `Waiting` in `verdi process list`.
:::

The outputs are present and identical to Module 1's local run: same numbers, same provenance, only the computation location differs.
Click *Show cell* below to expand the same parsing code we used in Module 1 and convince yourself that the result is identical:

```{code-cell} ipython3
:tags: ["hide-cell"]

# Inspect the outputs (same parsing as Module 1).
import io

import numpy as np

from include.constants import MEAN_RE, VARIANCE_RE

with node.outputs.results_npz.open(mode='rb') as fh:
    arrays = np.load(io.BytesIO(fh.read()))
    v_field = arrays['V_final']

stdout_text = node.outputs.stdout.get_content()
var_v = float(VARIANCE_RE.search(stdout_text).group(1))
mean_v = float(MEAN_RE.search(stdout_text).group(1))

print(f"V field shape: {v_field.shape}")
print(f"variance(V) = {var_v:.4e}")
print(f"mean(V)     = {mean_v:.4e}")
```

The same swap also isn't specific to `launch_shell_job`: it works for the pipeline from {ref}`Module 2 <tutorial:module2>`, the `gray_scott_sweep` workflow from {ref}`Module 3 <tutorial:module3>`, and any {ref}`CalcJob <topics:calculations:concepts:calcjobs>` or {ref}`WorkChain <topics:workflows>` you may write in the future.

### Per-calculation scheduler options

The submission above worked because the tutorial's SLURM container has no queue limits, no project accounting, and no wallclock enforcement.
Real HPC centres almost always require you to specify, per job: how many nodes and MPI processes, which queue (partition), which project account, and how long the job is allowed to run.
These are not computer-level defaults; they vary per calculation.

You can set them through `metadata.options` on the submission.
With `aiida-shell`'s `launch_shell_job`, that means passing `metadata=...`:

```python
results, node = launch_shell_job(
    gsrd_remote,
    arguments='{input}',
    nodes={'input': input_path},
    outputs=['results.npz'],
    metadata={
        'options': {
            'resources': {'num_machines': 2, 'num_mpiprocs_per_machine': 16},
            'queue_name': 'debug',
            'account': 'proj123',
            'max_wallclock_seconds': 2 * 60 * 60,  # 2 hours
        },
    },
)
```

The same `metadata.options` namespace is available on `CalcJob` and `WorkChain` builders.
For workflows, you set them once at the entry point of your workflow and they propagate downstream.

Compared to the local-run call this makes the submission code visibly more verbose, but that verbosity is not an AiiDA artefact: those flags are simply what every batch scheduler needs to size, schedule, and bill a job, regardless of how you submit.
Filling them in is part of running on HPC.

:::{dropdown} The most commonly used&nbsp;`metadata.options`&nbsp;keys
| Key | Purpose |
|---|---|
| `resources` | `num_machines`, `num_mpiprocs_per_machine`, etc. The minimum the scheduler needs to size the job. |
| `queue_name` | Scheduler queue/partition (`debug`, `normal`, `gpu`, ...). |
| `account` | Project/account code for billing. Often mandatory at supercomputer centres. |
| `max_wallclock_seconds` | Wall-time limit. Real HPC centres almost always require this. |
| `custom_scheduler_commands` | Raw extra scheduler directives (e.g. `#SBATCH --constraint=mc`) for anything not covered by the keys above. |
| `environment_variables` | Per-job env vars exported in the job script. |
| `prepend_text` / `append_text` | Per-job shell snippets (in addition to whatever is set at the code and computer level). |

The full list lives in {ref}`how-to:real-world-tricks` ("Full list of metadata available").
:::

## Inspecting remote calculations

Every CalcJob exposes a `remote_folder` output, a {ref}`RemoteData <topics:data_types:core:remote>` node pointing at the working directory on the computer where it ran:

```{code-cell} ipython3
print(f"Remote working directory: {node.outputs.remote_folder.get_remote_path()}")
```

:::{note}
The path looks like `<work-dir>/<aa>/<bb>/<rest-of-uuid>` because AiiDA shards the working directory by the calculation node's UUID.
The first two characters form the top-level directory, the next two the second-level directory, and the remaining 32 characters the leaf.
This keeps any single directory from accumulating millions of entries on long-running profiles, which would slow down `ls`, scheduler scans, and backup tools.
:::

Two `verdi` commands make remote results tangible:

- **`verdi calcjob gotocomputer <PK>`** opens an SSH session and drops you straight into that working directory on the cluster. Invaluable for inspecting a job after it finished or failed.
- **`verdi process dump <PK>`** (from {ref}`Module 1 <tutorial:module1>`) writes out the inputs, outputs, and logs that AiiDA has already retrieved into its local file repository, as a human-readable directory tree on disk.

```{code-cell} ipython3
:tags: ["hide-output"]

%verdi process show {node.pk}
```

The `Computer` column now reads `slurm-ssh` instead of `localhost`.
Everything else (the input/output links, the exit status, the `verdi` commands you use to inspect it) is identical.

## Next steps

You can now run calculations on remote HPC clusters with full provenance.
The remaining modules each pick up an independent thread and can be tackled in any order:

- {ref}`Module 5 <tutorial:module5>`: querying the database with the `QueryBuilder`
- {ref}`Module 6 <tutorial:module6>`: more advanced workflow patterns (conditionals, dynamic graphs, sub-workflow composition)
- {ref}`Module 7 <tutorial:module7>`: handling failures and recovering from them

## Further reading

- Transports (how AiiDA connects to computers): {ref}`topics:transport`
- Schedulers (batch systems that queue jobs): {ref}`topics:schedulers`
- Setting up and configuring computers: {ref}`how-to:run-codes:computer:setup`, {ref}`how-to:run-codes:computer:configuration`
- Code types (InstalledCode, PortableCode, ContainerizedCode): {ref}`topics:data_types:core:code`
- The AiiDA resource registry (pre-built computer/code configs): [github.com/aiidateam/aiida-resource-registry](https://github.com/aiidateam/aiida-resource-registry)
- `verdi calcjob gotocomputer` and other practical tips: {ref}`how-to:real-world-tricks`
