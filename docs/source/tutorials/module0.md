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

{bdg-secondary}`⏱️ ~45 min read` {bdg-success}`Beginner`

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module0.ipynb` {octicon}`download`
:::

In this module, we run a simulation the traditional way, without AiiDA, to experience the pain points it is built to solve.

Throughout this tutorial we use a **reaction-diffusion simulation**, the classic Gray-Scott model, as our running example.
It models the concentration of particles diffusing and reacting on a 2D grid, producing a variety of spatial patterns.
Depending on the feed rate, F, and kill rate, k, it forms strikingly different structures:

:::{dropdown} A gallery of Gray-Scott patterns
```{image} https://raw.githubusercontent.com/aiidateam/gsrd/2b43234ba82c796fd082278f7b0f874c35829d89/gallery/showcase.png
:width: 100%
:align: center
```
:::

&nbsp;

The concrete code we will be wrapping is [`gsrd`](https://github.com/aiidateam/gsrd), a small command-line simulator deliberately written to *mirror the conventions and quirks of real-world scientific codes*: a single positional argument, no `--help` to guide you, hardcoded output filenames, scalar results scattered across stdout, citation banners, and unreliable exit codes.
None of this is essential to a Gray-Scott solver, but all of it can show up in scientific software that has grown over the years around the science rather than the interface, which is exactly the situation a scientific workflow manager needs to handle gracefully.

:::{dropdown} More about the model

`gsrd` implements a reaction-diffusion system known as the Gray-Scott model.
Two concentrations, U and V, evolve on a 2D grid.
U is continuously fed into the system and both substances decay, while V catalyzes its own production from U in a positive feedback loop.
The interplay of these processes, controlled primarily by the feed rate F and kill rate k, determines what patterns form.
Identical starting conditions (same initial grid) can produce wildly different patterns just by tweaking F and k.
:::

## Setup

This first module uses only the `gsrd` simulator, no AiiDA yet. We recommend [`uv`](https://docs.astral.sh/uv/), but plain `pip` works just as well:

```bash
uv pip install git+https://github.com/aiidateam/gsrd.git

# or, without uv:

pip install git+https://github.com/aiidateam/gsrd.git
```

Now, there are three ways to work through this tutorial, and which of its files you need to fetch, if any, depends on which you follow:

- **Reading on the web**: what you are doing right now. The code and its output are already rendered on this page, so there is nothing to install, download, or run; just read on.
- **The downloaded notebook**: the fetch is already included, so just run the cells in order, as you would any notebook.
- **Your own notebook** (copy-pasting cells from this page): run the cell below once to fetch `input.yaml` and the other helper files the tutorial uses.

```{code-cell} ipython3
:tags: [hide-cell]
:mystnb:
:    code_prompt_show: 'Show the fetch cell (local-notebook users)'
:    code_prompt_hide: 'Hide the fetch cell'

# Fetch the tutorial's include/ helpers if they are not already present.
from pathlib import Path

if not (Path('include') / 'input.yaml').exists():
    import json
    import urllib.request

    api = 'https://api.github.com/repos/GeigerJ2/aiida-core/contents/docs/source/tutorials/include?ref=docs/integrate-tutorials'
    Path('include').mkdir(exist_ok=True)
    for entry in json.load(urllib.request.urlopen(api)):
        if entry['type'] == 'file':
            urllib.request.urlretrieve(entry['download_url'], Path('include') / entry['name'])
```

## Running the simulation

We invoke `gsrd` from the command line, passing the parameters via an `input.yaml` file:

:::{dropdown} `input.yaml`&nbsp;contents

```yaml
F: 0.04          # feed rate
k: 0.060         # kill rate
du: 0.16         # diffusion coefficient of U
dv: 0.08         # diffusion coefficient of V
dt: 1.0          # time step
grid_size: 128   # grid is grid_size x grid_size
n_steps: 10000   # number of integration steps
seed: 42         # RNG seed for the initial perturbation
```
:::

Now run `gsrd` with the input file:

```{code-cell} ipython3
:tags: ["hide-output"]

# gsrd reads the input file and writes its results into the current directory.
# Expand the output to see what it prints.
!gsrd include/input.yaml
```

:::{note}
As we run in a Jupyter notebook here, we prepend the shell command with `!` to execute it from within the notebook. When running directly in a terminal, drop the `!`.
:::

Expand the output above. The run's two key results, **variance(V)** (how sharply contrasted the final pattern is across the grid) and **mean(V)** (the average V concentration), are printed in a diagnostics box at the very end. That box is surrounded by much more, though: a banner, a citation block, and per-iteration progress, all on stdout.

Now, let's see what `gsrd` wrote to disk. Besides most of the output being on stdout, it also produced `results.npz` in the current directory, a binary NumPy archive. Let's load it and list what it holds:

```{code-cell} ipython3
import numpy as np

data = np.load('results.npz')
print('U_final:', data['U_final'].shape)
print('V_final:', data['V_final'].shape)
print('params: ', repr(data['params'].item()))
```

The run was successful, but a closer look reveals three problems:

**Key numbers live only in the log.** The two summary diagnostics, `variance(V)` and `mean(V)`, are nowhere in `results.npz`; they appear only in the stdout block you expanded above. If you forgot to redirect stdout to a file, you have to re-run the simulation just to recover them.

**The saved inputs are an opaque blob.** The `params` entry *does* record the inputs, but as a single JSON string with no schema, not a structured record you can query.
Pulling anything out of it means parsing the JSON back into a dict yourself, and there is no guarantee that the next code you wrap will follow the same convention (or any convention at all).

**The output filename is fixed.** `results.npz` is written to a fixed name in the current directory: run `gsrd` again there and it silently overwrites the previous results.
Some codes go further and implicitly *read* leftover files from the working directory to "restart", so the very same command can produce different results depending on what happens to be lying around.

## Running again

All of this compounds further the moment you run more simulations. So let's do exactly that and try a different set of input parameters.
The natural thing to do is to make a copy of the input, open it in a text editor, and change `F` from `0.04` to `0.050`.
```{code-cell} ipython3
# Change the feed rate F from 0.04 to 0.050, saved as our own editable input
# (in practice you might open input.yaml in a text editor).
!sed 's/F: 0.04/F: 0.050/' include/input.yaml > input.yaml
```

Then run the simulation with the modified input file:

```{code-cell} ipython3
:tags: ["hide-output"]

!gsrd input.yaml
```

With `F=0.050`, the pattern looks completely different:

```{image} https://raw.githubusercontent.com/aiidateam/gsrd/2b43234ba82c796fd082278f7b0f874c35829d89/gallery/dissolved.png
:width: 60%
:align: center
```

&nbsp;

Tweaking a parameter and re-running like this is how the exploratory phase of a scientific project often looks, and done casually it can quietly cost you in three ways:

**The previous output is gone.** The re-run reused the fixed `results.npz` filename, silently overwriting the first run's results.

**Editing in place erases the original input.** We changed `F` in `input.yaml` and overwrote it, so the first run's parameters are gone, with nothing on disk recording that it happened.

**Typos fail silently.** Editing inputs by hand is convenient, but many scientific codes (`gsrd` included) ignore keys they don't recognize, so a mistyped parameter name runs cleanly using the default value instead of raising an error.

## Running into errors

Now, let's see what happens when things actually go wrong with our simulation.
We run it with an oversized timestep (`dt=100`), from a prepared `input_bad.yaml`:

:::{dropdown} `input_bad.yaml`&nbsp;contents

```yaml
F: 0.04          # feed rate
k: 0.060         # kill rate
du: 0.16         # diffusion coefficient of U
dv: 0.08         # diffusion coefficient of V
dt: 100.0        # time step (oversized, makes the integration blow up)
grid_size: 128   # grid is grid_size x grid_size
n_steps: 10000   # number of integration steps
seed: 42         # RNG seed for the initial perturbation
```
:::

```{code-cell} ipython3
# Run an input with an oversized timestep (dt=100), which makes the
# integration blow up. We use subprocess (rather than the shell `!`) so we
# can capture the exit code, which is the telling part below.
import subprocess

result = subprocess.run(
    ['gsrd', 'include/input_bad.yaml'],
    capture_output=True,
    text=True,
)
print('Exit code:', result.returncode)
print(result.stderr)
```

Three things are simultaneously wrong with that failure mode:

**The exit code lies.** It is `0`, so as far as your shell or any orchestration script is concerned, the run succeeded.

**The only failure signal is buried in the log.** A terse `ERR:` line on stderr (here preceded by a numpy `RuntimeWarning` about the overflow that caused it) and the *absence* of `*** JOB DONE ***` on stdout, easy to miss in a longer output log.

**No output file was written.** Combined with the zero exit code, a downstream script will happily try to open a non-existent `results.npz`, or worse, pick up a stale one from a previous run.

And, lastly, from the error, you are not being told what to fix or how to recover.

:::{admonition} The friction, all in one place
:class: warning

Pulled together, the raw command-line workflow leaves you fighting:

- **No single source of truth for a run**: results are split across different channels (stdout, output files, log files, etc.).
- **Silently overwritten results**: a fixed output filename means each run clobbers the last, with nothing recording which inputs produced which output.
- **Inputs you can't query or trust**: parameters are saved as an unstructured blob with no schema, and editing in place loses the original values.
- **Failures that pass silently**: a failed run can still exit `0`, so downstream automation carries on as if nothing went wrong.
:::

We deliberately baked these shortcomings into `gsrd`, but if you've spent any time in the field, chances are you've hit one or more of them in your actual work.

## How this becomes even worse at real-world scale

Now, while these issues are mildly annoying at a few runs, they turn into real problems once you scale up.

Also, at larger scale, more complications can start appearing:

- **Even more scattered data**: input and output files might end up on scratch filesystems across different clusters, your local machine, and shared drives. Months later, just tracking down which directory holds the converged results becomes a chore in itself.
- **Failures in multi-step workflows**: one step prepares the inputs, another runs the simulation, a third post-processes the results. If step 2 fails for 15 out of 100 runs, how do you figure out which ones failed, why, and how to re-run just those? You'd have to manually identify the failures, fix or adjust the inputs, and re-run each.
- **Heterogeneous output formats**: each code has its own conventions. Some write structured output (e.g., XML or HDF5) that is easy to parse, others (`gsrd` included) scatter key numbers across plain-text logs with no defined schema. Extracting results programmatically across many such codes often means writing and maintaining fragile custom parsers that break with new code versions.
- **Code versions and environments**: was this result produced with v2.1 or v2.3? Compiled with which flags? On which cluster? You'd easily lose track unless you logged it yourself.
- **Post-processing at scale**: aggregating a single number from each of hundreds of output files requires custom scripts that might break when the output format changes.
- **Collaboration and handover**: a colleague takes over your project. They inherit a directory tree of thousands of files with no documentation of what produced what. You could write a README, but keeping it up to date is yet another manual task that rarely happens in practice.

Unlike the pitfalls from the single runs above, these are not really shortcomings of any individual code but are instead inherent to any large computational project.
To handle such a workload, you'd need a naming convention, a spreadsheet, and custom scripts to execute and keep track of your simulations.
Those approaches are fragile, and the resulting data (and the workflow that produced it) is hard to pass on to a colleague.

## How AiiDA solves these problems

This is where AiiDA comes in, built to remove exactly this friction.
Every calculation you run through AiiDA is recorded automatically in a **provenance graph**, including its inputs, outputs, relevant metadata, and the links between them.
And the same machinery that runs one simulation can help you run thousands: AiiDA was created for high-throughput workloads from the start.
In practice, that means:

- **Provenance tracking**: every result can be traced back to the exact inputs, code, and machine that produced it. No overwriting, no orphaned files, no need to keep input files around by hand.
- **Workflow orchestration**: multi-step pipelines run as managed workflows, handling execution, file transfer, data passing, and error recovery. If some steps fail, AiiDA knows which ones, why, and can help you restart just those. And because every run is recorded, identical calculations can be served from a cache instead of being recomputed.
- **Plugins and community knowledge**: AiiDA plugins for popular codes ship with workflows, parsers, and error handlers, encoding years of domain expertise. You benefit from best practices without having to painfully discover them yourself.
- **Reliable failure detection**: parsers shipped with AiiDA plugins look for the markers that actually indicate success or failure, so a run with a spurious zero exit code still gets flagged as failed and the downstream workflow does not blindly carry on.
- **Structured output parsing**: AiiDA plugins provide parsers that extract structured results from a code's output channels, storing them as SQL database entries with a well-defined schema.
- **Querying**: because every calculation and its results live in a database, you can search and filter across all of them without ever manually opening a single output file.
- **Reproducibility and sharing**: the full provenance graph can be exported as a portable archive. A collaborator can easily reproduce, audit, or extend your work.

:::{important}
The promise is not just "more throughput".
It is that the **scaffolding around your simulations** (bookkeeping, parsing, data transfer, retries) **stops being your problem**, so the time you'd otherwise spend fighting tooling goes back to doing science.
:::

Buckle up: in {ref}`Module 1 <tutorial:module1>`, we'll run the same `gsrd` simulation through AiiDA and start seeing the benefits in action.

## Further reading

- The `gsrd` package and the conventions it deliberately mimics: <https://github.com/aiidateam/gsrd>
- AiiDA's provenance model: {ref}`topics:provenance`
