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

(tutorial:module0)=
(tutorial:intro)=
# Module 0: Calculations without AiiDA

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module0.ipynb` {octicon}`download`
:::

In this module, we run a simulation the traditional way, without AiiDA, to experience the pain points it is built to solve.

Throughout this tutorial we use a **reaction-diffusion simulation** as our running example.
It models the concentration of particles diffusing and reacting on a 2D grid, producing a variety of spatial patterns depending on its parameters.
A typical pattern formed can look like this:

```{image} include/reaction-diffusion-fields.png
:width: 60%
:align: center
```

&nbsp;

:::{dropdown} More about the model

The simulation implements a reaction-diffusion system known as the Gray-Scott model.
Two concentrations, U and V, evolve on a 2D grid.
U is continuously fed into the system and both substances decay, while V catalyzes its own production from U in a positive feedback loop.
The interplay of these processes, controlled primarily by the feed rate F and kill rate k, determines what patterns form.
Identical starting conditions (same initial grid) can produce wildly different patterns just by tweaking F and k.
:::

The concrete code we will be wrapping is [`gsrd`](https://github.com/aiidateam/gsrd), a small command-line simulator deliberately written to *emulate the conventions and quirks of real-world scientific codes*: a single positional argument, hardcoded output filenames, scalar results scattered across stdout, citation banners, and unreliable exit codes.
None of this is necessary for a Gray-Scott solver, but all of it is depressingly common in established scientific software, which is exactly the situation a workflow manager has to deal with.

## Running the simulation

<!-- MOTIVATION: Show the typical experience of running a scientific code.
     Users should recognize the UX from their own work: a CLI tool with
     an input file that produces output, where critical results are scattered
     across stdout and the output file. -->

The simulation is invoked like a typical scientific code: a command-line executable that reads an input file and writes its output to the current directory.

```{code-cell} ipython3
:tags: ["remove-cell"]

import tempfile
from pathlib import Path

work_dir = Path(tempfile.mkdtemp(prefix='aiida_tutorial_m0_'))
input_src = Path('include/input.yaml').resolve()
input_bad_src = Path('include/input_bad.yaml').resolve()
import shutil
shutil.copy(input_src, work_dir / 'input.yaml')
```

```console
$ gsrd input.yaml
```

```{code-cell} ipython3
:tags: ["remove-input"]

# Actually run the simulation in a clean working directory (hidden from
# rendered output, since the real banner+progress block is too noisy).
import subprocess
result = subprocess.run(
    ['gsrd', 'input.yaml'],
    cwd=work_dir,
    capture_output=True, text=True,
)
print(result.stdout)
if result.stderr:
    print('--- stderr ---')
    print(result.stderr)
print(f'Exit code: {result.returncode}')
```

That is a lot of output for what is essentially a 2D PDE solve.
Banner, fake citation block, per-iteration progress, a diagnostics box at the end, all interleaved on stdout.
This is a deliberately tame rendition; many production scientific codes are an order of magnitude noisier.

Let's see what `gsrd` actually wrote to disk:

```{code-cell} ipython3
:tags: ["remove-input"]

print('Files in working directory:')
for p in sorted(work_dir.iterdir()):
    print(f'  {p.name}')
```

The simulation produced `results.npz`.
But look more carefully: the two scalar diagnostics, **variance(V)** and **mean(V)**, only appear in the *Diagnostics* block on stdout.
They are *not* in `results.npz`:

```{code-cell} ipython3
:tags: ["remove-input"]

import numpy as np
with np.load(work_dir / 'results.npz') as data:
    print('results.npz contents:')
    for key in data.files:
        arr = data[key]
        kind = f'array shape={arr.shape}' if arr.ndim else f'scalar ({arr.dtype})'
        print(f'  {key:<10}  {kind}')
```

So the headline numbers of the run are only in the log.
If you forgot to redirect stdout to a file, you have to re-run the simulation to recover them.
And `results.npz` is a fixed filename in the current directory: run `gsrd` again in the same directory and it silently overwrites the previous results.

:::{admonition} Results scattered across stdout and the output file
:class: warning

- The arrays go to a binary file (`results.npz`), but the headline scalars (`variance(V)`, `mean(V)`) only appear on stdout
- The output filename is hardcoded, so two runs in the same directory overwrite each other
- The input parameters that produced these results are nowhere in the output file by default; you would have to keep the input YAML next to it yourself
:::

## Running again

<!-- MOTIVATION: Show how quickly you lose track of what produced what.
     The user edits the input file, runs again, and now the original
     input is gone. The output file doesn't help either. -->

What if we want to try a different feed rate?
Open `input.yaml` in a text editor and change `F` from `0.04` to `0.055`.

```{code-cell} ipython3
:tags: ["remove-cell"]

# Simulate editing the input file in place (the user would do this
# in a text editor). This overwrites the original parameters.
import yaml

input_path = work_dir / 'input.yaml'
with open(input_path) as f:
    params = yaml.safe_load(f)
params['F'] = 0.055
with open(input_path, 'w') as f:
    yaml.dump(params, f)
```

Then run the same command again:

```console
$ gsrd input.yaml
```

With `F=0.055`, the pattern looks completely different:

```{image} include/reaction-diffusion-fields-2.png
:width: 60%
:align: center
```

&nbsp;

However, note that we just overwrote our input file, *and* the `results.npz` of the first run, in one go.
The original parameters are gone, and so is the previous output. Nothing on disk now records that the first run ever happened.

Quickly tweaking parameters and re-running like this is exactly how the exploratory phase of a project tends to look in practice, which makes the pain points below easy to walk into.

:::{admonition} No systematic record of your work
:class: warning

- Editing the input file in place loses the original parameters
- The fixed output filename means the second run overwrites the first
- Without a systematic way to organize runs, results become untraceable and data may be lost
:::

## Running into errors

<!-- MOTIVATION: Show that errors from scientific codes are often cryptic
     and leave no useful trace. The user has no idea what went wrong, and
     no record that the run even happened. -->

What happens when things go wrong? Let's try a feed rate where V dies out before any pattern can form (`F=0.1`):

```console
$ gsrd input.yaml
```

```{code-cell} ipython3
:tags: ["remove-input"]

# Actually run with the bad input (show only its tail, plus stderr and
# the exit code, so the failure mode is visible without the banner noise).
result_bad = subprocess.run(
    ['gsrd', str(input_bad_src)],
    cwd=work_dir,
    capture_output=True, text=True,
)
stdout_tail = ''.join(result_bad.stdout.splitlines(keepends=True)[-4:])
print('... (banner and progress lines elided) ...')
print(stdout_tail, end='')
if result_bad.stderr:
    print('--- stderr ---')
    print(result_bad.stderr, end='')
print(f'Exit code: {result_bad.returncode}')
```

Three things are simultaneously wrong with that failure mode:

- The exit code is `0`. As far as your shell or any orchestration script is concerned, the run succeeded.
- The only signal that something failed is a single terse `ERR:` line on stderr (and the *absence* of `*** JOB DONE ***` on stdout). Both are easy to miss in a sea of progress output.
- `results.npz` was not written. Combined with the zero exit code, an automation script downstream will happily try to open a non-existent file, or worse, pick up a stale `results.npz` from a previous run.

In real scientific software this is typically much worse, with pages of unrelated output drowning out anything useful. But even the minimal version here doesn't tell you what to fix or how to recover.

:::{admonition} Failures are hard to diagnose and easy to lose
:class: warning

- Exit codes are not reliable: many scientific codes always return 0 and signal failure through log markers instead
- Failed runs may produce no output file at all, or, worse, a partial file that looks plausible
- Even when error messages exist, connecting them back to the right inputs and parameters is up to you
:::

## So, what's the problem?

<!-- MOTIVATION: The punchline of Module 0. Connect the concrete pain
     points above to what AiiDA solves, then paint the picture at scale
     to make the case compelling. -->

### What we already saw

We ran just a couple of simulations and already hit these problems:

- **Inputs disconnected from outputs**: there is no automatic link between what you ran and what you got, unless you track it yourself
- **Results scattered across files and logs**: arrays in a binary file, scalars on stdout, parameters in a separate YAML; reuniting them is your job
- **Original parameters lost**: we edited the input file in place, and the previous version is gone
- **Fixed output filename**: re-running in the same directory silently overwrites the previous results
- **Failures are hard to detect**: exit codes can be uninformative, error messages cryptic, and failed runs may leave no trace at all

### What scientific software tends to look like

The pain points above are not bugs in `gsrd`; they are a faithful caricature of the established scientific codes that workflow managers actually have to wrap.
A typical legacy simulation code in the wild has some mix of:

- A single positional argument and no `--help`, with the real interface buried in a PDF manual
- Critical scalar results printed only to stdout, mixed in with banners and progress lines, and parsed by everyone with a slightly different regex
- Output files with fixed names in the current directory
- Tolerant input parsers that silently accept misspelled or unsupported keys
- "Restart" mechanisms that pick up files from the working directory implicitly, so the same command can produce different results depending on what is already there
- Uninformative exit codes; success and failure both reported as `0`

These conventions reflect decades of HPC habits more than any deliberate API design, and they are precisely what makes scientific software hard to compose and automate. A workflow manager has to wrap them, hide them, and make the result usable.

### What happens at real-world scale

:::{note}
Now imagine doing this not for 2 runs, but for **100 different parameter combinations**.
You'd need a naming convention, a spreadsheet, and custom scripts to execute and keep track of your simulations.
Those approaches are fragile, and the resulting data (and the workflow that produced it) is hard to pass on to a colleague.
:::

Some more things that can go wrong at scale:

- **Scattered data**: input and output files can end up on scratch filesystems across different clusters, your local machine, and shared drives. Months later, just tracking down which directory holds the converged results becomes a chore in itself.
- **Multi-step workflows**: one code prepares the geometry, another runs the simulation, a third post-processes the results. If step 2 fails for 15 out of 100 runs, how do you figure out which ones failed, why, and how to re-run just those? You'd have to manually identify the failures, fix or adjust the inputs, and re-run each.
- **Unstructured output formats**: as we just saw, many codes write plain text logs with no defined schema, and the headline numbers come out of stdout. Extracting results programmatically often means writing fragile custom parsers that break with new code versions.
- **Code versions and environments**: was this result produced with v2.1 or v2.3? Compiled with which flags? On which cluster? You'd easily lose track unless you logged it yourself.
- **Post-processing at scale**: aggregating a single number from each of hundreds of output files requires custom scripts that might break when the output format changes.
- **Collaboration and handover**: a colleague takes over your project. They inherit a directory tree of thousands of files with no documentation of what produced what. You could write a README, but keeping it up to date is yet another manual task that rarely happens in practice.

## How AiiDA solves these problems

AiiDA is a workflow manager designed for exactly these problems.
At its core is the **provenance graph**: an automatic record of every calculation, its inputs, its outputs, and how they all connect, for every run, including failed ones.
It gives you:

- **Provenance tracking**: nothing is lost. Every result can be traced back to the exact inputs, code, and machine that produced it.
- **Workflow orchestration**: multi-step pipelines run as managed workflows, handling execution, data passing, and error recovery. If some steps fail, AiiDA knows which ones, why, and can help you restart just those.
- **Reproducibility and sharing**: the full provenance graph can be exported as a portable archive. A collaborator can easily reproduce, audit, or extend your work.
- **Structured output parsing**: AiiDA plugins provide parsers that extract structured results from a code's output files *and* its stdout, store them as queryable database entries, and let you search and filter across all your calculations without ever opening a single file.
- **Community knowledge**: AiiDA plugins for popular codes ship with workflows, parsers, and error handlers, encoding years of domain expertise. You benefit from best practices without having to painfully discover them yourself.

The promise is not just "more throughput". It is that the scaffolding around your simulations &mdash; bookkeeping, parsing, restart logic, retries &mdash; stops being your problem, so the time you'd otherwise spend fighting tooling goes back to doing science.

Buckle up: in {ref}`Module 1 <tutorial:module1>`, we'll run the same `gsrd` simulation through AiiDA and start seeing the benefits in action.

## Further reading

- The `gsrd` package and the conventions it deliberately mimics: <https://github.com/aiidateam/gsrd>
- AiiDA's provenance model: {ref}`topics:provenance:concepts`
