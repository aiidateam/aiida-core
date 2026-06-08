# Module 6 plan &mdash; Complex workflows

Living plan for Module 6. Edit freely; the agent picks up from this file after compact and starts writing the module against the storyline below.

## What the reader already has at the start of Module 6

Modules 1-3 built the WorkGraph foundation:

- `@task` and `@task.graph()` decorators (Module 3).
- A working `gray_scott_pipeline` graph task with three steps (`prepare_input` &rarr; `ShellJob` &rarr; `parse_output`).
- A `gray_scott_sweep` graph task using `Map` over `param_sweep`, ending in a `make_transition_plot` reduction.
- All the gsrd helpers in `include/tasks.py`.

Module 6 is independent of Modules 4 and 5. The reader may or may not have done QueryBuilder / remote submission first. Stay self-contained.

## What Module 6 adds, in one sentence

Module 3's workflows had **fixed shape**: the graph was the same every run.
Module 6 shows how to build workflows that **decide their own shape at runtime**: skip steps conditionally, iterate until converged, nest sub-workflows, and construct parts of the graph from intermediate results.

## Storyline (proposed spine &mdash; edit me)

1. **Why fixed-shape isn't enough.** Recall Module 3's sweep: every F got the same three-step pipeline. Real research is adaptive: skip cheap analysis when the cheap pre-check fails, iterate until convergence, refine where it matters. The WorkGraph features for this are *zone tasks*: `If`, `While`, `Map` (already seen), all context managers in the graph builder.
2. **`If` zones: skip expensive steps conditionally.** A cheap predicate decides whether the expensive branch runs. Example: only compute an expensive analysis (FFT / variance-spectrum / whatever) if a cheap pre-check identifies the run as "interesting" (e.g., variance above a threshold).
3. **`While` zones: iterate until converged.** Example: run gsrd at successively smaller dt until variance_V stabilises to a tolerance. Builds the convergence-check task on the fly.
4. **Composing sub-workflows with `@task.graph()`.** Reuse a `@task.graph()` (already met in Module 3) as a single task inside another graph. Example: wrap "run + parse + converge-check" into a sub-graph called once per dt step.
5. **Dynamic construction from intermediate results.** Build the param-set or task-set programmatically before `Map` consumes it, using normal Python and a calcfunction to keep provenance. Example: from a coarse F-sweep, identify the transition region and generate a refined sweep around it.
6. **Putting it together: an adaptive workflow.** One end-to-end workflow that uses two of the above features at once. Likely: coarse sweep &rarr; identify transition &rarr; refined sweep (with `Map` over the dynamic param set).
7. **Next steps + Further reading.**

## Tone & format

- Same shape as Modules 1-5: surface a pain point inline, then the WorkGraph feature, then build up.
- Live executable cells throughout. The setup cell at the top should reuse `include/setup_tutorial.py` like other modules.
- Semantic linebreaks (one sentence per line, applied via `_notes/semantic_linebreaks.py`).
- No em-dashes.
- Admonitions: `note` blue for definitions, `tip` green for optional improvements, `important` orange for *one* central abstraction message. Candidate central message: "the workflow graph is data that you build; once you accept that, control flow is just normal Python that *adds tasks*, gated by other tasks' outputs."
- Hide non-AiiDA bookkeeping behind `hide-cell` with descriptive `code_prompt_show` labels (same convention as Module 5's scale-argument cells).

## Coverage to surface from TRACKING.md

- [ ] If/While context managers (zone tasks).
- [ ] Nested sub-workflows (`@task.graph()` as a task inside another graph).
- [ ] Dynamic workflow construction (param set built from intermediate results).
- [ ] Error handlers within workflows.

The fourth bullet (error handlers) overlaps with Module 7's scope (Error handling). Decision needed below.

## Open judgment calls (please decide before I start)

### 1. Motivating example for `While`

Two natural candidates:

- **`dt` convergence**: run gsrd at successively smaller dt until variance_V stabilises. Plays into the physical-science motivation but **only works if gsrd is actually dt-sensitive at the values we use**; needs to be verified before writing (see "Things to verify" below). If gsrd is dt-insensitive at typical settings we'd be staging a fake convergence, which is bad pedagogy.
- **Convergence over wall-clock budget**: run gsrd for longer simulated times (`tmax`) until the variance change between successive runs falls below a tolerance. Mechanically same `While` shape, definitely converges (longer simulation &rarr; more pattern coarsening), no dt-physics gamble.

> JG: add code for both. then we'll see how it plays out, and decide. if need be, check the gsrd source code, and find something that's physically meaningful and works in the context we want

### 2. Motivating example for `If`

The cleanest framing is **"skip an expensive task conditionally"**. Options for the expensive task:

- **FFT-based pattern wavelength**: do an FFT on the V-field snapshot, extract a peak wavelength. Genuinely useful diagnostic, requires `numpy.fft` and `SinglefileData` access. Adds extra-files dependency on the gsrd output (V-field), but we already use `results.npz`.
- **High-resolution rerun**: only re-run gsrd at higher spatial resolution if the low-res run shows patterning. Simpler conceptually but doubles the gsrd cells.
- **Pure synthetic**: a calcfunction that takes a second to run on purpose, with a passing comment. Honest about being a demo but doesn't add real-science content.

> JG: same as before. implement option 1 (sounds promising indeed!), but let's also see what happens with option 2

### 3. Where do error handlers live?

The current TRACKING line "Error handlers within workflows" is bulleted under Module 6, but Module 7's whole point is error handling. Two options:

- **All error handling stays in Module 7** (current chapter scope). Drop the bullet from Module 6's TRACKING.
- **WorkGraph-style handlers (via `ErrorHandlerSpec`) live in Module 6**, since they're a *control-flow* feature of WorkGraph, and Module 7 then focuses on the WorkChain-style `@process_handler` API plus end-to-end retry strategies. This is what `_notes/api-discrepancies.md` line 142 originally proposed.

> JG: <please decide; my instinct: option 2 (WG handlers here, WC handlers in M7), aligns with the API-discrepancies plan and gives M6 a fourth feature> -> agreed!

### 4. Closing example

Module 5 closed with a satisfying payoff (rebuild the M2 plot from QB alone). Module 6 candidates:

- **Adaptive sweep**: coarse F sweep &rarr; find transition &rarr; refined sweep with `Map` over a dynamic param set. Uses dynamic construction (5) and `Map` (recap from M3); doesn't need `If` or `While` for the closing flourish.
- **Iterative refinement of a single F**: pick F = transition midpoint, While-converge tmax, return final variance_V. Uses `While` (3) and `@task.graph()` nesting (4).
- **Both** in one big graph: coarse sweep, refined sweep, with While-convergence at each refined point. End-to-end but heavy.

> JG: <please decide; my instinct: option 1 (adaptive sweep) as the close, since it's visually striking (the refined-region plot) and reuses the M3 `gray_scott_sweep` pattern> -> could we also add the FFT on top? then it would really be a workflow that's comparable to real-world workflows!

## Things to verify before writing

- gsrd's actual dt sensitivity at the values we use (only matters if we pick Option 1 of judgment call #1).
- Whether gsrd's `results.npz` exposes the V-field (needed for Option 1 of judgment call #2). Check `include/tasks.py` and the gsrd repo.
- aiida-workgraph nested-zone behaviour: can `If` go inside `Map`? Can `While` contain a `@task.graph()`? Build a tiny scratch graph and verify before committing to nested examples.
- `aiida-workgraph` version pinned in `pyproject.toml` actually exposes the `If` / `While` zone tasks at the same import path as `Map` (`from aiida_workgraph import If, While, Map`).
- `ErrorHandlerSpec` import path and signature (only if judgment call #3 lands on option 2).
- Existing anchors to use in "Further reading": `topics:workflows`, `topics:workflows:concepts`, and any aiida-workgraph docs anchors for If/While/error-handlers.

## Files to create / modify

- `docs/source/tutorials/module6.md`: replace the stub with the full module.
- `docs/source/tutorials/TRACKING.md`: tick off the items listed under Module 6 as they land. Possibly move "Error handlers within workflows" depending on judgment call #3.
- `docs/source/tutorials/index.md`: once Module 6 is functional, swap its `*Coming soon*` card for a `button-ref` (matching Module 4 / Module 5).
- `docs/source/tutorials/include/tasks.py`: add any new task definitions (FFT analysis, convergence check, transition finder) once judgment calls land.

## Out of scope (explicitly)

- WorkChain-style API (`while_()`, `if_()`, `@process_handler`). That's Module 7's territory unless judgment call #3 says otherwise.
- Multi-parameter (F &times; k) phase diagrams. Mentioned in the boss notes as "advanced topics" but a clean adaptive single-parameter story already exercises every feature this module needs.
> JG: could be something we at least show somewhere once, though, no? As the 2D plot, would be nice, and not as boring as a single sweep!
>
> CC: Agreed it's visually nicer. I left it out of M6 because mechanically a 2D phase diagram is just `Map`-of-`Map` (or one `Map` over the Cartesian product), which doesn't really demonstrate a new M6 feature; M3 introduces `Map`, so the cleanest place to slot it is *as an extension of M3*, not M6. Cost is real though: 8 F &times; 8 k = 64 gsrd runs (~2 min in CI at `n_steps=3000`). My instinct: leave it for now, drop the 2D plot into the *teaser* page (the commented-out `AiiDA in Action` card on `tutorials/index.md`) where it earns its keep visually rather than pedagogically. Happy to add it to M3 instead if you'd rather, let me know.
- Remote submission. The module assumes local execution; the `metadata.options` story for remote belongs to Module 4
> JG: yes, run locally here, keep remote to module 4
>
> CC: Confirmed, kept local. Done.
- Heavy theory of dataflow / Petri nets / process algebras. Keep the framing operational.
> JG: wtf is that?
>
> CC: Just pre-emptively heading off a rabbit hole &mdash; a WorkGraph is, in CS theory, a "dataflow graph" (computations as nodes, values as edges), and the same idea has been formalised under names like Petri nets and process algebras. Pure trivia for the tutorial's audience. Dropped from anything reader-facing; left this bullet in the plan only because the boss notes mentioned the keywords.

## Notes pulled in from elsewhere

- `_notes/api-discrepancies.md` lines 145-154 (item 5): WorkGraph If/While are zone tasks, conditions are *task output sockets* not Python booleans. Worth a `:::{note}` or inline aside the first time `If(condition_socket)` appears.
- `_notes/2026-03-30-notes-cleaned.md` lines 42, 95: boss notes flag "branching teaser (If control flow)" and "Advanced workflows (If, While control flow)" as the M6 scope. Stays consistent with current direction.
