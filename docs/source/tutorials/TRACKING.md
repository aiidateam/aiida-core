# Tutorial content tracking

Development-only checklist. Tracks what each module should teach and current status.

---

## Module 0: The running example

**Goal:** Introduce the simulation, run it without AiiDA, motivate why AiiDA is needed.

- [x] Introduce the reaction-diffusion simulation (what it does, show image)
- [x] Dropdown with model details (Gray-Scott name, U/V, F/k parameters)
- [x] Run the simulation via CLI, inspect YAML output
- [x] Run with different parameters (F=0.055), show different pattern (static image)
- [x] Show a failure (F=0.1, exit code 30, no output file)
- [x] "What's missing?" section motivating AiiDA (no provenance, no record of failures, no versioning)
- [ ] Consider packaging simulation as a CLI tool (`gsrd`) instead of a raw Python script (deferred)

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
- [ ] `verdi shell` subsection (interactive database exploration)
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
- [ ] Built-in data types table (Dict, Float, Int, Str, List, ArrayData, XyData, SinglefileData)
- [ ] Extras subsection (attach arbitrary metadata to nodes for tagging/filtering)
- [ ] Grouping results (collect sweep runs into an AiiDA Group, `verdi group list/show`)
- [ ] Benchmark/speed note on result retrieval at scale (QueryBuilder vs file I/O)

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
- [ ] Comparison table: AiiDA core concepts vs WorkGraph concepts
- [ ] Control flow: If/While examples (deferred to future modules)

---

## Module 4: Complex workflows (coming soon)

**Goal:** Conditional logic, nested sub-workflows, dynamic construction.

- [ ] If/While context managers
- [ ] Nested sub-workflows
- [ ] Dynamic workflow construction
- [ ] Error handlers within workflows

---

## Module 5: Remote submission (coming soon)

**Goal:** Run on remote HPC clusters.

- [ ] Setting up a remote Computer (SSH transport, scheduler)
- [ ] Setting up a remote Code
- [ ] Queue management and job scheduling
- [ ] Monitoring remote jobs (`verdi process list`, `verdi process watch`)

---

## Module 6: Querying and analysis (coming soon)

**Goal:** Use QueryBuilder for searching and analyzing provenance.

- [ ] QueryBuilder basics (append, filters, project)
- [ ] Filtering by node type, attributes, extras
- [ ] Traversing relationships (inputs, outputs, ancestors, descendants)
- [ ] Aggregation and statistics
- [ ] Exporting and sharing results (AiiDA archive)

---

## Module 7: Error handling (coming soon)

**Goal:** Exit code checking, error handlers, automatic retries.

- [ ] Exit codes and how AiiDA uses them
- [ ] Defining error handlers
- [ ] Automatic retries with modified inputs
- [ ] Combining error handling with workflows

---

## Cross-cutting concerns (not module-specific)

- [ ] Teaser page (AiiDA in Action demo, currently commented out in index)
- [x] Shared include files: `constants.py`, `tasks.py`, `setup_tutorial.py`, `reaction-diffusion.py`
- [x] Shared plot helpers: `plot_provenance.py`, `plot_sweep.py`, `plot_fields.py`
- [x] Static images: `reaction-diffusion-fields.png`, `reaction-diffusion-fields-2.png`
