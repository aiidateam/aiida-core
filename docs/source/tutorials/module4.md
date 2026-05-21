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

<!-- SCAFFOLD / DRAFT.
     Scope: remote / HPC execution only. The run-vs-submit + daemon concept
     now lives in Module 3 (at the sweep, where blocking actually hurts);
     this module assumes the reader can already `submit()` and only changes
     *where* a calculation runs. Structure, storyline and prose are grounded
     in the existing how-to and topic docs (cross-references verified against
     this worktree). The remote-HPC steps cannot execute in the docs build
     (no cluster, no SSH), so all example code is illustrative `{code-block}`
     by design. TODO markers flag every remaining content decision.

     INTENDED APPROACH (JG notes, 2026-05): drive computer/code setup from a
     real registry YAML rather than hand-typed flags. See the expanded TODO
     blocks in "Configuring a remote computer" and "Registering a remote
     code" for the registry/search/code-type plan and its current blockers. -->


(tutorial:module4)=
# Module 4: Remote submission

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module4.ipynb` {octicon}`download`
:::

:::{note}
This module reuses the tutorial profile and the `python_code` object created in {ref}`Module 1 <tutorial:module1>`, and continues the workflow built in {ref}`Module 3 <tutorial:module3>`.
If you are following along locally, run those modules first — or, against your own profile, replace the setup cell at the top of the downloaded notebook with:

```python
from aiida import load_profile

load_profile()
```
:::

## What you will learn

After this module, you will be able to:

- Understand where a calculation runs: the computer, how AiiDA connects to it, and how its jobs are queued
- Configure a remote HPC cluster and register a code that lives on it
- Send your existing workflow to the cluster instead of your own machine
- Retrieve the results and see that the provenance is identical, wherever the work happened

```{code-cell} ipython3
:tags: ["remove-cell"]

# Auto-generated tutorial profile for docs build.
# If running locally with your own profile (e.g. from ``verdi presto``),
# replace this cell with:
#
#     from aiida import load_profile
#     load_profile()

%load_ext aiida
%run -i include/setup_tutorial.py
```

## Where calculations run

Every calculation so far has run on `localhost` — your own machine.
Real research rarely does: simulations run on **HPC clusters**, shared machines you reach over the network, where jobs wait in a scheduler queue until resources free up.

You do not rewrite your workflow for that.
In {ref}`Module 1 <tutorial:module1>` we met the two objects AiiDA uses to abstract *where* work happens:

- A **{ref}`Computer <how-to:run-codes:computer>`** describes *where* to run. It bundles the hostname, a **transport** (how AiiDA connects and moves files — `core.local` for your machine, `core.ssh` for a remote one) and a **scheduler** (how the machine runs jobs — `core.direct` runs them immediately, `core.slurm` / `core.pbspro` queue them through a batch system).
- A **{ref}`Code <how-to:run-codes:code>`** describes *what* runs there: the executable's path on that computer.

The tutorial's `localhost` is just the simplest case: local transport, direct scheduler.
Point a workflow at a different Computer and Code and the *same* workflow runs on a cluster — the rest of this module is setting those two up.

## Configuring a remote computer

:::{note}
The rendered tutorial cannot execute this section: the docs build has no HPC cluster and no SSH access.
The commands below are illustrative.
Run them against a cluster you have access to, substituting your hostname, account, transport and scheduler.
:::

Setting up a remote computer is a one-time, three-step process: **setup** (describe the machine), **configure** (the connection credentials), and **test** (verify it works):

<!-- TODO (JG notes, 2026-05): drive this from a real registry YAML, not
     hand-typed flags.

     - Use a real CSCS entry from `aiida-resource-registry`
       (github.com/aiidateam/aiida-resource-registry). Pick one machine
       (e.g. a CSCS cluster), ship a cleaned copy as `include/computer-cscs.yaml`,
       and show the full flow:
         $ verdi computer setup --config include/computer-cscs.yaml
         $ verdi computer configure core.ssh <label> --config include/...
         $ verdi computer test <label>
     - BLOCKER: `aiida-resource-registry` YAMLs are geared toward AiiDAlab and
       carry extra metadata fields that crash plain `verdi computer setup
       --config` in aiida-core. JG has an open PR addressing this. Until it
       merges, the `include/` copy must be the hand-cleaned (aiida-core-valid)
       version, and we note the caveat in prose.
     - Mention both registries: `aiida-code-registry` and
       `aiida-resource-registry`. JG's view: these overlap and should be
       merged; say so lightly (or in a note) rather than presenting them as
       two separate stable things.
     - Forward-looking: JG started a direct `verdi computer search` /
       `verdi code search` endpoint to query the registry from the CLI. NOT
       released yet (open PR) -> do not show as a working step; mention as
       "coming" at most, or omit until merged.
     - Cross-check option names against `verdi computer setup --help`.

     ALTERNATIVE / OPEN DECISION (do NOT implement yet — JG to verify):
     instead of an invented host, use a *real* SSH+SLURM target. The
     `xenonmiddleware/slurm` Docker image is exactly what aiida-core's own
     CI runs against, and this repo already ships aiida-core-valid configs:
       * .github/config/slurm-ssh.yaml        -> verdi computer setup
         (hostname localhost, transport core.ssh, scheduler core.slurm)
       * .github/config/slurm-ssh-config.yaml -> verdi computer configure
         core.ssh (port 5001, key auth, safe_interval 0)
       * .github/workflows/setup.sh shows the exact wiring.
     Reproducible by any reader, exercises a real scheduler, and sidesteps
     the aiida-resource-registry blocker entirely.
     TRADE-OFF to settle first: this requires Docker. Defensible for an
     advanced module, but conflicts with "keep things as simple as
     possible". Leaning: keep a simple illustrative (non-Docker) example
     as the default, offer the xenonmiddleware/slurm route as an optional
     "run it for real" dropdown — but confirm before implementing. -->

```{code-block} console
$ verdi computer setup \
    --label hpc \
    --hostname login.hpc.example.org \
    --transport core.ssh \
    --scheduler core.slurm
$ verdi computer configure core.ssh hpc --username myuser
$ verdi computer test hpc
```

`verdi computer test` runs a series of connection and scheduler checks.
They must all pass before the computer is usable: a green `verdi computer test` is the signal that AiiDA can reach the cluster, move files, and talk to its scheduler.

## Registering a remote code

With the computer in place, register the executable that lives on the cluster — the same `verdi code create` you would use locally, just pointed at the remote computer and its remote path:

<!-- TODO (JG notes, 2026-05):
     - Show registering a code from the same `aiida-resource-registry` CSCS
       entry (ship `include/code-cscs.yaml`), via
       `verdi code create core.code.installed --config include/code-cscs.yaml`.
     - THEN also show a "typical InstalledCode" the manual way (the common
       case: a real executable on the cluster, with prepend/append text for
       site `module load` lines — a very common real-world need).
     - Also briefly mention the other code types so readers know they exist:
         * InstalledCode      — executable already present on the computer
                                (what we use here)
         * PortableCode       — the executable/files are stored in AiiDA and
                                shipped to the computer at run time
         * ContainerizedCode  — runs inside a container (Singularity/Docker…)
       Keep it to a short note + {ref} pointers (verify anchors before going
       live: topics:data_types:core:code:installed / :portable /
       :containerized). -->


```{code-block} console
$ verdi code create core.code.installed \
    --label python3 \
    --computer hpc \
    --filepath-executable /usr/bin/python3 \
    --default-calc-job-plugin core.shell
```

The code is now addressable as `python3@hpc`, the same way the tutorial's local code is `python3@localhost`.

## Running there, unchanged

Here is the payoff.
The workflow from {ref}`Module 3 <tutorial:module3>` does not change at all.
You already know how to `submit()` it (Module 3); to run it on the cluster instead, you change exactly **one argument** — the `Code` — and submit as before:

<!-- TODO: show the Module 3 `gray_scott_sweep` rebuilt with the remote code
     and submitted, side by side with the local version, to make "one
     argument changed" concrete. -->

```{code-block} python
remote_code = load_code('python3@hpc')

wg_sweep = gray_scott_sweep.build(
    param_sweep=param_sweep,
    command=remote_code,  # the ONLY change: python3@hpc instead of python3@localhost
    script=script_node,
)
wg_sweep.submit()
```

From here the daemon does the rest: it opens the SSH connection, uploads the inputs, submits each job to the cluster's scheduler, polls until it finishes, and retrieves the outputs.
While a job sits in the cluster queue it shows up as `Waiting` in `verdi process list` (from {ref}`Module 3 <tutorial:module3>`) — the scheduler state is just another thing AiiDA records.

## Retrieving results, wherever they ran

When the jobs finish, the provenance graph looks **identical** to a local run: same nodes, same links.
Where the work physically happened is just metadata on the nodes.

Every CalcJob exposes a `remote_folder` output, a {ref}`RemoteData <topics:data_types:core:remote>` node pointing at the working directory on the computer where it ran.
You already saw this on `localhost` in {ref}`Module 1 <tutorial:module1>`; on a cluster it points into the remote filesystem instead:

<!-- TODO: this part IS runnable on localhost — could graduate to a live
     `{code-cell}` reusing a Module 1-style node to show `remote_folder`.
     Keep the remote-specific commentary illustrative. -->

```{code-block} python
calcjob = wg_sweep.process  # ... drill down to a child CalcJob node
print(calcjob.outputs.remote_folder.get_remote_path())
```

Two commands make remote results tangible:

- `verdi calcjob gotocomputer <PK>` opens an SSH session on the computer, dropping you straight into that working directory — invaluable for inspecting a job on the cluster after it finished or failed.
- `verdi process dump <PK>` (from {ref}`Module 1 <tutorial:module1>`) pulls the full inputs/outputs/logs tree back to your machine as readable files, so you can inspect a remote run without leaving your laptop.

The lesson of this module is a single sentence: **AiiDA decouples *what* you compute from *where* it runs.** A workflow you debugged on your laptop scales to a supercomputer by changing one argument, and the provenance you get back is the same either way.

## Next steps

You can now run your workflows on remote HPC clusters with full provenance.
The remaining modules each pick up an independent thread and can be tackled in any order:

- {ref}`Module 5 <tutorial:module5>` — querying the database with the `QueryBuilder`
- {ref}`Module 6 <tutorial:module6>` — more advanced workflow patterns (conditionals, dynamic graphs, sub-workflow composition)
- {ref}`Module 7 <tutorial:module7>` — handling failures and recovering from them

## Further reading

- Transports (how AiiDA connects to computers): {ref}`topics:transport`
- Schedulers (batch systems that queue jobs): {ref}`topics:schedulers`
- Setting up and configuring computers: {ref}`how-to:run-codes:computer:setup`, {ref}`how-to:run-codes:computer:configuration`
- `verdi calcjob gotocomputer` and other real-world run tips: {ref}`how-to:real-world-tricks`
