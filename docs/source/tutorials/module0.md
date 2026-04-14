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
# Module 0: The running example

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module0.ipynb` {octicon}`download`
:::

Throughout this tutorial we use a **reaction-diffusion simulation** as our running example.
It models two chemical substances diffusing and reacting on a 2D grid: depending on the balance of parameters, the simulation produces a variety of spatial patterns, from spots to labyrinthine structures.

```{image} include/reaction-diffusion-fields.png
:width: 80%
:align: center
```

&nbsp;

:::{dropdown} More about the model

The simulation implements a reaction-diffusion system known as the Gray-Scott model.
Two concentrations, U and V, evolve on a 2D grid.
U is continuously fed into the system and both substances decay, while V catalyzes its own production from U in a positive feedback loop.
The interplay of these processes, controlled primarily by the feed rate F and kill rate k, determines what patterns form.
Identical starting conditions can produce wildly different patterns just by tweaking F and k.
:::

## Running the simulation

The simulation script ({download}`include/reaction-diffusion.py`) is called like a typical command-line tool -- let's run it directly, no AiiDA involved yet:

```{code-cell} ipython3
:tags: ["hide-cell"]

import tempfile
from pathlib import Path

work_dir = Path(tempfile.mkdtemp(prefix='aiida_tut_m0_'))
```

```{code-cell} ipython3
# Run the reaction-diffusion simulation via the command line.
!python3 include/reaction-diffusion.py \
    --input include/input.yaml \
    --output {work_dir}/results.yaml
```

The output is a plain YAML file, so we can inspect it directly:

```{code-cell} ipython3
!cat {work_dir}/results.yaml
```

## Running with different parameters

Let's run again with a higher feed rate (`F=0.055` instead of `F=0.04`) to see how the pattern changes:

```{code-cell} ipython3
!python3 include/reaction-diffusion.py \
    --input include/input_2.yaml \
    --output {work_dir}/results_2.yaml
```

```{code-cell} ipython3
!cat {work_dir}/results_2.yaml
```

A different feed rate produces a completely different pattern (compare the image above with the one below):

```{image} include/reaction-diffusion-fields-2.png
:width: 80%
:align: center
```

We now have two result files sitting in a directory -- but which one used which parameters?
You'd have to remember, or carefully encode parameters in filenames yourself.

## Dealing with errors

Not all parameter combinations produce interesting patterns.
Let's try with `F=0.1` (too high -- the feed rate overwhelms the reaction):

```{code-cell} ipython3
# Run with a bad parameter to see how failures look.
!python3 include/reaction-diffusion.py \
    --input include/input_bad.yaml \
    --output {work_dir}/results_bad.yaml; echo "Exit code: $?"
```

The simulation detected a **trivial steady state** (exit code 30) -- no pattern formed, and no output file was written.
Unless you are redirecting stderr to a log file, you will have no record of this calculation, and even then you will have a hard time figuring out _why_ it failed.

## What's missing?

We ran two simulations and got results. But consider what happened:

- We have `results.yaml` and `results_2.yaml` with **no record** of what produced them -- the only way to know which parameters produced which is to remember, or to manually encode them in filenames
- The **failed run** (F=0.1) left no trace at all -- we'd have to remember that we tried it and that it didn't work
- If we change the simulation script, there's **no record** of which version produced which results
- In high-throughput scenarios, managing inputs and outputs by hand quickly becomes unmanageable, and shell scripts to automate this are fragile and difficult to transfer

In short: the computations worked, but nothing is **tracked, searchable, or reproducible**.

In {ref}`Module 1 <tutorial:module1>`, we'll run the same simulation through AiiDA, which solves all of these problems.
