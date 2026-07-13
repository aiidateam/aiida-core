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

(tutorial:module6b)=
# Module 6b: Workflows that build themselves

:::{note}
This module continues {ref}`Module 6a <tutorial:module6a>` and reuses its `If`-gated pipeline.
If you are following along locally, work through {ref}`Module 6a <tutorial:module6a>` first.
:::

## What you will learn

After this module, you will be able to:

- Give each iteration of a `Map` its own shape, by putting an `If`-gated pipeline inside the `Map`.
- Build part of a workflow's graph from **data that wasn't known when you wrote it**, using a calcfunction to turn one stage's outputs into the next stage's parameter set.
- Combine both into a single adaptive sweep whose refined parameters are computed midway through the run.

:::{note} Setup
This module uses AiiDA, `aiida-shell`, and `aiida-workgraph`:

```bash
pip install aiida-core aiida-shell aiida-workgraph
```
:::

```{code-cell} ipython3
# Set up the tutorial's isolated sandbox profile (same as Module 1).
# `%load_ext aiida` enables the `%verdi` magic; `%run` creates or loads the
# shared `tutorial-<hash>` profile, so data from earlier modules is available.
%load_ext aiida
%run -i include/setup_tutorial.py
```

We build on {ref}`Module 6a <tutorial:module6a>`, so we pull in the same helpers.
Because each notebook runs in its own kernel, the shared pieces come from `include/`:

```{code-cell} ipython3
from typing import Annotated

from aiida import orm
from aiida_workgraph import If, Map, dynamic, namespace, task

from include.workflows import gray_scott_pipeline
from include.tasks import fft_peak_wavelength, identify_transition_region

# The default Gray-Scott parameters and the feed-rate scan (same as Module 2).
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
F_VALUES = [0.038, 0.040, 0.042, 0.044, 0.046, 0.050, 0.055, 0.060]
```

We also reuse `pipeline_with_optional_fft` from {ref}`Module 6a <tutorial:module6a>`, repeated here (folded) so this notebook runs standalone:

```{code-cell} ipython3
:tags: [hide-input]

# The If-gated pipeline from Module 6a: run the pipeline, then run the FFT
# only if the run's variance clears a threshold.
@task.graph()
def pipeline_with_optional_fft(
    parameters: orm.Dict,
    command: orm.AbstractCode,
    variance_threshold: float,
):
    """Run the Module 3 pipeline, then run the FFT only if the run looks interesting."""
    result = gray_scott_pipeline(parameters=parameters, command=command)
    with If(result.variance_V > variance_threshold):
        task(fft_peak_wavelength)(results_npz=result.results_npz)
```

## `If` inside `Map`: per-iteration variable shape

Module 3's `gray_scott_sweep` ran the same three-step pipeline for every `F`: every iteration had the **same shape**.
What happens if we put an `If`-gated pipeline inside the `Map`?
Each iteration's internal shape is then decided **by that iteration's own data**: one run does the FFT, the next one does not, all from the same `param_sweep`.
The outer graph builds the loop body once; the engine fans it out at runtime, and the shape of each fan-out branch is independent.

```{code-cell} ipython3
@task.graph()
def conditional_sweep(
    param_sweep: Annotated[dict, dynamic(dict)],
    command: orm.AbstractCode,
    variance_threshold: float,
):
    """A coarse F-sweep where each iteration decides for itself whether to run the FFT."""
    with Map(param_sweep) as m:
        pipeline_with_optional_fft(
            parameters=m.item.value,
            command=command,
            variance_threshold=variance_threshold,
        )


param_sweep = {
    f'F_{f:.3f}'.replace('.', '_'): {**BASE_PARAMS, 'F': f}
    for f in F_VALUES
}
wg_cond = conditional_sweep.build(
    param_sweep=param_sweep,
    command=gsrd_code,
    variance_threshold=0.005,
)
```

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg_cond.run()
```

Counting how many `fft_peak_wavelength` processes ran shows the fan-out's variable shape directly:

```{code-cell} ipython3
fft_runs = sum(
    1 for c in wg_cond.process.called_descendants
    if c.process_label == 'fft_peak_wavelength'
)
print(f'FFT ran for {fft_runs} of {len(param_sweep)} sweep points '
      f'(threshold variance(V) > 0.005).')
```

`Map` plus a uniform sub-graph (Module 3) gives you `N` identical iterations.
`Map` plus an `If`-gated sub-graph (this section) gives you `N` iterations whose shape is decided per-iteration, from data that did not exist when you wrote the graph.

## Putting it together: an adaptive sweep

The final pattern combines the dynamic-shape idea with one more move: building *part of the graph from the output of an earlier part of the same graph*.
Concretely, we want a coarse `F`-sweep to *decide* where a refined sweep should land, then refine there.
The interesting parameter values do not exist when the workflow starts; they are computed midway through.

The recipe has three parts:

1. **Coarse sweep**: run `gsrd` over a sparse grid of `F` values to locate the transition.
2. **Identify**: a task (`identify_transition_region`) consumes the coarse `{F: variance}` map and returns a refined parameter sweep clustered around the steepest variance jump.
3. **Refined sweep + analysis**: a second `Map` runs `gsrd` plus an FFT on each refined point.

The trick that makes step 3 depend on step 2 is the `Map` source: it is a *socket* (`refined.result`), not a Python dict, so AiiDA only enumerates the iteration keys once the coarse sweep has finished.

The coarse sweep needs only `variance_V`; the refined sweep needs both `variance_V` and `results_npz` (for the FFT). `gray_scott_pipeline` from `include/workflows.py` already exposes all three outputs, so we reuse it for both `Map` zones below.

```{code-cell} ipython3
fft_peak_wavelength_task = task(fft_peak_wavelength)
```

Now the adaptive sweep itself.
It is one `@task.graph()` that contains two `Map` zones; the second one's source comes from a task that consumes the first one's output.

```{code-cell} ipython3
@task.graph()
def adaptive_sweep(
    coarse_sweep: Annotated[dict, dynamic(dict)],
    base_parameters: orm.Dict,
    command: orm.AbstractCode,
    n_refined: orm.Int,
) -> namespace(
    coarse_variances=dynamic(float),
    refined_variances=dynamic(float),
    refined_wavelengths=dynamic(float),
):
    """Coarse F-sweep -> locate transition -> refined sweep with FFT on each point."""
    # 1. Coarse sweep: only the variance is needed to locate the transition.
    with Map(coarse_sweep) as coarse:
        run = gray_scott_pipeline(parameters=coarse.item.value, command=command)
        coarse.gather({'variance_V': run.variance_V})

    # 2. Identify: build the refined sweep dict from the coarse variances.
    refined = identify_transition_region(
        variances=coarse.outputs.variance_V,
        base_parameters=base_parameters,
        n_refined=n_refined,
    )

    # 3. Refined sweep: the Map source is the *socket* refined.result, not a static dict.
    with Map(refined.result) as fine:
        fine_run = gray_scott_pipeline(parameters=fine.item.value, command=command)
        wavelength = fft_peak_wavelength_task(results_npz=fine_run.results_npz)
        fine.gather({
            'variance_V': fine_run.variance_V,
            'wavelength': wavelength.result,
        })

    return {
        'coarse_variances': coarse.outputs.variance_V,
        'refined_variances': fine.outputs.variance_V,
        'refined_wavelengths': fine.outputs.wavelength,
    }
```

```{code-cell} ipython3
# A slightly longer simulation than the M2/M3 default so the FFT analysis
# has well-developed patterns to measure.
adaptive_base = {**BASE_PARAMS, 'n_steps': 8000}

coarse_sweep_input = {
    f'F_{f:.3f}'.replace('.', '_'): {**adaptive_base, 'F': f}
    for f in F_VALUES
}

wg_adaptive = adaptive_sweep.build(
    coarse_sweep=coarse_sweep_input,
    base_parameters=orm.Dict(adaptive_base),
    command=gsrd_code,
    n_refined=orm.Int(5),
)
```

The graph mirrors the three-step recipe one-to-one: two `map_zone` siblings (the coarse and refined sweeps) bridged by the `identify_transition_region` task. The refined `map_zone` reads its source socket from `identify_transition_region.result`, so the engine cannot begin the refined fan-out until the coarse `Map`'s `variance_V` gather has finished and `identify_transition_region` has produced the new parameter set.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg_adaptive
```

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg_adaptive.run()
```

The refined sweep is clustered where the coarse sweep showed the steepest change in variance. Inspect both:

```{code-cell} ipython3
from include.plotting import plot_adaptive_sweep

plot_adaptive_sweep(
    coarse_variances=wg_adaptive.outputs.coarse_variances._value,
    refined_variances=wg_adaptive.outputs.refined_variances._value,
)
```

The wavelength estimate from the FFT is in there too, one per refined point:

```{code-cell} ipython3
def _key_to_f(key: str) -> float:
    """Reverse the ``F_0_038`` key encoding back to a float."""
    _, integer, fractional = key.split('_')
    return float(f'{integer}.{fractional}')


wavelengths = wg_adaptive.outputs.refined_wavelengths._value
for key in sorted(wavelengths):
    print(f'  F = {_key_to_f(key):.4f}  ->  wavelength = {float(wavelengths[key]):.2f} cells')
```

What AiiDA recorded is one workflow node with the whole story attached: the coarse `Map`, the `identify_transition_region` step that bridged the two, the refined `Map`, and the per-point FFT analysis.
None of the refined parameter values existed before the workflow ran.

## Next steps

You can now build workflows whose shape depends on intermediate data, not just on what you knew when you wrote the script.
The remaining piece, recovering from failures (exit codes, retries, parameter adjustments), is the topic of {ref}`Module 7 <tutorial:module7>`.
Error handlers are themselves another control-flow feature of WorkGraph: a way to extend the graph dynamically when a task fails, rather than when a predicate succeeds.

## Further reading

- WorkGraph concepts and process abstractions: {ref}`topics:workflows`, {ref}`topics:workflows:concepts`
- Process states and exit codes (background for Module 7): {ref}`topics:processes:concepts`, {ref}`topics:processes:concepts:exit_codes`
- WorkGraph `If` / `While` / `Map` zone tasks and the graph context: [aiida-workgraph documentation](https://aiida-workgraph.readthedocs.io)
- Building data products from provenance after the fact (instead of inside the workflow): {ref}`Module 5 <tutorial:module5>`
