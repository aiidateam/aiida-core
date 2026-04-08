# Tutorial Meeting Notes — 2026-03-30

## Timeline & People

- Mbx here until end of June; Alex away May & June, then 4 more months
- Alternatively, fall (EB preference)
- **Goal**: story line fixed by end of April
- **Coding week**: by then, have the story line ready
- Possibly another coding week end of May / begin of June
- Invite specific people where it makes sense

## Agreed Module Layout

### Module 0: The Running Example
- Current "Introduction" absorbed here
- Run the script once directly (no AiiDA)
- Keep it to the minimum: only required inputs shown
- Show what's missing without a management layer

### Module 1: Running with AiiDA
- `aiida-shell` for running the simulation
- Basic AiiDA benefits: `verdi process list`, provenance graph, `verdi process dump`
- Handling failures (exit codes)
- No calcfunctions, no parsing, no submit/run distinction yet

### Module 2: Interacting with Data
- **Part A**: Parameter sweep with `aiida-shell` in a for-loop
  - File in -> ShellJob -> file out (only `SinglefileData`)
  - Plot transition curve from extracted results
  - Show limitation: can't query inside files
- **Part B**: Richer provenance with calcfunctions
  - `prepare_input`: `Dict` -> `SinglefileData` (YAML)
  - `parse_output`: `SinglefileData` (.npz) -> `Float`, `Float`
  - Full pipeline: prepare -> ShellJob -> parse
  - Re-run sweep with structured, queryable data
  - Input as `Dict` in database, outputs as `Float` in database

### Module 3: Writing Simple Workflows
- **Part 1**: Wrap the Module 2 pipeline (prepare + simulate + parse) as a single WorkGraph
  - Show hierarchical provenance vs. flat
- **Part 2**: Wrap the for-loop as a workflow (Map)
  - Single "sweep" workflow node containing all runs
- Branching teaser (If control flow)

### Modules 4–7: Future (Coming Soon)
- Error handling & debugging (exit codes, error handlers, retries)
- Remote HPC submission (`submit()` vs `run()`, daemon, SSH computers)
- Querying & organizing data (QueryBuilder, Groups, archives)
- Advanced topics (multi-param sweeps, WorkGraph vs WorkChain, FFT analysis)

## TODOs

### Tutorial Content
- [ ] Finalize Module 0 content (runs correctly in Sphinx build)
- [ ] Finalize Module 1 content (add `verdi process dump` section, runs correctly)
- [ ] Finalize Module 2 Part A (aiida-shell sweep, runs correctly)
- [ ] Finalize Module 2 Part B (calcfunctions, runs correctly)
- [ ] Write Module 3 Part 1 with working WorkGraph code (needs testing against aiida-workgraph)
- [ ] Write Module 3 Part 2 with Map (depends on aiida-workgraph Map API stability)
- [ ] Test full Sphinx build with all modules (no warnings, no broken refs)
- [ ] Test notebook execution for Modules 0–2

### Teaser / Landing Page
- [ ] Decide: use "highlights" from new website as teaser, or keep current teaser module?
- [ ] Show WorkGraph code in teaser?
- [ ] Currently commented out in index.md — finalize and re-enable
- [ ] Add GIFs to intro/teaser?

### Infrastructure / Packaging
- [ ] `pip install aiida` metapackage — does it exist? Talk to Alex, possibly Ali
- [ ] Revisit cookiecutter
- [ ] Comparison table between core concepts and WorkGraph concepts (CalcJob/WorkChain vs. WorkGraph process nodes)

### WorkGraph Integration
- [ ] Verify `@task` vs `@calcfunction` decorator story (two decorators vs `@task.calcfunction`)
- [ ] Verify archive exporting with WorkGraph processes (link rules, instance checks for WorkChain/CalcJob may miss WorkGraph)
- [ ] Verify WorkGraph behavior in Jupyter notebooks
- [ ] WG CLI integration: `task pause/play/kill/list` — integrate into core?
- [ ] WG submission model: drop `run`/`submit` distinction? Also `build`?

### AiiDA Core
- [ ] No RMQ broker not blocking — doesn't change tutorial story line
- [ ] RestAPI not a target for tutorial (separate module; consumer is the GUI)
- [ ] GUI — slightly higher priority than TUI
- [ ] `verdi init` — git-like behavior
- [ ] `verdi workchain` command? (low priority; currently `verdi process` and `verdi calcjob`)

## Other Top-Level Topics (Not Yet in Tutorial)

These were discussed as potential future content beyond the current Modules 0–7:

- Submit / daemon mechanics
- HPC remote execution
- Custom CalcJob plugins & parsing
- Base restart WorkChain (at least as concept)
- Advanced workflows (If, While control flow)
- Advanced querying (QueryBuilder joins, projections)
- AiiDAlab integration
- Materials science applications
- Short videos: Relax, PDOS, Ph, Vmin, etc.

## Raw Handwritten Notes (Transcribed)

### Page 1
- WG CLI: task pause/play/kill/list — integrate into core?
- Intro: required vs not required; add GIFs; keep to minimum
- Merge Mod 0 and 1 (done: current intro + run once = Module 0)
- Mod 1: DB drop; verdi shell; verdi diff
- Mod 0: (current) intro + run once; groups, AiiDA manages your FS; verdi dump; benefits: process list, dump, provenance
- Mod 2: parsing + basic data interaction; for-loop parameter sweep; group; retrieve files from loop; do manual parsing -> THEN show how to do parsing directly in AiiDA; input as Dict, calcfunction to write file, calcfunction to read npz and fetch data

### Page 2
- 2A: basic data types, SinglefileData
- 2A: filters & 2D data types beyond files
- 2B: show speed impact (benchmark?)
- 3: end of Mod 2 deliverable is the transition plot
- 3: single WFs -> linear (for loop); basically Mod 2 as a single process; then wrap also the for-loop as a single process; then branching
