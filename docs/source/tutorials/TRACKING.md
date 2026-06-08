---
orphan: true
---

# Tutorial content tracking

Development-only checklist. Tracks what each module should teach and current status.

---

## Module 0: The running example

**Goal:** Introduce the simulation, run it without AiiDA, motivate why AiiDA is needed.

- [x] Introduce the reaction-diffusion simulation (what it does, show image)
- [x] Dropdown with model details (Gray-Scott name, U/V, F/k parameters)
- [x] Run the simulation via CLI, inspect YAML output
- [x] Run with different parameters (F=0.055), show different pattern (static image)
- [x] Show a failure (F=0.1, gsrd writes `ERR:` to stderr, always exits 0, no `results.npz`)
- [x] "What's missing?" section motivating AiiDA (no provenance, no record of failures, no versioning)
- [x] Surface gsrd-specific pain points (stdout-only scalars, hardcoded `results.npz`, banner noise, uninformative exit codes)
- [x] Frame AiiDA as "makes researchers' lives easier when dealing with scientific software", not just "high-throughput"
- [x] Switch tutorial code from raw `reaction-diffusion.py` to the `gsrd` package (https://github.com/aiidateam/gsrd)

---

## Module 1: Running with AiiDA

**Goal:** Set up AiiDA, run the same simulation through aiida-shell, inspect provenance.

- [x] Setting up an AiiDA profile (`verdi presto`)
- [x] Explain the setup cell (profile creation, `python_code` variable)
- [x] IPython magics note (`%run -i`, `%verdi`, `%load_ext aiida`)
- [x] Run simulation via `launch_shell_job` (aiida-shell)
- [x] Explain CalcJob lifecycle (upload, submit, retrieve, parse)
- [x] Explain Computer and Code concepts
- [x] Explore outputs (list output nodes, open YAML results file)
- [x] `verdi process show` and `verdi process list`
- [x] Provenance graph visualization
- [x] `verdi process dump` (export calculation data to disk)
- [x] `verdi shell` subsection added as a foldable dropdown (interactive database exploration: `load_node`, output traversal, QueryBuilder shorthand)
- [x] Raw `gsrd` stdout shown once via `print(node.outputs.stdout.get_content())` so the banner + progress lines are visible at least once. Later modules elide them but they are always captured in the stdout node.
- [ ] Handling failures section (re-run with F=0.1, show AiiDA records failed CalcJob, contrast with Module 0)

---

## Module 2: Structured data and calcfunctions

**Goal:** Move from opaque files to structured, queryable data. Introduce calcfunctions.

- [x] Parameter sweep with aiida-shell in a loop (file in, file out)
- [x] Show limitation: must manually open each YAML file to read results
- [x] Explain the idea: structured AiiDA data nodes (Dict, Float) vs opaque files
- [x] Explain ORM concept (tip box)
- [x] Write `prepare_input` calcfunction (Dict -> SinglefileData YAML)
- [x] Note on calcfunction arguments (AiiDA nodes, auto-serialization)
- [x] Write `parse_output` calcfunction (SinglefileData YAML -> Float nodes)
- [x] Note on calcfunction return types (single node vs dict)
- [x] Run the enriched pipeline (prepare_input -> ShellJob -> parse_output)
- [x] Provenance graph showing Dict in and Float out
- [x] Full parameter sweep with the enriched pipeline
- [x] Plot transition curve from structured AiiDA data
- [x] QueryBuilder teaser (tip box with example query)
- [x] `verdi process list`
- [x] Built-in data types table (Dict, Float, Int, Str, List, ArrayData, XyData, SinglefileData)
- [x] Extras subsection (attach arbitrary metadata to nodes for tagging/filtering)
- [x] Grouping results (collect sweep runs into an AiiDA Group, `verdi group list/show`)
- [x] Keep Groups + Extras + light QB teaser here, *before* Querying (per 2026-05-12 notes); scale benchmark (QB vs file I/O) moved to Module 5

---

## Module 3: Writing simple workflows

**Goal:** Wrap the pipeline into a WorkGraph workflow. Turn the for-loop into a Map sweep.

- [x] Why workflows? (no grouping, no hierarchy, no parallelism, no single entry point)
- [x] WorkGraph vs WorkChain note
- [x] WorkGraph mental model (WorkGraph, Task, Socket, Link)
- [x] Important note: calling a task inside a graph does not execute it
- [x] `@task.graph`, `shelljob()`, `spec` helpers explained
- [x] Map/If/While context managers mentioned
- [x] Wrap calcfunctions with `task()` and `spec.namespace`
- [x] Define `gray_scott_pipeline` as a `@task.graph`
- [x] Dropdown: declaring graph-level inputs/outputs explicitly
- [x] Dropdown: peeking inside the graph before running (build vs run, sockets)
- [x] Two ways to use a graph task (standalone vs sub-task)
- [x] Run single workflow, inspect with `verdi process status` and `verdi process show`
- [x] Provenance graph showing hierarchical structure
- [x] Map concept explained (source collection, item.key/value, gather)
- [x] Build param_sweep dict for Map
- [x] Run Map sweep (full F_VALUES range)
- [x] Notes on Map usage (dict keys, no dots, item.value is a socket)
- [x] Inspect sweep with `verdi process status` and `verdi process show`
- [x] Analyze results (print variances, plot transition curve)
- [x] Comparison table: AiiDA core concepts vs WorkGraph concepts
- [x] Control flow: dropped from M3, added link to Module 6 in Further Reading
- [x] `gray_scott_pipeline` promoted to `include/workflows.py` (canonical home), with M3 using `{literalinclude}` to display the source and `from include.workflows import gray_scott_pipeline` to bring it into the kernel. Pipeline now also exposes `results_npz` so Module 6 can read the V-field for the FFT diagnostic.
- [x] Interactive WorkGraph viz cells (`wg_preview`, `wg_sweep`) using bare-`wg` trailing expression + `nb_mime_priority_overrides` flip in `conf.py` so the self-contained Rete.js srcdoc iframe renders inline.
- [x] Closing 2D F&times;k phase-diagram section: 5&times;5 `Map`-over-Cartesian-product through the same `gray_scott_sweep`, rendered as a log-scale heatmap via `plot_2d_variance_heatmap` in `include/plotting.py`.
- [x] `wg_sweep.outputs.summary_plot.value` dereference now works against current aiida-workgraph; embedded transition curve PNG inline at the end of the sweep section (previously a `# TODO:` block).

---

## Module 4: Remote submission

**Goal:** Run on remote HPC clusters.

- [x] Setting up a remote Computer (SSH transport, scheduler)
- [x] Setting up a remote Code
- [x] Per-calculation scheduler options (resources / queue_name / account / max_wallclock_seconds) via `metadata.options`
- [x] Monitoring remote jobs (`verdi process show`)
- [x] Mention `aiida-resource-registry` as tip (link to repo, reference PR #7378 for YAML support)
- [x] Also show a typical manual InstalledCode (with `prepend-text` / `module load`)
- [x] Computer-level `prepend_text` / `append_text` tip (vs per-code `--prepend-text`)
- [x] `verdi code test` after `verdi code create` (executable-exists check)
- [x] Multi-computers-per-profile prose: profiles are not tied to a single cluster
- [x] Production-rate-limit warning: tutorial uses aggressive `--safe-interval 0` + `set_minimum_job_poll_interval(1)`; real clusters need 30s+
- [x] Mention the three code types: InstalledCode / PortableCode / ContainerizedCode (inline bold list)
- [x] DECIDED: use `xenonmiddleware/slurm:17` container for live executable cells; illustrative `daint` examples for realistic cluster setup
- [x] CI plumbing: slurm service in `docs-build.yml`, gsrd installed on container via `uv`
- [x] `setup_slurm.py` hidden cell: SSH config, computer/code registration via Python API
- [x] `core.ssh_async` transport (note vs `core.ssh`)
- [ ] Forward-looking only: `verdi computer/code search` endpoint (JG WIP, open PR, unreleased — mention, don't demo)
- [ ] Mention `aiida-code-registry` vs `aiida-resource-registry` (JG view: should be merged)

---

## Module 5: Querying and analysis

**Goal:** Use QueryBuilder for searching and analyzing provenance.

- [x] QueryBuilder basics (append, filters, project)
- [x] Filtering by node type, attributes, extras
- [x] Traversing relationships (inputs, outputs, ancestors, descendants, with_group)
- [x] Aggregation note: rolled into the basics tip ("after projection it is just Python on a list") instead of a dedicated section, since the JG-confirmed Python-side aggregation reduces to stdlib `min`/`max`/`statistics.mean` with no AiiDA-native angle
- [x] Exporting and sharing results (AiiDA archive; pointer to `verdi archive create` + `how-to:share`)
- [x] Benchmark/speed: result retrieval at scale, QueryBuilder vs file I/O (live `time.perf_counter()` comparison on the existing F-sweep)
- [x] Final payoff cell: rebuild the Module 2 transition curve purely from QueryBuilder, no `enriched_results` list

---

## Module 6: Complex workflows

**Goal:** Conditional logic, nested sub-workflows, dynamic construction.

- [x] `If` zone (conditional FFT analysis gated on `variance_V`)
- [x] `While` zone with `wg.ctx` for iterative state (extend `n_steps` until saturation), plus dropdown on `dt`-convergence vs `tmax`-convergence
- [x] Nested sub-workflows (`@task.graph()` composition: `pipeline_with_optional_fft` inside `conditional_sweep`; all three featured graphs reuse the shared `gray_scott_pipeline` from `include/workflows.py`)
- [x] Dynamic workflow construction (`identify_transition_region` builds the refined `Map` source at runtime)
- [x] Error handlers moved to Module 7 (depends on Module 1 "Handling failures" being filled in first; the gsrd CLI's always-exit-0 behaviour also makes the standalone error-handler example contrived without a custom shell parser, see notes)
- [x] `help(If)`, `help(While)`, `help(Map)` signature cells at first introduction of each control-flow region (foldable behind a "Show signature" toggle).
- [x] Interactive WorkGraph viz cells after every substantial graph definition (`pipeline_with_optional_fft`, `extend_to_plateau`, `conditional_sweep`, `adaptive_sweep`), each with a one-sentence prose hint pointing at the specific tasks/edges to look for.
- [x] `:::{important}` admonition on `wg.ctx`: explains *why* it exists (only channel for state across `While` iterations, since the loop body is a static sub-graph) and flags the type-safety gap honestly (same complaint people have raised about WorkChain `ctx`).
- [x] `:::{note}` admonition on `get_current_graph()`: explains the `ContextVar`-based "ambient graph" pattern (Flask `current_app`-style dynamic scoping).
- [x] FFT diagnostic plot (`plot_fft_spectrum` in `include/plotting.py`): 2D power spectrum + radial profile, called right after the descendants-diff cell so the reader can *see* what the `If`-gated FFT recovered.

---

## Module 7: Where to go next

**Goal:** Survey module &mdash; error handling, CalcJob plugins, WorkChains, caching, plugin ecosystem.

- [x] Module retitled "Where to go next" (was "Error handling"); broadened scope per the M7 plan in `_notes/module7-plan.md`
- [x] Error handling section: synthetic `gsrd` failure (`dt = 10.0` &rarr; numerical instability &rarr; missing `results.npz` &rarr; ShellJob exit 303), WorkGraph error handler (`add_error_handler`) that halves `dt` and rebuilds the YAML input as a fresh `SinglefileData`, ShellJob retries and succeeds. Both attempts visible in provenance.
- [x] "When to write an error handler &mdash; and when not to" dropdown (transient/recoverable vs hard programmer errors)
- [x] WorkChain `@process_handler` callout pointing at `BaseRestartWorkChain` and `how-to:restart-workchain`
- [x] CalcJob plugin section: motivation, sketch of `GsrdCalculation` subclass (`define`, `prepare_for_submission`, exit codes), entry-point wiring snippet, pointer to `how-to:plugin-codes` and `aiida-plugin-cutter`
- [x] "How to choose &mdash; `aiida-shell` vs a CalcJob plugin" dropdown
- [x] WorkChain side-by-side section: `MultiplyAddWorkChain` via `{literalinclude}` of `src/aiida/workflows/arithmetic/multiply_add.py`, comparison table (mental model, state passing, dynamic graphs, ecosystem, when to pick which)
- [x] Caching section: single-ShellJob demo (`enable_caching` context manager, `node.base.caching.get_cache_source()`, `verdi process list -P pk process_label exit_status cached_from`), plus a sweep cache demo on `gray_scott_sweep` showing ~Nx speedup on the second run
- [x] "Local vs daemon caching" important admonition (`enable_caching` only affects local interpreter; `verdi config set caching.default_enabled True` for the daemon)
- [x] "Caveats &mdash; what gets cached" dropdown (plugin author marking hashable inputs, `_aiida_hash`, `_hash_ignored_inputs`)
- [x] Plugin ecosystem 8-card grid: aiida-project, aiida-hyperqueue, aiida-workgraph, aiida-shell, aiida-submission-controller, aiida-code-registry, AiiDAlab, domain plugins
- [x] "Where to go next" closing pointers: write a CalcJob plugin, write a parser, try a domain plugin, browse the registry, AiiDA Discourse, CONTRIBUTING.md
- [x] `tutorials/index.md` M7 card updated: title "Where to go next", description rewritten, button now active (was "Coming soon")
- [ ] Optional: synthetic-failure section currently uses `dt = 10.0` instability; could also demo a walltime-style recovery once M4-style remote runs are reachable from the tutorial profile

---

## Cross-cutting concerns (not module-specific)

- [ ] Teaser page (AiiDA in Action demo, currently commented out in index)
- [x] Shared include files: `constants.py`, `tasks.py`, `setup_tutorial.py`, `workflows.py` (custom `reaction-diffusion.py` replaced by the `gsrd` package, a docs dep in `pyproject.toml` `[project.optional-dependencies.tutorials]`)
- [x] Shared plot helpers: `plotting.py` (`plot_provenance`, `plot_transition_curve`, `plot_uv_fields`, `plot_2d_variance_heatmap`, `plot_fft_spectrum`)
- [x] Shared workflows: `workflows.py` (`gray_scott_pipeline` with `GrayScottOutputs` TypedDict exposing `variance_V`, `mean_V`, `results_npz` so M6 can reuse the same pipeline)
- [x] **gsrd** package: removed the `TrivialStateError` post-hoc quality gate (`simulate.py` no longer raises when V decays to the trivial state), so dead-zone `(F, k)` combinations now report `variance(V) ≈ 0` instead of failing the ShellJob. This unblocks the M3 2D phase-diagram sweep without needing error handling. Other failure modes (`DiffusionError`, `TimeStepError`, `InstabilityError`) intact &mdash; still material for M7.
- [x] Static images: `reaction-diffusion-fields.png`, `reaction-diffusion-fields-2.png`
- [x] Sphinx `-W` admonition cleanup: converted `:::{tip}/:note: <title> :class: dropdown` into plain `:::{dropdown} <title> :icon: info` across M1, M6, M7. The sphinx-design renderer treats the former as "splitting content across first line and body with options", which becomes a hard error under `-W`. Affected lines were M1:261, M6:60, M6:344, plus the five new admonitions in M7.
- [ ] Compare the new modules against the classic tutorial (`basic.md`); check nothing important was dropped (per 2026-05-12 notes)
