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

(tutorial:module7)=
# Module 7: Where to go next

:::{note}
This module reuses the tutorial profile and the `gsrd_code` object created in {ref}`Module 1 <tutorial:module1>`.
If you are following along locally, run that first.
:::

## What you will learn

By the end of this module, you will have a map of the wider AiiDA world and concrete pointers for taking the next step.
Specifically:

- How to make a workflow **recover** from a failed calculation using a WorkGraph error handler, instead of giving up.
- Why **CalcJob plugins** exist, what they look like, and when to write one instead of staying with `aiida-shell`.
- How **WorkChains** relate to WorkGraph, and when you'll meet them in the wild.
- How **caching** lets you re-run the same workflow at near-zero cost, and how to inspect cache hits.
- An overview of the **plugin ecosystem**, with one card per plugin and a link.

This module is a survey, not a deep dive: each section is a concrete demo or sketch plus a pointer to the canonical reference.

:::{note} Setup
This module touches AiiDA, `aiida-shell`, and `aiida-workgraph`:

```bash
pip install aiida-core aiida-shell aiida-workgraph
```

Install `aiida-core`, not `aiida` (the latter is an old meta-package).
:::

```{code-cell} ipython3
# Set up the tutorial's isolated sandbox profile (same as Module 1).
# `%load_ext aiida` enables the `%verdi` magic; `%run` creates or loads the
# shared `tutorial-<hash>` profile, so data from earlier modules is available.
%load_ext aiida
%run -i include/setup_tutorial.py
```

## Error handling: recovering from a failed calculation

By {ref}`Module 6 <tutorial:module6>` we built workflows that could *decide* what to run from intermediate data.
The next adaptive feature is what should happen when a step doesn't merely return a boring result, but actually **fails**.

Every AiiDA process reports an integer **exit code** when it ends: `0` means success, anything else is a specific failure mode declared by the plugin.
WorkGraph lets you attach an **error handler** to a task that fires when its exit code matches a list you specify, gives the handler a chance to mutate the task's inputs, and then re-runs the task.

We need a failure to trigger the handler.
`gsrd`'s integrator becomes numerically unstable if you push the time step past the explicit-scheme stability bound (`dt` too large for the diffusion constants).
When that happens, `gsrd` emits an `ERR: field values departed manifold` message and skips writing `results.npz`.
From `aiida-shell`'s point of view, the requested output file is missing, so the ShellJob exits with `ERROR_OUTPUT_FILEPATHS_MISSING` (exit code 303):

```{code-cell} ipython3
from aiida_shell.calculations.shell import ShellJob
print(ShellJob.exit_codes.ERROR_OUTPUT_FILEPATHS_MISSING)
```

Let's confirm the failure mode end-to-end before wiring anything fancy:

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show first run (unstable `dt`, will fail)'
:    code_prompt_hide: 'Hide first run'

import io
import yaml

from aiida import orm
from aiida_shell import launch_shell_job

# The default Gray-Scott parameters (same as earlier modules).
BASE_PARAMS = {
    'grid_size': 64,
    'du': 0.16,
    'dv': 0.08,
    'F': 0.04,
    'k': 0.065,
    'dt': 1.0,
    'n_steps': 3000,
    'seed': 42,
}

unstable_params = {**BASE_PARAMS, 'dt': 10.0, 'n_steps': 500}
input_file = orm.SinglefileData(
    io.BytesIO(yaml.dump(unstable_params).encode()),
    filename='input.yaml',
)

_, node_fail = launch_shell_job(
    gsrd_code,
    arguments='{input}',
    nodes={'input': input_file},
    outputs=['results.npz'],
)
```

```{code-cell} ipython3
print(f'Exit status : {node_fail.exit_status}')
print(f'Exit message: {node_fail.exit_message}')
```

The process is `Finished`, but with a non-zero exit code: AiiDA has recorded both the failed inputs *and* the exit code in the provenance graph.
We can now write a handler that knows how to recover from this specific failure.

### Attaching an error handler

A handler is a plain Python function that takes the failed task and mutates its inputs.
Here, the recovery is to halve `dt` (so the integrator becomes stable again) and let WorkGraph rerun the same ShellJob with the corrected input file:

```{code-cell} ipython3
def halve_dt(task):
    """Recover from `gsrd`'s numerical-instability failure by halving `dt`."""
    current_input = task.inputs.nodes.input.value
    with current_input.open(mode='r') as fh:
        params = yaml.safe_load(fh.read())
    params['dt'] = params['dt'] / 2.0
    new_input = orm.SinglefileData(
        io.BytesIO(yaml.dump(params).encode()),
        filename='input.yaml',
    )
    task.set_inputs({'nodes': {'input': new_input}})
    return f"reduced dt to {params['dt']} and retrying"
```

Two details worth a look before we wire it in:

- The handler signature is `(task) -> str | None`. It receives the failed task with its inputs still bound to the values from the failing run, mutates them in place via `task.set_inputs(...)`, and optionally returns a short status message that ends up in the process report.
- We **construct a new `SinglefileData`** for the corrected input file rather than mutating the old one. Stored AiiDA nodes are immutable; the provenance will record the new input node as the input to the *retry* of the ShellJob, with the original failed input still present as the input to the first attempt.

We attach the handler by building a small WorkGraph imperatively (the imperative `with WorkGraph(...)` form gives us a named handle on the ShellJob task, which the `add_error_handler` method lives on):

```{code-cell} ipython3
from aiida_workgraph import WorkGraph, shelljob

with WorkGraph(name='resilient_gsrd') as wg:
    shelljob(
        command=gsrd_code,
        arguments=['{input}'],
        nodes={'input': input_file},
        outputs=['results.npz'],
    )

wg.tasks.ShellJob.add_error_handler({
    'halve_dt': {
        'executor': halve_dt,
        'exit_codes': [ShellJob.exit_codes.ERROR_OUTPUT_FILEPATHS_MISSING.status],
        'max_retries': 3,
    }
})
```

The graph itself shows the wiring: a single `ShellJob<gsrd@localhost>` task with the failing input file pre-bound. The handler is a piece of metadata attached to that task, not a node in the graph; you can see its presence via `tasks.ShellJob.error_handlers`.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg
```

Now run it:

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg.run()
```

```{code-cell} ipython3
print(f'Final state : {wg.state}')
print(f'Exit status : {wg.tasks.ShellJob.process.exit_status}')
```

The ShellJob now succeeds, on its second attempt, with the handler-corrected `dt`.
The provenance records both attempts: the first as a failed `ShellJob` with the original input file, the second as a `ShellJob` whose input file has `dt = 5.0`.

:::{dropdown} When to write an error handler, and when not to
:icon: info

Handlers are the right tool for **transient or recoverable** failures: walltime exhausted (restart with more time), out-of-memory (rerun on a fatter queue), a numerical scheme drifted out of its stability window (tighten the step).
They are the *wrong* tool for hard programmer errors (a malformed input that no parameter sweep will rescue): those should fail loudly so you fix the cause, not the symptom.

A useful rule of thumb: if the same handler would also be the correct response *had a human noticed the failure on the cluster at 3am*, then automating it is a win. If the handler would silently paper over a real bug, don't write it.
:::

:::{dropdown} WorkChain-style handlers via `@process_handler`
:icon: info

The same pattern existed in aiida-core long before WorkGraph, via the {class}`~aiida.engine.processes.workchains.restart.BaseRestartWorkChain` and the `@process_handler` decorator.
You will see it in production plugins (`aiida-quantumespresso`'s `PwBaseWorkChain`, `aiida-cp2k`'s `Cp2kBaseWorkChain`, ...) where one "Base" WorkChain wraps the CalcJob plus a stack of handlers for every common failure.
See {ref}`how-to:restart-workchain` for the canonical recipe.
:::

### Further reading

- Exit codes and the process state machine: {ref}`topics:processes:concepts:exit_codes`, {ref}`topics:processes:concepts:state`.
- WorkChain restart pattern and `@process_handler`: {ref}`how-to:restart-workchain`.
- The aiida-workgraph error-handler how-to (full API, parametrised handlers): [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io).

## Beyond aiida-shell: writing a CalcJob plugin

`aiida-shell` is the right tool for prototyping and for one-off codes: it has *zero* boilerplate, you point it at a binary and you're running through AiiDA.
The cost is that every invocation has to re-discover the command's interface: arguments, expected output filenames, parser hooks.
For a code you call once a day, that is fine; for a code you (or your group) will run thousands of times, you want the interface captured *once*, in code, and shipped as a pip-installable plugin.

That's what a {ref}`CalcJob plugin <topics:calculations:usage:calcjobs>` is.

A `CalcJob` subclass declares:

- **Typed inputs** through `spec.input(...)`, with valid types and helpful descriptions.
- **The recipe** for preparing the working directory (`prepare_for_submission`).
- **The expected outputs** through `spec.output(...)`.
- **A parser** (a separate `Parser` subclass) that turns retrieved files into AiiDA data nodes.
- **Domain-meaningful exit codes** through `spec.exit_code(...)` (the same mechanism the error-handler section just hooked into).

A sketch for `gsrd` would look like this (just so you can see the shape; the full how-to lives at {ref}`how-to:plugin-codes`):

```python
from aiida import orm
from aiida.common import datastructures
from aiida.engine import CalcJob


class GsrdCalculation(CalcJob):
    """A CalcJob for the `gsrd` Gray-Scott solver."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('parameters', valid_type=orm.Dict, help='Gray-Scott parameters.')
        spec.output('results_npz', valid_type=orm.SinglefileData, help='Final U/V fields.')
        spec.output('variance_V', valid_type=orm.Float)
        spec.output('mean_V', valid_type=orm.Float)
        spec.exit_code(400, 'ERROR_UNSTABLE', 'Integration left the stable manifold.')
        spec.exit_code(401, 'ERROR_TRIVIAL_STATE', 'V field decayed without forming a pattern.')

    def prepare_for_submission(self, folder):
        import yaml
        with folder.open('input.yaml', 'w') as fh:
            yaml.safe_dump(self.inputs.parameters.get_dict(), fh)
        codeinfo = datastructures.CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.cmdline_params = ['input.yaml']
        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.retrieve_list = ['results.npz', 'stdout', 'stderr']
        return calcinfo
```

The matching `Parser` reads `results.npz` and stdout, fishes out `variance_V` / `mean_V`, and returns one of the declared exit codes on failure. The whole plugin is then registered through an entry point in `pyproject.toml`:

```toml
[project.entry-points."aiida.calculations"]
"mygroup.gsrd" = "mygroup.calculations.gsrd:GsrdCalculation"
```

After `pip install`, the new plugin is discoverable to AiiDA: anyone can `load_node`, query, share archives produced by it, and write WorkChains/WorkGraphs that use it, just as you used `aiida_shell.ShellJob` throughout this tutorial.
The {ref}`how-to:plugin-codes` guide walks you through this step by step, including the parser, the entry-point wiring, and how to lay out the package.
For the project skeleton itself, the [AiiDA plugin cutter](https://github.com/aiidateam/aiida-plugin-cutter) is a Cookiecutter template that gives you a working starting point.

:::{dropdown} How to choose: `aiida-shell` vs a CalcJob plugin
:icon: info

- **Prototyping**, scripts you'll run a handful of times, codes you've never used before &rarr; `aiida-shell`.
- A code your group runs **routinely**, with a stable input/output convention you want to encode once &rarr; CalcJob plugin.
- A code you want to **distribute** so others can `pip install` your interface and reuse your parser &rarr; CalcJob plugin.
- A code where the **same failure modes recur** and you want them surfaced as named exit codes for handlers to hook into &rarr; CalcJob plugin.

The two are not mutually exclusive: many groups prototype with `aiida-shell`, then promote the wrapper to a CalcJob plugin once the interface is stable.
:::

## A note on WorkChain

{ref}`Module 3 <tutorial:module3>` and {ref}`Module 6 <tutorial:module6>` used **WorkGraph** as the workflow framework.
A lot of the production AiiDA plugin ecosystem (`aiida-quantumespresso`, `aiida-cp2k`, `aiida-siesta`, ...) is built on the older **WorkChain** framework instead.
The two coexist; you will meet them both, so it is worth knowing what's different.

WorkChain is *imperative*: you write a sequence of steps (an `outline`), each step submits child processes, and state passes between steps through `self.ctx`. Here is the [`MultiplyAddWorkChain`](https://github.com/aiidateam/aiida-core/blob/main/src/aiida/workflows/arithmetic/multiply_add.py) bundled with aiida-core, for comparison:

```{literalinclude} ../../../src/aiida/workflows/arithmetic/multiply_add.py
:language: python
:lines: 12-62
```

The same workflow written as a WorkGraph would be a short `@task.graph()` body wiring three calls together, structurally closer to what you wrote in Module 3.

Both produce the same provenance (a `WorkChainNode` / `WorkGraphNode` with the same kind of called/return links), accept the same `engine.run` / `engine.submit` API, and integrate with the same `verdi process` commands. The difference is purely in *authoring style*:

| | WorkGraph (`@task.graph()`) | WorkChain (`outline`) |
|---|---|---|
| **Mental model** | Declarative; wire sockets between tasks. | Imperative; describe steps in order. |
| **State between steps** | Sockets and `wg.ctx`. | `self.ctx` and explicit returns. |
| **Dynamic graphs** | `If`, `While`, `Map`, dynamic construction. | Conditionals/loops via outline helpers (`if_`, `while_`, `return_`). |
| **Today's plugin ecosystem** | Newer, smaller, growing fast. | Mature; most domain plugins ship WorkChains. |
| **Use it when** | Composing/customising workflows as a user; exploring dynamic shapes. | Distributing a workflow as a plugin to a domain community. |

If you are *using* an existing plugin, you'll likely interact with its WorkChains.
If you are *writing* your own workflow, WorkGraph is the path this tutorial has been taking, and it is the one most active AiiDA development is pointed at.
The full WorkChain reference is at {ref}`topics:workflows:concepts:workchains`, with usage examples at {ref}`topics:workflows:usage:workchains`.

## Caching: never re-run the same calculation twice

Caching is one of AiiDA's most useful and most overlooked features.
The idea is direct: AiiDA hashes each `CalcJob`'s inputs after a well-defined normalisation; if you re-run the same `CalcJob` on the same inputs, AiiDA *re-uses* the existing result instead of submitting the calculation again.

Re-using means *cloning the result nodes from the cached run into a new process node*, so the provenance still records that you "ran" the calculation a second time, with a link back to the cache source. The downstream provenance graph stays correct; the simulator was just never actually executed.

We can demonstrate this on a single `gsrd` call. The `enable_caching` context manager turns caching on locally for this Python interpreter:

```{code-cell} ipython3
import time

from aiida.manage.caching import enable_caching

valid_params = {**BASE_PARAMS}
valid_input = orm.SinglefileData(
    io.BytesIO(yaml.dump(valid_params).encode()),
    filename='input.yaml',
)

# First run: actually executes gsrd.
t0 = time.perf_counter()
_, node_first = launch_shell_job(
    gsrd_code,
    arguments='{input}',
    nodes={'input': valid_input},
    outputs=['results.npz'],
)
t_first = time.perf_counter() - t0

# Second run with caching enabled and identical inputs: should be cached.
t0 = time.perf_counter()
with enable_caching():
    _, node_cached = launch_shell_job(
        gsrd_code,
        arguments='{input}',
        nodes={'input': valid_input},
        outputs=['results.npz'],
    )
t_cached = time.perf_counter() - t0

print(f'first run  : {t_first * 1e3:7.1f} ms  (exit={node_first.exit_status})')
print(f'cached run : {t_cached * 1e3:7.1f} ms  (exit={node_cached.exit_status})')
print(f'speedup    : ~{t_first / max(t_cached, 1e-6):.0f}x')
print(f'cache source: {node_cached.base.caching.get_cache_source()}')
print(f'  matches first run UUID: {node_cached.base.caching.get_cache_source() == node_first.uuid}')
```

The second run completes in milliseconds because no subprocess actually ran. `node.base.caching.get_cache_source()` returns the UUID of the original process, and `verdi process list` exposes the same information as a `cached_from` column:

```{code-cell} ipython3
%verdi process list -a -P pk process_label exit_status cached_from -L 'ShellJob<gsrd@localhost>'
```

The `ShellJob<gsrd@localhost>` rows include both runs; the second one carries the PK of the first in the `cached_from` column.

Caching also composes with everything WorkGraph builds on top. Re-running a sweep with identical inputs is essentially free:

:::{dropdown} `gray_scott_pipeline` (from Module 3a, in `include/workflows.py`)
```{literalinclude} include/workflows.py
:language: python
:pyobject: gray_scott_pipeline
```
:::

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show cached sweep'
:    code_prompt_hide: 'Hide cached sweep'

from typing import Annotated

from aiida_workgraph import Map, dynamic, task

from include.workflows import gray_scott_pipeline

# Feed-rate values to scan (same as Module 2).
F_VALUES = [0.038, 0.040, 0.042, 0.044, 0.046, 0.050, 0.055, 0.060]


@task.graph()
def gray_scott_sweep(param_sweep: Annotated[dict, dynamic(dict)], command):
    with Map(param_sweep) as m:
        run = gray_scott_pipeline(parameters=m.item.value, command=command)
        m.gather({'variance_V': run.variance_V})


param_sweep = {
    f'F_{f:.3f}'.replace('.', '_'): {**BASE_PARAMS, 'F': f} for f in F_VALUES
}

# First sweep: every iteration actually runs gsrd.
t0 = time.perf_counter()
wg_first = gray_scott_sweep.build(param_sweep=param_sweep, command=gsrd_code)
wg_first.run()
t_sweep_first = time.perf_counter() - t0

# Second sweep with caching: every iteration is cached.
t0 = time.perf_counter()
with enable_caching():
    wg_cached = gray_scott_sweep.build(param_sweep=param_sweep, command=gsrd_code)
    wg_cached.run()
t_sweep_cached = time.perf_counter() - t0
```

```{code-cell} ipython3
print(f'fresh sweep   : {t_sweep_first:6.2f} s')
print(f'cached sweep  : {t_sweep_cached:6.2f} s  ({t_sweep_first / max(t_sweep_cached, 1e-6):.0f}x faster)')
```

For a small tutorial sweep the absolute numbers look modest; on a real ab-initio workflow where each calculation is minutes-to-hours, the same mechanism turns "re-running last week's analysis" from days into seconds.

:::{important} Local vs daemon caching
The `enable_caching` context manager only affects the **current Python interpreter**.
If you submit to the daemon (e.g. `wg.submit()`), caching is governed by the profile configuration instead:

```bash
verdi config set caching.default_enabled True --scope <profile>
```

Once set, every daemon-launched CalcJob respects caching without you having to wrap calls in `enable_caching`. See {ref}`topics:provenance:caching:control-caching` for per-plugin control and identifier patterns.
:::

:::{dropdown} Caveats: what gets cached
:icon: info

Caching depends on the plugin author marking input types as hashable and on the `CalcJob` declaring which inputs are cache-relevant.
The core data types and `aiida-shell` get this right out of the box; third-party plugins occasionally get it wrong, which manifests as "I ran the same thing twice and the cache didn't hit".
{ref}`topics:provenance:caching:control-hashing` is the page to read when that happens. It covers `_aiida_hash`, `_hash_ignored_inputs`, and how to invalidate stale hashes.
:::

### Further reading

- The caching concept and how hashes are computed: {ref}`topics:provenance:caching`.
- Per-plugin and per-identifier caching controls: {ref}`topics:provenance:caching:control-caching`.
- Tuning for many-cached workloads: {ref}`how-to:tune-performance:caching`.

## The plugin ecosystem

aiida-core deliberately ships a small surface area; almost everything beyond running calculations and querying provenance lives in plugins.
A few that are worth knowing about by name:

::::{grid} 2 2 2 2
:gutter: 3

:::{grid-item-card} {fa}`folder-tree;mr-1` aiida-project
:text-align: center
:shadow: md

Project-scoped AiiDA environments: one Python venv plus profile per investigation, switchable with a single command. Solves the "ten ongoing studies, ten conflicting dependencies" problem.

+++

```{button-link} https://github.com/aiidateam/aiida-project
:color: primary
:outline:

Go to GitHub
```
:::

:::{grid-item-card} {fa}`layer-group;mr-1` aiida-hyperqueue
:text-align: center
:shadow: md

[HyperQueue](https://it4innovations.github.io/hyperqueue/) metascheduler integration. Pack thousands of short jobs into a single SLURM allocation without re-queueing each one. Cross-referenced in {ref}`how-to:tune-performance`.

+++

```{button-link} https://aiida-hyperqueue.readthedocs.io
:color: primary
:outline:

Read the docs
```
:::

:::{grid-item-card} {fa}`diagram-project;mr-1` aiida-workgraph
:text-align: center
:shadow: md

The workflow framework you've been using since {ref}`Module 3 <tutorial:module3>`. Maintained separately from aiida-core so it can iterate faster on workflow ergonomics.

+++

```{button-link} https://aiida-workgraph.readthedocs.io
:color: primary
:outline:

Read the docs
```
:::

:::{grid-item-card} {fa}`terminal;mr-1` aiida-shell
:text-align: center
:shadow: md

The "wrap any executable, no plugin code required" path you have been using since {ref}`Module 1 <tutorial:module1>`. The fastest way to bring a new code into AiiDA; promote it to a CalcJob plugin once the interface stabilises.

+++

```{button-link} https://aiida-shell.readthedocs.io
:color: primary
:outline:

Read the docs
```
:::

:::{grid-item-card} {fa}`list-check;mr-1` aiida-submission-controller
:text-align: center
:shadow: md

Helper classes for orchestrating very large submission queues, e.g. "run this WorkChain over 100,000 input structures, throttled to N concurrent jobs". The standard partner for high-throughput screening.

+++

```{button-link} https://github.com/aiidateam/aiida-submission-controller
:color: primary
:outline:

Go to GitHub
```
:::

:::{grid-item-card} {fa}`server;mr-1` aiida-code-registry
:text-align: center
:shadow: md

Pre-built `Computer` and `Code` definitions for common HPC machines (CSCS, MARVEL, ...). Drop into a fresh profile to skip the manual `verdi computer setup` ritual. Referenced in {ref}`Module 4 <tutorial:module4>`.

+++

```{button-link} https://github.com/aiidateam/aiida-code-registry
:color: primary
:outline:

Go to GitHub
```
:::

:::{grid-item-card} {fa}`window-restore;mr-1` AiiDAlab
:text-align: center
:shadow: md

Jupyter-based front-end on top of AiiDA. Hosts the [Quantum ESPRESSO app](https://aiidalab-qe.readthedocs.io) and friends: turnkey GUIs for full simulation protocols, talking to your local AiiDA profile.

+++

```{button-link} https://aiidalab.net
:color: primary
:outline:

Visit AiiDAlab
```
:::

:::{grid-item-card} {fa}`puzzle-piece;mr-1` Domain plugins
:text-align: center
:shadow: md

`aiida-quantumespresso`, `aiida-cp2k`, `aiida-siesta`, `aiida-vasp`, `aiida-pseudo`, ... Each wraps a production code with full CalcJob plugins, parsers, and WorkChains. The {ref}`reference:core_plugins` page lists the non-domain-specific ones, and the full catalogue is at the plugin registry.

+++

```{button-link} https://aiidateam.github.io/aiida-registry/
:color: primary
:outline:

Plugin registry
```
:::
::::

:::{dropdown} Further reading on the plugin ecosystem
:icon: info

The AiiDA team also maintains a curated index of non-domain-specific plugins on the docs ({ref}`reference:core_plugins`) and a [blog post](https://aiida.net/blog/2024-12-13-core-plugins/) walking through several of them with motivation and short examples.
The plugin registry above is the authoritative catalogue.
:::

## Where to go next

You have, in seven modules, gone from running a single tracked calculation to building adaptive, error-resilient, cached workflows that you could in principle ship as a plugin.
Some natural next steps:

- **Write a CalcJob plugin** for a code you already use. The {ref}`how-to:plugin-codes` guide and the [aiida-plugin-cutter](https://github.com/aiidateam/aiida-plugin-cutter) template will get a skeleton working in an afternoon.
- **Write a parser** for an existing CalcJob plugin that does not have one for the output you care about. Drop-in parsers are a great low-friction way to contribute back.
- **Try one of the domain plugins** on a real problem from your work. `aiida-quantumespresso`'s `PwBaseWorkChain` is a good starting point if your domain is electronic structure; the [aiida-qe-demo](https://github.com/aiidateam/aiida-qe-demo) walks through a full Quantum ESPRESSO example end to end.
- **Browse the plugin registry** for adjacent tools (workflow controllers, queue managers, GUI front-ends) before you write something yourself. The answer is often "someone already did this".
- **Connect with the community.** Questions, ideas, and feedback go on the [AiiDA Discourse](https://aiida.discourse.group). Bug reports and feature requests go on the relevant GitHub repository.
- **Contribute back.** AiiDA is community-maintained. Improvements to docs, tutorials, plugins, and the core engine itself all start from the same place: the [CONTRIBUTING.md guide](https://github.com/aiidateam/aiida-core/blob/main/CONTRIBUTING.md) in the aiida-core repository.

The provenance graph you built over Modules 1&ndash;6 is yours to keep: it remains queryable indefinitely, archivable into a `.aiida` file at any time ({ref}`how-to:share`), and re-usable as the starting point for tomorrow's analysis.
The pieces this module sketched are the ways that graph grows beyond a tutorial.
