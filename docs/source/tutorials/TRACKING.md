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
- [ ] Keep Groups + Extras + light QB teaser here, *before* Querying (per 2026-05-12 notes); scale benchmark (QB vs file I/O) moved to Module 5

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

## Module 4: Remote submission (coming soon)

**Goal:** Run on remote HPC clusters.

- [ ] Setting up a remote Computer (SSH transport, scheduler)
- [ ] Setting up a remote Code
- [ ] Queue management and job scheduling
- [ ] Monitoring remote jobs (`verdi process list`, `verdi process watch`)
- [ ] Set up Computer + Code from a real `aiida-resource-registry` CSCS YAML (`include/computer-cscs.yaml`, `include/code-cscs.yaml`) via `verdi computer/code ... --config`
- [ ] BLOCKER: resource-registry YAMLs carry AiiDAlab metadata that breaks `verdi computer setup --config` in aiida-core (JG has open PR); ship hand-cleaned copies until merged
- [ ] Mention `aiida-code-registry` vs `aiida-resource-registry` (JG view: should be merged)
- [ ] Forward-looking only: `verdi computer/code search` endpoint (JG WIP, open PR, unreleased — mention, don't demo)
- [ ] Also show a typical manual InstalledCode (with prepend/append `module load`)
- [ ] Mention the three code types: InstalledCode / PortableCode / ContainerizedCode
- [ ] DECIDE (before implementing): replace invented host with the real `xenonmiddleware/slurm` container (aiida-core CI's own target; configs already in `.github/config/slurm-ssh*.yaml`). Trade-off: requires Docker vs. "keep it simple"; leaning toward optional "run it for real" dropdown

---

## Module 5: Querying and analysis (coming soon)

**Goal:** Use QueryBuilder for searching and analyzing provenance.

- [ ] QueryBuilder basics (append, filters, project)
- [ ] Filtering by node type, attributes, extras
- [ ] Traversing relationships (inputs, outputs, ancestors, descendants)
- [ ] Aggregation and statistics
- [ ] Exporting and sharing results (AiiDA archive)
- [ ] Benchmark/speed: result retrieval at scale, QueryBuilder vs file I/O (per 2026-05-12 notes; only a light teaser in Module 2)

---

## Module 6: Complex workflows (coming soon)

**Goal:** Conditional logic, nested sub-workflows, dynamic construction.

- [ ] If/While context managers
- [ ] Nested sub-workflows
- [ ] Dynamic workflow construction
- [ ] Error handlers within workflows

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
- [x] Shared include files: `constants.py`, `tasks.py`, `setup_tutorial.py` (custom `reaction-diffusion.py` replaced by the `gsrd` package, a docs dep in `pyproject.toml` `[project.optional-dependencies.tutorials]`)
- [x] Shared plot helpers: `plotting.py` (`plot_provenance`, `plot_transition_curve`, `plot_uv_fields`)
- [x] Static images: `reaction-diffusion-fields.png`, `reaction-diffusion-fields-2.png`
- [ ] Compare the new modules against the classic tutorial (`basic.md`); check nothing important was dropped (per 2026-05-12 notes)
