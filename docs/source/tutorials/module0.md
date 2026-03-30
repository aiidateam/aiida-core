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

## What you will learn

After this module, you will be able to:

- Understand the Gray-Scott reaction-diffusion model we use throughout the tutorial
- Run the simulation script from the command line
- Inspect and visualize the simulation outputs
- Recognize the limitations of running simulations without any management layer

## The Gray-Scott model

This tutorial teaches you the core concepts of AiiDA through a single, running example: a **reaction-diffusion simulation** based on the Gray-Scott model.

*"This code simulates how two diffusing and reacting substances on a 2D grid spontaneously form spatial patterns, starting from a nearly uniform initial state."*

:::{admonition} Why this example?
:class: tip

- **Conceptually simple**: You do not need to understand the full mathematics to follow the tutorial; the model provides a visually intuitive result.
- **Parameterizable**: The main parameters (feed rate F, kill rate k, diffusion constants) are scalars that are easy to sweep.
- **Deterministic and reproducible**: Simulations with the same seed always produce the same results.
- **Visual output**: Produces 2D patterns, providing immediate feedback.
- **Error-prone in a controlled way**: Numerical instabilities or trivial states allow natural introduction of exit codes, handlers, and debugging.
:::

:::{dropdown} Longer explanation of the Gray-Scott model
*"Reaction-diffusion systems model two competing processes: chemicals spreading out (diffusion) and chemicals transforming into each other (reaction). In the Gray-Scott model specifically, we track two substances U and V on a grid. U is constantly fed into the system and both substances can decay, while V catalyzes its own production from U in a positive feedback loop. When diffusion, feeding, and decay are balanced just right, these simple local rules spontaneously create global patterns -- the same mathematical framework explains everything from leopard spots to chemical oscillations in test tubes. The fascinating part is that identical starting conditions (nearly uniform concentrations everywhere) can produce wildly different patterns just by tweaking two parameters: the feed rate F and kill rate k."*
:::

## The simulation script

Throughout this tutorial we use a command-line Python script that mimics the pattern of a real scientific code:

- **Input**: a YAML file with simulation parameters
- **Output**: a `.npz` file containing the final fields and scalar diagnostics
- **Exit codes**: `0` (success), `10`/`11` (invalid parameters), `20` (numerical instability), `30` (trivial steady state)

The script is called like a typical command-line tool:

```console
$ python3 reaction-diffusion.py input.yaml --output results.npz
JOB DONE
```

The script is provided as {download}`include/reaction-diffusion.py` -- expand the box below to inspect it, or just move on.

:::{dropdown} Inspect the simulation script
```{literalinclude} include/reaction-diffusion.py
:language: python
```
:::

### Input and output overview

#### Inputs (YAML file)

| Parameter | Type | Description |
|-----------|------|-------------|
| `grid_size` | int | Size of the 2D grid (grid_size x grid_size) |
| `du`, `dv` | float | Diffusion rates of U and V |
| `F` | float | Feed rate (primary scan parameter) |
| `k` | float | Kill rate |
| `dt` | float | Time step for simulation |
| `n_steps` | int | Number of iterations |
| `seed` | int, optional | Random seed for reproducibility |

#### Outputs (`.npz` file)

| Output | Type | Description |
|--------|------|-------------|
| `U_final` | 2D array | Final distribution of U (values 0-1) |
| `V_final` | 2D array | Final distribution of V (values 0-1) |
| `variance_V` | float | Scalar measure of pattern "strength" |
| `mean_V` | float | Average value of V |
| `params` | JSON string | Full simulation parameters used |

#### Success and failure signaling

- **Success**: stdout prints `JOB DONE`, exit code 0
- **Failure**: non-zero exit code with `ERROR[code]: message` on stderr

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 10 | Diffusion constants not positive |
| 11 | Time step not positive |
| 20 | Numerical instability (NaN/Inf detected) |
| 30 | Trivial steady state (no pattern formed) |

## Running the simulation

Let's run the simulation directly -- no AiiDA involved yet.
First, we create a YAML input file with our parameters:

```{code-cell} ipython3
import subprocess
import tempfile
from pathlib import Path

import yaml

work_dir = Path(tempfile.mkdtemp())

params = {
    'grid_size': 64,
    'du': 0.16,
    'dv': 0.08,
    'F': 0.04,
    'k': 0.065,
    'dt': 1.0,
    'n_steps': 3000,
    'seed': 42,
}

input_path = work_dir / 'input.yaml'
input_path.write_text(yaml.dump(params))
print(f"Input file written to: {input_path}")
```

Now we run the script using `subprocess`, just like you would run any command-line tool:

```{code-cell} ipython3
script_path = Path('include/reaction-diffusion.py').resolve()
output_path = work_dir / 'results.npz'

result = subprocess.run(
    ['python3', str(script_path), str(input_path), '--output', str(output_path)],
    capture_output=True,
    text=True,
)

print(f"Exit code: {result.returncode}")
print(f"Stdout: {result.stdout.strip()}")
```

The simulation succeeded. Let's load and inspect the output:

```{code-cell} ipython3
import numpy as np

data = np.load(output_path)

print(f"variance(V) = {float(data['variance_V']):.4e}")
print(f"mean(V)     = {float(data['mean_V']):.4e}")
print(f"Fields shape: {data['U_final'].shape}")
```

## Visualizing the results

```{code-cell} ipython3
%run -i include/plot_fields.py
plot_uv_fields(u_field=data['U_final'], v_field=data['V_final'])
```

The simulation produces striking spatial patterns.
The U field (substrate) shows depleted regions where V (activator) has formed structures -- spots and labyrinthine patterns that emerge spontaneously from uniform initial conditions.

## What happens when things go wrong

Not all parameter combinations produce interesting patterns.
Let's try with `F=0.1` (too high -- the feed rate overwhelms the reaction):

```{code-cell} ipython3
bad_params = params.copy()
bad_params['F'] = 0.1  # Too high — no pattern forms

bad_input_path = work_dir / 'input_bad.yaml'
bad_input_path.write_text(yaml.dump(bad_params))

result_bad = subprocess.run(
    ['python3', str(script_path), str(bad_input_path), '--output', str(work_dir / 'results_bad.npz')],
    capture_output=True,
    text=True,
)

print(f"Exit code: {result_bad.returncode}")
print(f"Stderr: {result_bad.stderr.strip()}")
```

The simulation detected a **trivial steady state** (exit code 30) -- the pattern never formed.
This is exactly the kind of failure mode that becomes important when running many simulations: you need to detect failures, record them, and possibly retry with different parameters.

## What's missing?

We ran a simulation and got results. But consider what happened:

- The parameters live in a **temporary YAML file** that will be deleted when we close this session
- The results are in a **temporary `.npz` file** with no record of what produced them
- There is **no link** between the input parameters and the output -- if we had 20 result files, we couldn't tell which parameters produced which
- The **failed run** (F=0.1) left no trace -- we'd have to remember that we tried it
- If we change the simulation script, there's **no record** of which version produced which results

In short: the computation worked, but nothing is **tracked, searchable, or reproducible**.

In {ref}`Module 1 <tutorial:module1>`, we'll run the same simulation through AiiDA, which solves all of these problems automatically.
