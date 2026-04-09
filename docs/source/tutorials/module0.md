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
# Module 0: The Running Example

:::{tip}
This tutorial can be downloaded and run as a Jupyter notebook: {nb-download}`module0.ipynb` {octicon}`download`
:::

Throughout this tutorial we use a **reaction-diffusion simulation** (Gray-Scott model) as our running example -- a simple script that takes a YAML input file and produces a `.npz` output file, just like a real scientific code would.

:::{dropdown} Why this example? / More about the Gray-Scott model

**Why this example?**

- **Conceptually simple**: You do not need to understand the full mathematics to follow the tutorial; the model provides a visually intuitive result.
- **Parameterizable**: The main parameters (feed rate F, kill rate k, diffusion constants) are scalars that are easy to sweep.
- **Deterministic and reproducible**: Simulations with the same seed always produce the same results.
- **Visual output**: Produces 2D patterns, providing immediate feedback.
- **Error-prone in a controlled way**: Numerical instabilities or trivial states allow natural introduction of exit codes, handlers, and debugging.

**The model**

Reaction-diffusion systems model two competing processes: chemicals spreading out (diffusion) and chemicals transforming into each other (reaction). In the Gray-Scott model specifically, we track two substances U and V on a grid. U is constantly fed into the system and both substances can decay, while V catalyzes its own production from U in a positive feedback loop. When diffusion, feeding, and decay are balanced just right, these simple local rules spontaneously create global patterns -- the same mathematical framework explains everything from leopard spots to chemical oscillations in test tubes. The fascinating part is that identical starting conditions (nearly uniform concentrations everywhere) can produce wildly different patterns just by tweaking two parameters: the feed rate F and kill rate k.
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
# Run the Gray-Scott simulation via the command line.
!python3 include/reaction-diffusion.py \
    --input include/input.yaml \
    --output {work_dir}/results.npz
```

The key inputs and outputs:

| | Name | Description |
|---|---|---|
| **Input** | `F` | Feed rate (primary scan parameter) |
| | `k` | Kill rate |
| | `n_steps` | Number of simulation iterations |
| **Output** | `U_final`, `V_final` | Final 2D concentration fields |
| | `variance_V` | Scalar measure of pattern "strength" |

:::{dropdown} Inspect the simulation script
```{literalinclude} include/reaction-diffusion.py
:language: python
```
:::

The simulation succeeded. Let's load and inspect the output:

```{code-cell} ipython3
# Load the .npz output and print scalar results.
import numpy as np

data = np.load(work_dir / 'results.npz')

print(f"variance(V) = {float(data['variance_V']):.4e}")
print(f"mean(V)     = {float(data['mean_V']):.4e}")
print(f"Fields shape: {data['U_final'].shape}")
```

## Visualizing the results

```{code-cell} ipython3
# Visualize the 2D concentration fields (U and V).
%run -i include/plot_fields.py
plot_uv_fields(u_field=data['U_final'], v_field=data['V_final'])
```

The simulation produces striking spatial patterns.
The U field (substrate) shows depleted regions where V (activator) has formed structures -- spots and labyrinthine patterns that emerge spontaneously from uniform initial conditions.

## Running with different parameters

Let's run again with a higher feed rate (`F=0.055` instead of `F=0.04`) to see how the pattern changes:

```{code-cell} ipython3
# Run a second simulation with a different feed rate.
!python3 include/reaction-diffusion.py \
    --input include/input_2.yaml \
    --output {work_dir}/results_2.npz
```

```{code-cell} ipython3
# Load and visualize the second run.
data_2 = np.load(work_dir / 'results_2.npz')

print(f"variance(V) = {float(data_2['variance_V']):.4e}")
plot_uv_fields(u_field=data_2['U_final'], v_field=data_2['V_final'])
```

A different feed rate produces a completely different pattern.
We now have two result files sitting in a directory -- but which one used which parameters?
You'd have to remember, or carefully encode parameters in filenames yourself.

## When things go wrong

Not all parameter combinations produce interesting patterns.
Let's try with `F=0.1` (too high -- the feed rate overwhelms the reaction):

```{code-cell} ipython3
# Re-run with a bad parameter (F=0.1) to demonstrate failure handling.
import subprocess

result_bad = subprocess.run(
    ['python3', 'include/reaction-diffusion.py',
     '--input', 'include/input_bad.yaml',
     '--output', str(work_dir / 'results_bad.npz')],
    capture_output=True,
    text=True,
)

print(f"Exit code: {result_bad.returncode}")
print(f"Stderr: {result_bad.stderr.strip()}")
```

The simulation detected a **trivial steady state** (exit code 30) -- no pattern formed, and no output file was written.
When running many simulations with different parameters, some will inevitably fail like this.

## What's missing?

We ran two simulations and got results. But consider what happened:

- We have `results.npz` and `results_2.npz` with **no record** of what produced them -- the only way to know which parameters produced which is to remember, or to manually encode them in filenames
- The **failed run** (F=0.1) left no trace at all -- we'd have to remember that we tried it and that it didn't work
- If we change the simulation script, there's **no record** of which version produced which results
- In high-throughput scenarios, managing inputs and outputs by hand quickly becomes unmanageable

In short: the computations worked, but nothing is **tracked, searchable, or reproducible**.

In {ref}`Module 1 <tutorial:module1>`, we'll run the same simulation through AiiDA, which solves all of these problems.
