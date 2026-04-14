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
# Module 0: Life without AiiDA

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module0.ipynb` {octicon}`download`
:::

<!-- MOTIVATION: Give users an immediate, visual sense of what the simulation
     produces, so they care about the rest of the module. Keep it simple:
     one image, plain language, no jargon. -->

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

## Running the simulation

<!-- MOTIVATION: Show the typical experience of running a scientific code.
     Users should recognize the UX from their own work: a CLI tool with
     an input file that produces output, where critical results are scattered
     across stdout and the output file. -->

The simulation is invoked like a typical scientific code: a command-line executable that reads an input file and writes results to an output file:

```{code-cell} ipython3
:tags: ["remove-cell"]

import tempfile
from pathlib import Path

work_dir = Path(tempfile.mkdtemp(prefix='aiida_tut_m0_'))
```

```console
$ ./reaction-diffusion.py --input input.yaml --output results.yaml
```

```{code-cell} ipython3
:tags: ["remove-input"]

# Actually run the simulation (hidden from rendered output).
!python3 include/reaction-diffusion.py \
    --input include/input.yaml \
    --output {work_dir}/results.yaml
```

Let's look at the output file:

```{code-cell} ipython3
:tags: ["remove-input"]

with open(f'{work_dir}/results.yaml') as f:
    print(f.read(), end='')
```

The simulation ran and produced some numbers, but notice what's missing: there is no record of which parameters were used to produce these results.

:::{admonition} Inputs are disconnected from the output
:class: warning

The output file only contains computed results, not the parameters that produced them.
If you come back next week you won't know to which execution this file belongs to.
:::

<!-- TODO: Once gsrd prints critical info to stdout, add a pain point
     admonition about results being scattered across stdout and the output
     file, and how you'd lose the stdout results unless you redirect to
     a log. -->

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
import shutil
import yaml

input_path = work_dir / 'input.yaml'
shutil.copy('include/input.yaml', input_path)

with open(input_path) as f:
    params = yaml.safe_load(f)
params['F'] = 0.055
with open(input_path, 'w') as f:
    yaml.dump(params, f)
```

Then run the same command again:

```console
$ ./reaction-diffusion.py --input input.yaml --output results.yaml
```

With `F=0.055`, the pattern looks completely different:

```{image} include/reaction-diffusion-fields-2.png
:width: 60%
:align: center
```

&nbsp;

However, note that we just overwrote our input file, and now the original parameters are gone.
As the output doesn't record what was used, it's not clear which result came from which parameter set. You'd have to remember, or manually organize your folders and files accordingly.

:::{admonition} No systematic record of your work
:class: warning

- By editing the input file in place, the original parameters are now gone
- Without a systematic way to organize runs, results become untraceable and data may be lost
:::

:::{note}
This example might seem contrived here, but during the exploratory phase of a computational science project, quickly tweaking parameters and re-running is exactly how people often work in practice.
:::

## Running with errors

<!-- MOTIVATION: Show that errors from scientific codes are often cryptic
     and leave no useful trace. The user has no idea what went wrong, and
     no record that the run even happened. -->

What happens when things go wrong? Let's try with `F=0.1`:

```console
$ ./reaction-diffusion.py --input input.yaml --output results.yaml
```

```{code-cell} ipython3
:tags: ["remove-input"]

# Actually run with the bad input (show only its output).
import subprocess
result = subprocess.run(
    ['python3', 'include/reaction-diffusion.py',
     '--input', 'include/input_bad.yaml',
     '--output', f'{work_dir}/results_bad.yaml'],
    capture_output=True, text=True,
)
if result.stderr:
    print(result.stderr)
print(f'Exit code: {result.returncode}')
```

A wall of text referencing internal functions and a cryptic error code.
The error message doesn't tell you what to fix, and you're left digging through source code to make sense of it.

:::{admonition} Failures are hard to diagnose and easy to lose
:class: warning

- Error messages are often cryptic and hard to act on
- Failed runs may not produce any output at all
- Even when error logs exist, connecting them back to the right inputs is up to you
:::

## So, what's the problem?

<!-- MOTIVATION: The punchline of Module 0. Connect the concrete pain
     points above to what AiiDA solves, then paint the picture at scale
     to make the case compelling. -->

### What we already saw

We ran just a couple of simulations and already hit these problems:

- **Inputs disconnected from outputs**: there's no automatic link between what you ran and what you got, unless you track it yourself
- **Original parameters lost**: we edited the input file in place, and the previous version is gone
- **Manual bookkeeping**: even with careful naming and folder organization, keeping track of everything is up to you and prone to mistakes
- **Failures are hard to fix**: error messages are often cryptic, and connecting them back to the right inputs and parameters is up to you

### What happens at real-world scale

:::{note}
Now imagine doing this not for 2 runs, but for **100 different parameter combinations**.
You'd need a naming convention, a spreadsheet, and custom scripts to execute and keep track of your simulations.
Those approaches are fragile, and the resulting data (and the workflow that produced it) is hard to pass on to a colleague.
:::

Some more things that can go wrong at scale:

- **Scattered data**: input and output files can end up on scratch filesystems across different clusters, your local machine, and shared drives. After a few months, good luck finding which directory has the converged results.
- **Multi-step workflows**: one code prepares the geometry, another runs the simulation, a third post-processes the results. If step 2 fails for 15 out of 100 runs, how do you figure out which ones failed, why, and how to re-run just those? You'd have to manually identify the failures, fix or adjust the inputs, and re-run each.
- **Unstructured output formats**: many codes write plain text files with no defined schema. Extracting results programmatically often means writing fragile custom parsers that can break with new code versions.
- **Code versions and environments**: talking of code versions, was this result produced with v2.1 or v2.3? Compiled with which flags? On which cluster? You'd easily lose track unless you logged it yourself.
- **Post-processing at scale**: aggregating a single number from each of hundreds of output files requires custom scripts that might break when the output format changes.
- **Collaboration and handover**: a colleague takes over your project. They inherit a directory tree of thousands of files with no documentation of what produced what. You could write a README, but keeping it up to date is yet another manual task that rarely happens in practice.

## How AiiDA solves these problems

AiiDA is a workflow manager designed for exactly these problems.
It automatically builds a **provenance graph** that records every input, every output, which code ran on which machine, and how they are all connected, for every calculation, including failed ones.
It gives you:

- **Provenance tracking**: every calculation is recorded with its full history. Inputs, outputs, metadata, the code it ran with, and the machine it ran on, are linked together automatically. Nothing is lost. Everything is tracked.
- **Workflow orchestration**: multi-step pipelines run as managed workflows, handling execution, data passing, and error recovery. If some steps fail, AiiDA knows which ones, why, and can help you restart just those.
- **Reproducibility and sharing**: the full provenance graph can be exported and shared. A colleague can trace any result back to the exact inputs, code, and parameters that produced it.
- **Structured output parsing**: AiiDA plugins provide parsers that extract structured results from code output files and store them as queryable database entries, so you can search and filter across all your calculations without ever opening a single file.
- **Community knowledge**: AiiDA plugins for popular codes ship with workflows, parsers, and error handlers, encoding years of domain expertise. You benefit from best practices without having to painfully discover them yourself.

Buckle up: in {ref}`Module 1 <tutorial:module1>`, we'll run the same simulation through AiiDA and start seeing the benefits in action.
