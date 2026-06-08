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

(tutorial:module6)=
# Module 6: Complex workflows

:::{note}
This module reuses the tutorial profile and the `gsrd_code` object created in {ref}`Module 1 <tutorial:module1>`, and assumes you have read {ref}`Module 3 <tutorial:module3>` (`@task.graph()`, `Map`, `shelljob`).
If you are following along locally, run those first.
:::

## What you will learn

After this module, you will be able to:

- Decide a workflow's **shape at runtime** using `If` and `While` control-flow regions, so steps run only when they should and loops iterate until convergence.
- Construct parts of a workflow's structure from **data that wasn't known when you wrote the graph**, using a calcfunction as the bridge between an earlier stage's outputs and a later stage's parameter set.
- Combine these features into a single workflow whose shape **emerges at runtime** from its own intermediate results.

```{code-cell} ipython3
:tags: ["remove-cell"]

# Auto-generated tutorial profile for docs build.
# If running locally with your own profile (e.g. from ``verdi presto``),
# replace this cell with:
#
#     from aiida import load_profile
#     load_profile()

%load_ext aiida
%run -i include/setup_tutorial.py
```

## When fixed-shape workflows aren't enough

Module 3's `gray_scott_pipeline` and `gray_scott_sweep` had a **fixed shape**: the same three steps for every parameter set, the same map fan-out, the same reduction at the end.
That's the right shape when you already know what you want to compute.
Real research is rarely that tidy:

- An expensive diagnostic is only worth running on the runs where it would say something useful.
- A simulation has a free parameter (a time step, a tolerance, a grid size) that has to be *driven* until a quantity stabilises.
- The interesting parameter range only becomes clear *after* a first cheap scan.

WorkGraph supports all these use cases through three additional building blocks, on top of what you already know:

- `If` and `While` are **control-flow regions**, written as Python context managers in your graph definition; they select which tasks belong to a region of the graph that may run zero, one, or many times.

  :::{dropdown} A note on terminology
  :icon: info
  aiida-workgraph calls these *zone tasks* in its API. The underlying idea is the same as a *sub-process* in BPMN, a *TaskGroup* in Airflow, or a *region* in a compiler control-flow graph: a region of the graph that groups tasks under structured control flow.
  :::
- The graph's `ctx` is a shared, mutable key-value store, the WorkGraph analogue of the WorkChain `ctx`. Writing into it from inside a `While` region is what lets the loop iterate over evolving state.
- Any calcfunction whose output is a `dict` can be used to **build a parameter set for a downstream `Map`**, because calcfunctions are AiiDA processes whose outputs flow through normal socket connections.

:::{important}
This module pushes Module 3's central insight further: **the workflow graph is data that you build**, and control flow is just normal Python that *adds tasks* to the graph, gated on the outputs of *other* tasks.
`If`, `While`, and `Map` regions don't run Python branches; they declare regions of the graph whose execution is decided at runtime by AiiDA from the values of the sockets you wired in.
(See the Module 3 *"building and running are separate steps"* callout if the sockets-vs-values distinction is not fresh.)
:::

## Conditional analysis with `If`

A simple example: most useful diagnostics are not free.
Running an FFT on the V-field to estimate the dominant pattern wavelength only makes sense for runs that *show* a pattern; spending the same cost on a flat run wastes time and clutters the provenance with meaningless numbers.

We have everything needed from earlier modules:

- `variance_V` is computed cheaply by `parse_output` (Module 2). It is a good `is there a pattern at all?` predicate.
- The full V-field is in `results.npz` (Module 2). The expensive analysis reads it.

`include/tasks.py` exposes a small calcfunction that wraps the analysis:

```{code-cell} ipython3
from include.tasks import fft_peak_wavelength
help(fft_peak_wavelength)
```

The recipe is the gating itself.
We extend the Module 3 pipeline with one `If` zone: the FFT task is only added to the *running* graph when the cheap predicate exceeds a threshold.
`If` is a Python context manager that takes a *condition socket* and an optional `invert_condition` flag (useful for `else`-style zones):

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show `If` signature and docstring'
:    code_prompt_hide: 'Hide signature'

from aiida_workgraph import If
help(If)
```

With the signature in hand, the building blocks are the same as Module 3.
We import `gray_scott_pipeline` from `include/workflows.py`. The canonical version we wrote there exposes `variance_V`, `mean_V`, *and* `results_npz`, so the FFT downstream can read the V-field directly.

```{code-cell} ipython3
from typing import Annotated

from aiida import orm
from aiida_workgraph import If, task

from include.constants import BASE_PARAMS
from include.workflows import gray_scott_pipeline
```

`pipeline_with_optional_fft` then becomes a thin wrapper: call `gray_scott_pipeline`, and gate the FFT on the variance socket.

```{code-cell} ipython3
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

:::{note}
Two details worth noticing:

- **`result.variance_V > variance_threshold` is not a Python boolean.** It is a comparison between an output socket and a value, which WorkGraph compiles into a tiny operator task whose output is itself a socket. That socket is what `If(...)` reads to decide whether to enter the zone at runtime.
- **The body of the `with If(...)`** is not skipped at definition time. Every task inside it is registered into the graph; it is the *execution* of those tasks that the zone gates. This is the same dual-life idea as Module 3's `Map`: build now, decide later.
:::

The graph shape itself makes this concrete: an automatically inserted comparison task (`op_gt`) reads `variance_V` and feeds its boolean output into the `if_zone`, whose single child is `fft_peak_wavelength`. Everything outside the `if_zone` runs unconditionally; the FFT task runs only when the comparison output is `True`.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

pipeline_with_optional_fft.build(
    parameters=orm.Dict({**BASE_PARAMS, 'F': 0.040}),
    command=gsrd_code,
    variance_threshold=0.005,
)
```

To see the *execution-time* difference, build the same workflow twice with the same threshold but different `F`.
At `F = 0.04` the pattern is strong (`variance(V) ≈ 1e-2`), so the FFT fires.
At `F = 0.060` the pattern is much weaker (`variance(V) ≈ 5e-4`), so the FFT is skipped entirely.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg_strong = pipeline_with_optional_fft.build(
    parameters=orm.Dict({**BASE_PARAMS, 'F': 0.040}),
    command=gsrd_code,
    variance_threshold=0.005,
)
wg_strong.run()
wg_weak = pipeline_with_optional_fft.build(
    parameters=orm.Dict({**BASE_PARAMS, 'F': 0.060}),
    command=gsrd_code,
    variance_threshold=0.005,
)
wg_weak.run()
```

```{code-cell} ipython3
:tags: [hide-input]
:mystnb:
:    code_prompt_show: 'Show inspection code (helper that returns descendant count and process labels)'


def descendants(process):
    return sorted({c.process_label for c in process.called_descendants})


def show(label, items):
    print(f'{label}:')
    for item in items:
        print(f'    - {item}')


strong = descendants(wg_strong.process)
weak = descendants(wg_weak.process)

show('F = 0.040', strong)
print()
show('F = 0.060', weak)
print()
show('Only in F = 0.040', sorted(set(strong) - set(weak)))
```

The first run records a `fft_peak_wavelength` process; the second doesn't. Both runs took the same code through the same `@task.graph()` definition; the **shape** of what AiiDA ran (and recorded) is different.

What did that FFT actually see?
The strong-pattern V-field, when transformed into k-space, shows a ring of energy at a characteristic radius. That radius is the inverse of the dominant pattern wavelength.
The radial profile picks out the peak:

```{code-cell} ipython3
:tags: [hide-input]
:mystnb:
:    code_prompt_show: 'Show inspection code (recover the strong run''s `results.npz` from provenance)'

from include.plotting import plot_fft_spectrum

strong_npz = next(
    c for c in wg_strong.process.called_descendants
    if c.process_label == 'ShellJob<gsrd@localhost>'
).outputs.results_npz
plot_fft_spectrum(strong_npz)
```

::::{dropdown} What am I looking at? The physics of the FFT panels
:icon: question

The Gray-Scott V-field is a 2D image. The **2D Fourier transform** decomposes that image into a sum of plane waves, sinusoidal patterns of varying *wavelength* and *direction*. Each pixel in the left panel corresponds to one plane wave: its position `(k_x, k_y)` is the wave's spatial frequency in each direction, and its brightness is how much of that wave is in the original V-field.

The **centre** of the panel (`k_x = k_y = 0`) is the "DC component", i.e. the spatial average of V. We subtract the mean before the FFT (`centred = v_field - v_field.mean()`) so this term sits near zero and doesn't drown out the pattern.

A **uniform field** would show energy only at the centre. A **field with a single dominant wavelength** (the case here) shows a *ring* of energy at one radius: the wavelength sets the radius, but the pattern has no preferred orientation, so the energy is spread around the ring. That is exactly the structure you see: a bright annulus around the centre, with the diamond-pattern lobes coming from the square grid's discrete sampling.

The **radial profile** (right panel) collapses that 2D image to 1D by averaging over all angles at each radius `k`. The peak in this 1D curve is the dominant radial wavenumber `k_peak`. Converting back to real space: a pattern with wavenumber `k` repeats every `(grid_size / k)` cells, so `k_peak = 4` on a `64`-cell grid means the dominant feature has a **wavelength of about 16 cells**, roughly four stripes/spots across the simulation box, which matches what you can see by eye in the V-field image from Module 2.

The peak shifts as the pattern type changes (spots vs stripes vs labyrinthine), which is why the wavelength is a useful diagnostic to gate downstream analysis on, rather than just "is there a pattern at all" (which `variance(V)` already captures).
::::

::::{dropdown} A different shape: skip an expensive&nbsp;*rerun*, not an expensive&nbsp;*analysis*
:icon: code

The same `If` machinery covers the related case where the expensive thing isn't a post-processing task but a *second simulation* (e.g., a higher-resolution rerun for runs that look pattern-forming).
The structure is identical; only the body of the `If` changes:

```python
with If(parsed.variance_V > variance_threshold):
    hires = shelljob(
        command=command,
        arguments=['{input}'],
        nodes={'input': prepare_input_task(
            parameters={**parameters.get_dict(), 'grid_size': 128}
        ).result},
        outputs=['results.npz'],
    )
```

The takeaway is that an `If` zone is just "a region of the graph that runs only when this socket is truthy." What you put inside it is up to you.
::::

## Iterative simulation with `While`

The next adaptive pattern is iteration.
The Gray-Scott simulation runs for a fixed `n_steps`, and we don't always know in advance how many time steps the pattern needs to settle.
A clean way to handle that is to keep extending the simulation, in 1000-step chunks, until `variance(V)` reaches the saturation level the parameter region produces.

That kind of feedback loop needs three things WorkGraph exposes through `wg.ctx`:

- A place to **initialise** the loop state (`wg.ctx = {...}` before the zone).
- A condition that **reads** ctx and is recomputed every iteration (the `While(...)` argument).
- Tasks inside the zone that **write back** into ctx, so the next iteration sees updated values.

To attach `wg.ctx = {...}` from inside a `@task.graph()` body, we need a handle on the graph being built.
`get_current_graph()` returns that handle: it gives us the same `WorkGraph` object `@task.graph().build(...)` would return, while we are still inside the decorated function.

:::{note}
Under the hood, `get_current_graph()` reads from a [`ContextVar`](https://docs.python.org/3/library/contextvars.html) that aiida-workgraph sets before invoking the decorated body (the same mechanism `with WorkGraph() as wg:` uses internally).
That makes the "current graph" an *ambient* value scoped to the executing coroutine or thread, in the same spirit as Flask's `current_app` or Django's request-local user.
The trade-off is ergonomics versus explicitness: it lets the `If` / `While` / `Map` context managers work without you passing `wg` around, at the cost of the dependency being implicit at the call site.
:::

:::{important}
**About `wg.ctx`**: think of it as the engine's per-graph dictionary that survives between iterations and between zones.
It is the WorkGraph analogue of the WorkChain `ctx` in aiida-core, and it is the *only* channel a `While` body has to thread state from one iteration to the next: the loop body is a *static* sub-graph (built once, executed many times), so the engine has no Python frame to carry local variables across repetitions. Without `ctx`, the growing `n_steps` could not survive the jump from "end of iteration `n`" to "start of iteration `n+1`".

It is also **untyped on purpose**: `wg.ctx = {'parameters': initial, 'done': orm.Bool(False)}` accepts any Python value with no schema or validation, the same as a regular dict. That openness is what makes it useful: the engine cannot know in advance what state a given workflow needs to carry around, so it does not force you to declare it.
The cost is the usual one for freeform key-value stores: if you write the wrong type and read it back later, you find out deep inside a task body at runtime. This is the same trade-off the WorkChain `ctx` has (and that workflow context stores in Airflow, Prefect, and friends all have). A *strictly* typed ctx would defeat its purpose; a more useful direction would be an *optional* per-graph schema you opt into when you want the safety, but that does not exist today in aiida-workgraph.
For now, the working discipline is to define the keys explicitly at the initialisation site and stick to them.
:::

`While` is a Python context manager that takes a condition socket and an optional max-iterations cap:

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show `While` signature and docstring'
:    code_prompt_hide: 'Hide signature'

from aiida_workgraph import While
help(While)
```

The only new helper we need is one that bumps `n_steps` in a parameters dict between iterations, a small calcfunction in `include/tasks.py`:

```{literalinclude} include/tasks.py
:language: python
:pyobject: bump_n_steps
```

```{code-cell} ipython3
from aiida_workgraph import While, get_current_graph
from include.tasks import bump_n_steps

bump_n_steps_task = task(bump_n_steps)
```

Each iteration runs `gsrd` at the current `n_steps`, measures `variance(V)`, and either stops (target reached) or bumps `n_steps` and goes again.
The stopping criterion is just `variance >= target`, which we can write directly on the socket: WorkGraph overloads the comparison operators on sockets, so `result.variance_V >= target` builds an `op_ge` task implicitly (the same way `wg.ctx.done == False` builds an `op_eq` task as the loop condition, or `variance_V > variance_threshold` did for the `If` example earlier).

```{code-cell} ipython3
@task.graph()
def extend_to_plateau(initial, command, target):
    wg = get_current_graph()
    wg.ctx = {
        'parameters': initial,
        'done': orm.Bool(False),
    }
    # E712 = "comparison to False should be 'is False' or 'not <x>'". Suppressed here:
    # `wg.ctx.done` is a socket, not a bool, so `==` builds an `op_eq` task; `is`/`not` would not.
    with While(wg.ctx.done == False, max_iterations=8):  # noqa: E712
        result = gray_scott_pipeline(parameters=wg.ctx.parameters, command=command)
        wg.ctx.parameters = bump_n_steps_task(
            parameters=wg.ctx.parameters, increment=orm.Int(1000)
        ).result
        wg.ctx.done = result.variance_V >= target


initial_params = orm.Dict({**BASE_PARAMS, 'F': 0.040, 'n_steps': 1000})
wg_loop = extend_to_plateau.build(
    initial=initial_params,
    command=gsrd_code,
    target=0.012,
)
```

:::{dropdown} The same loop with a named predicate task
:icon: info

For a one-line `>=`, the operator-overload form above is concise and consistent with the rest of the module. If the stopping criterion were more involved (multi-line logic, a learned classifier, pattern detection on the V-field), wrapping it as a `@task()` makes the graph self-documenting and gives the predicate a meaningful name in the provenance:

```python
@task()
def reached_plateau(variance: float, target: float) -> bool:
    """Return True once variance(V) reaches the saturation target."""
    return float(variance) >= float(target)

# ... inside the While body:
done = reached_plateau(variance=parsed.variance_V, target=target)
wg.ctx.done = done.result
```

The graph looks the same except the `op_ge` task is replaced by a `reached_plateau` PyFunction. `@task()` is enough here because the predicate is stateless and the inputs are plain Python values (`float`, not `orm.Float`); `@calcfunction` would also work but persists every iteration's call as a `CalcFunctionNode`, which is overkill for a one-line check.
:::

The graph contains the loop body **once**, even though it will run several times: an `op_eq` task wraps the `wg.ctx.done == False` comparison and feeds the `while_zone`, whose body holds the `gray_scott_pipeline` sub-graph task, the `bump_n_steps` calcfunction, and the `op_ge` task that compares `variance_V` against `target`. The two write-back edges from inside the zone to `graph_ctx` (`op_ge.result → ctx.done` and `bump_n_steps.result → ctx.parameters`) are what closes the loop.

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show interactive workflow graph'
:    code_prompt_hide: 'Hide interactive workflow graph'

wg_loop
```

```{code-cell} ipython3
:tags: [hide-output]
:mystnb:
:    code_prompt_show: 'Show workflow execution log'
:    code_prompt_hide: 'Hide workflow execution log'

wg_loop.run()
```

```{code-cell} ipython3
print(f'Final state: {wg_loop.state}')
```

:::{important}
**Reassigning a Python variable inside a `While` body does *not* create a feedback edge.**
Writing `result = gray_scott_pipeline(...)` rebinds the *Python* name `result` but does not tell WorkGraph that the next iteration's `parameters` should come from somewhere different. The next iteration is *the same static sub-graph* re-executed, not a re-walking of the Python body.
For state that has to flow from one iteration to the next, **write it into `wg.ctx`** and read it back from `wg.ctx` at the top of the body.
That is what the two `wg.ctx.<name>` assignments inside `extend_to_plateau` are for: `parameters` carries the growing `n_steps` between iterations, and `done` carries the stopping signal.
:::

The provenance shows one `ShellJob` (and the surrounding calcfunctions) per iteration:

```{code-cell} ipython3
:tags: ["hide-input"]
:mystnb:
:    code_prompt_show: 'Show inspection code (recover per-iteration n_steps and variance)'

iterations = []
for parse_node in wg_loop.process.called_descendants:
    if parse_node.process_label != 'parse_output':
        continue
    sim_stdout = parse_node.inputs.stdout
    sim_node = sim_stdout.creator
    n_steps = sim_node.inputs.nodes.input.creator.inputs.parameters.get_dict()['n_steps']
    variance = float(parse_node.outputs.variance_V.value)
    iterations.append((sim_node.ctime, n_steps, variance))

iterations.sort()
print(f'{len(iterations)} gsrd runs nested under the workflow:\n')
for n, (_, n_steps, variance) in enumerate(iterations, start=1):
    print(f'  iter {n}: n_steps = {n_steps:5d}  variance(V) = {variance:.4e}')
```

:::{tip}
The condition only references ctx values that the **current** iteration is responsible for setting (`done`).
This is the cleanest shape for a `While` loop in WorkGraph: each iteration *only* writes the ctx keys it owns, and the condition reads keys whose value is fully determined by a single task in the current iteration.
A loop whose condition compares "this iteration vs. last iteration" needs the previous value to *outlive* the current iteration's writes, which requires more care (you have to route the previous value through the comparing task explicitly so the engine sees the read-before-write dependency).
:::

::::{dropdown} Why we don't loop over&nbsp;`dt`&nbsp;here
:icon: question

A natural alternative is **time-step convergence**: halve `dt` and double `n_steps` (keeping the simulated time `dt * n_steps` constant) until `variance(V)` stops changing.
That probes whether the integrator itself is converged, independent of how long you run the simulation.

For the tutorial's parameter regime (`F = 0.04`, `dt = 1.0`, etc.) the integrator is already converged at `dt = 1.0` to four significant figures, so a `While` loop on `dt` would terminate after a single iteration.
That makes for poor pedagogy: the loop reads as iterative but the data say it never had to be.
We chose `n_steps` (i.e., simulated time) because it *does* drift across iterations at our parameters, so the loop does real work and exits on a real saturation condition.

If your code has a tighter stability margin or your parameters sit near the numerical-stability limit for the time step (the "CFL condition" for explicit schemes; roughly, halving `dt` is required whenever the diffusion is faster or the grid is finer), the same `While`+`ctx` skeleton applies to `dt` unchanged; the only thing that moves is what `bump_n_steps` becomes.
::::

## `If` inside `Map`: per-iteration variable shape

Module 3's `gray_scott_sweep` ran the same three-step pipeline for every `F`: every iteration had the **same shape**.
What happens if we put an `If`-gated pipeline inside the `Map`?
Each iteration's internal shape is then decided **by that iteration's own data**: one run does the FFT, the next one does not, all from the same `param_sweep`.
The outer graph builds the loop body once; the engine fans it out at runtime, and the shape of each fan-out branch is independent.

```{code-cell} ipython3
from aiida_workgraph import Map, dynamic, namespace

from include.constants import F_VALUES


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
from include.tasks import identify_transition_region

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
