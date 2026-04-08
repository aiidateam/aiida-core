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

## The simulation script

The script is called like a typical command-line tool:

```console
$ python3 reaction-diffusion.py input.yaml --output results.npz
JOB DONE
```

The key inputs and outputs:

| | Name | Description |
|---|---|---|
| **Input** | `F` | Feed rate (primary scan parameter) |
| | `k` | Kill rate |
| | `n_steps` | Number of simulation iterations |
| **Output** | `U_final`, `V_final` | Final 2D concentration fields |
| | `variance_V` | Scalar measure of pattern "strength" |

The script is provided as {download}`include/reaction-diffusion.py` -- expand the box below to inspect it, or just move on.

:::{dropdown} Inspect the simulation script
```{literalinclude} include/reaction-diffusion.py
:language: python
```
:::

## Running the simulation

Let's run the simulation directly -- no AiiDA involved yet.

```{code-cell} ipython3
# Run the simulation script directly via subprocess.
import subprocess
import tempfile
from pathlib import Path

from include.constants import BASE_PARAMS, SCRIPT_PATH

input_path = Path('include/input.yaml').resolve()
work_dir = Path(tempfile.mkdtemp())
output_path = work_dir / 'results.npz'

result = subprocess.run(
    ['python3', str(SCRIPT_PATH), str(input_path), '--output', str(output_path)],
    capture_output=True,
    text=True,
)

print(f"Exit code: {result.returncode}")
print(f"Stdout: {result.stdout.strip()}")
```

The simulation succeeded. Let's load and inspect the output:

```{code-cell} ipython3
# Load the .npz output and print scalar results.
import numpy as np

data = np.load(output_path)

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

## What happens when things go wrong

Not all parameter combinations produce interesting patterns.
Let's try with `F=0.1` (too high -- the feed rate overwhelms the reaction):

```{code-cell} ipython3
# Re-run with a bad parameter (F=0.1) to demonstrate failure handling.
import yaml

bad_params = BASE_PARAMS | {'F': 0.1}  # Too high — no pattern forms

bad_input_path = work_dir / 'input_bad.yaml'
bad_input_path.write_text(yaml.dump(bad_params))
bad_output_path = work_dir / 'results_bad.npz'

result_bad = subprocess.run(
    ['python3', str(SCRIPT_PATH), str(bad_input_path), '--output', str(bad_output_path)],
    capture_output=True,
    text=True,
)

print(f"Exit code: {result_bad.returncode}")
print(f"Stderr: {result_bad.stderr.strip()}")
```

The simulation detected a **trivial steady state** (exit code 30) -- no pattern formed, and no output file was written.
When running many simulations with different parameters, some will inevitably fail like this.

## What's missing?

We ran a simulation and got results. But consider what happened:

- The results sit in a local file with **no record** of what produced them -- if we had 20 result files, we couldn't tell which parameters produced which
- The **failed run** (F=0.1) left no trace -- we'd have to remember that we tried it
- If we change the simulation script, there's **no record** of which version produced which results

In short: the computation worked, but nothing is **tracked, searchable, or reproducible**.

In {ref}`Module 1 <tutorial:module1>`, we'll run the same simulation through AiiDA, which solves all of these problems automatically.
