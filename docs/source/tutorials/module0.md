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

<!-- TODO: re-enable once the md->ipynb conversion script is verified
:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module0.ipynb` {octicon}`download`
:::
-->

In this module, we run a simulation the traditional way, without AiiDA, to experience the pain points it is built to solve.

Throughout this tutorial we use a **reaction-diffusion simulation** as our running example.
It models the concentration of particles diffusing and reacting on a 2D grid, producing a variety of spatial patterns depending on its parameters.
A typical pattern formed can look like this:

```{image} include/reaction-diffusion-fields.png
:width: 60%
:align: center
```

&nbsp;

The concrete code we will be wrapping is [`gsrd`](https://github.com/aiidateam/gsrd), a small command-line simulator deliberately written to *mirror the conventions and quirks of real-world scientific codes*: a single positional argument, no `--help` to guide you, hardcoded output filenames, scalar results scattered across stdout, citation banners, and unreliable exit codes.
None of this is essential to a Gray-Scott solver, but all of it is common in scientific software that has grown over the years around the science rather than the interface, which is exactly the situation a scientific workflow manager needs to handle gracefully.

:::{dropdown} More about the model

`gsrd` implements a reaction-diffusion system known as the Gray-Scott model.
Two concentrations, U and V, evolve on a 2D grid.
U is continuously fed into the system and both substances decay, while V catalyzes its own production from U in a positive feedback loop.
The interplay of these processes, controlled primarily by the feed rate F and kill rate k, determines what patterns form.
Identical starting conditions (same initial grid) can produce wildly different patterns just by tweaking F and k.
:::

:::{note} Setup
This first module uses only the `gsrd` simulator, no AiiDA yet.
Install it with:

```bash
pip install git+https://github.com/aiidateam/gsrd
```
:::

## Running the simulation

<!-- MOTIVATION: Show the typical experience of running a scientific code.
     Users should recognize the UX from their own work: a CLI tool with
     an input file that produces output, where critical results are scattered
     across stdout and the output file. -->

We invoke `gsrd` from the command line, passing the parameters via an `input.yaml` file:

:::{dropdown} `input.yaml`&nbsp;contents

```yaml
F: 0.04          # feed rate
k: 0.065         # kill rate
du: 0.16         # diffusion coefficient of U
dv: 0.08         # diffusion coefficient of V
dt: 1.0          # time step
grid_size: 64    # grid is grid_size x grid_size
n_steps: 3000    # number of integration steps
seed: 42         # RNG seed for the initial perturbation
```
:::

```{code-cell} ipython3
# In a Jupyter notebook, a line starting with `!` runs a shell command.
# Make a scratch directory to work in and copy the example input into it.
!mkdir -p tmp
!cp include/input.yaml tmp/input.yaml
```

Now run `gsrd` on that input:

```{code-cell} ipython3
:tags: ["hide-output"]

# gsrd reads input.yaml and writes its results into the directory it runs
# in. Expand the output to see what it prints.
!cd tmp && gsrd input.yaml
```

Expand the output above to see what `gsrd` prints during a run: a banner, a citation block, per-iteration progress, and a diagnostics box at the end, all on stdout.

Let's see what `gsrd` actually wrote to disk:

```{code-cell} ipython3
# List the files gsrd created.
!ls tmp
```

The simulation produced `results.npz`.
But look more carefully: the two summary diagnostics of the final V field only appear in the *Diagnostics* block on stdout.
These are **variance(V)**, which measures how sharply contrasted the pattern is across the grid, and **mean(V)**, the average V concentration.
They are *not* in `results.npz`:

```{code-cell} ipython3
# results.npz is a binary NumPy archive. Load it and list what it holds.
import numpy as np

data = np.load('tmp/results.npz')
for name in data.files:
    print(name, data[name].shape)
```

So the two summary numbers of the run are only in the log.
If you forgot to redirect stdout to a file, you have to re-run the simulation to recover them.
And `results.npz` is a fixed filename in the current directory: run `gsrd` again in the same directory and it silently overwrites the previous results.
Some codes go further and implicitly *read* leftover files from the working directory to "restart", so the very same command can produce different results depending on what happens to be lying around.

There is also a `params` entry, however, it's not a structured record, but a single 104-character string blob.
Let's print it:

```{code-cell} ipython3
# The `params` entry stores the inputs, but as one opaque string.
print(repr(data['params'].item()))
```

So the inputs *are* in the output file, but as an opaque JSON-serialised string with no schema.
You can't query it without first parsing the JSON back into a dict yourself, and there is no guarantee that the next code you wrap will follow the same convention (or any convention at all).

:::{admonition} Results scattered across stdout and the output file
:class: warning

- The arrays go to a binary file (`results.npz`), but the summary diagnostics (`variance(V)`, `mean(V)`) only appear on stdout
- The output filename is hardcoded, so two runs in the same directory overwrite each other
- The input parameters are buried inside the output file as an opaque JSON blob with no schema; querying or filtering across many runs requires writing a custom parser
:::

## Running again

<!-- MOTIVATION: Show how quickly you lose track of what produced what.
     The user edits the input file, runs again, and now the original
     input is gone. The output file doesn't help either. -->

What if we want to try a different feed rate?
The natural thing to do is to open `input.yaml` in a text editor and change `F` from `0.04` to `0.055`.
Editing inputs by hand like this is convenient, but it has its own hazard: many scientific codes (`gsrd` included) silently ignore keys they don't recognize, so a mistyped parameter name runs cleanly using the default value instead of raising an error.

```{code-cell} ipython3
# Change the feed rate F from 0.04 to 0.055.
# In practice you would edit input.yaml in a text editor; here we do it in
# code so the notebook runs top to bottom on its own.
import yaml

with open('tmp/input.yaml') as f:
    params = yaml.safe_load(f)

params['F'] = 0.055

with open('tmp/input.yaml', 'w') as f:
    yaml.dump(params, f)
```

Then run the same command again:

```{code-cell} ipython3
:tags: ["hide-output"]

!cd tmp && gsrd input.yaml
```

With `F=0.055`, the pattern looks completely different:

```{image} include/reaction-diffusion-fields-2.png
:width: 60%
:align: center
```

&nbsp;

However, note that we just overwrote our input file, *and* the `results.npz` of the first run, in one go.
The original parameters are gone, and so is the previous output.
Nothing on disk now records that the first run ever happened.

Quickly tweaking parameters and re-running like this is exactly how the exploratory phase of a scientific project tends to look like in practice, which is precisely why the pain points below are so common.

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

What happens when things go wrong?
The explicit time-integration scheme `gsrd` uses is only stable up to a certain timestep size; push it past that, and the field values blow up.
Let's trigger that by running with an oversized timestep (`dt=100`), using a prepared `input_bad.yaml`:

```{code-cell} ipython3
# Copy in an input with an oversized timestep (dt=100). The integration
# blows up; watch how gsrd reports the failure.
!cp include/input_bad.yaml tmp/input_bad.yaml

import subprocess

result = subprocess.run(
    ['gsrd', 'input_bad.yaml'],
    cwd='tmp',
    capture_output=True,
    text=True,
)
print('Exit code:', result.returncode)
print(result.stderr)
```

Three things are simultaneously wrong with that failure mode:

- The exit code is `0`. As far as your shell or any orchestration script is concerned, the run succeeded.
- The only signal that something failed is a terse `ERR:` line on stderr (here preceded by a numpy `RuntimeWarning` about the overflow that caused it), plus the *absence* of `*** JOB DONE ***` on stdout.
- `results.npz` was not written. Combined with the zero exit code, an automation script downstream will happily try to open a non-existent file, or worse, pick up a stale `results.npz` from a previous run.

In practice this is often harder to spot, with the relevant line buried among pages of other output.
But even the minimal version here doesn't tell you what to fix or how to recover.

:::{admonition} Failures are hard to diagnose and easy to lose
:class: warning

- Exit codes are not reliable: many scientific codes always return 0 and signal failure through log markers instead
- Failed runs may produce no output file at all, or, worse, a partial file that looks plausible
- Even when error messages exist, connecting them back to the right inputs and parameters is up to you
:::

## How this becomes even worse at real-world scale

<!-- MOTIVATION: The punchline of Module 0. We already surfaced the concrete
     pain points inline as they appeared; here we project them to real-world
     scale to make the case for AiiDA compelling. -->

We ran just two simulations and already had to track inputs by hand, hunt for scalars in stdout, watch a re-run silently overwrite the previous one, and nearly miss a failure that still reported a successful exit code of `0`.
None of these are bugs in `gsrd`; they are the everyday texture of scientific software.
Mildly annoying at two runs, they turn into real problems once you scale up.

:::{note}
Now imagine doing this not for 2 runs, but for **100 different parameter combinations**.
You'd need a naming convention, a spreadsheet, and custom scripts to execute and keep track of your simulations.
Those approaches are fragile, and the resulting data (and the workflow that produced it) is hard to pass on to a colleague.
:::

At that scale, more things start to go wrong:

- **Scattered data**: input and output files can end up on scratch filesystems across different clusters, your local machine, and shared drives. Months later, just tracking down which directory holds the converged results becomes a chore in itself.
- **Multi-step workflows**: one code prepares the geometry, another runs the simulation, a third post-processes the results. If step 2 fails for 15 out of 100 runs, how do you figure out which ones failed, why, and how to re-run just those? You'd have to manually identify the failures, fix or adjust the inputs, and re-run each.
- **Heterogeneous output formats**: each code has its own conventions. Some write structured output (e.g., XML or HDF5) that is easy to parse, others (`gsrd` included) scatter key numbers across plain-text logs with no defined schema. Extracting results programmatically across many such codes often means writing and maintaining fragile custom parsers that break with new code versions.
- **Code versions and environments**: was this result produced with v2.1 or v2.3? Compiled with which flags? On which cluster? You'd easily lose track unless you logged it yourself.
- **Post-processing at scale**: aggregating a single number from each of hundreds of output files requires custom scripts that might break when the output format changes.
- **Collaboration and handover**: a colleague takes over your project. They inherit a directory tree of thousands of files with no documentation of what produced what. You could write a README, but keeping it up to date is yet another manual task that rarely happens in practice.

## How AiiDA solves these problems

AiiDA is a workflow manager designed for exactly these problems.
At its core is the **provenance graph**: an automatic record of every calculation, its inputs, its outputs, and how they all connect, for every run, including failed ones.
It gives you:

- **Provenance tracking**: nothing is lost. Every result can be traced back to the exact inputs, code, and machine that produced it. No overwriting, no orphaned files, no need to keep input YAMLs around by hand.
- **Workflow orchestration**: multi-step pipelines run as managed workflows, handling execution, data passing, and error recovery. If some steps fail, AiiDA knows which ones, why, and can help you restart just those.
- **Reliable failure detection**: parsers shipped with AiiDA plugins look for the markers that actually indicate success or failure (e.g., a `*** JOB DONE ***` line on stdout), so a run with a spurious zero exit code still gets flagged as failed and the downstream workflow does not blindly carry on.
- **Reproducibility and sharing**: the full provenance graph can be exported as a portable archive. A collaborator can easily reproduce, audit, or extend your work.
- **Structured output parsing**: AiiDA plugins provide parsers that extract structured results from a code's output files *and* its stdout, store them as queryable database entries, and let you search and filter across all your calculations without ever manually opening a single file.
- **Community knowledge**: AiiDA plugins for popular codes ship with workflows, parsers, and error handlers, encoding years of domain expertise. You benefit from best practices without having to painfully discover them yourself.

:::{important}
The promise is not just "more throughput".
It is that the **scaffolding around your simulations** (bookkeeping, parsing, restart logic, retries) **stops being your problem**, so the time you'd otherwise spend fighting tooling goes back to doing science.
:::

Buckle up: in {ref}`Module 1 <tutorial:module1>`, we'll run the same `gsrd` simulation through AiiDA and start seeing the benefits in action.

## Further reading

- The `gsrd` package and the conventions it deliberately mimics: <https://github.com/aiidateam/gsrd>
- AiiDA's provenance model: {ref}`topics:provenance`
