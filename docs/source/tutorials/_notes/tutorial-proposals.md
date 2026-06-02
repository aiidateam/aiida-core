# Tutorial module structure — proposals

## Side-by-side module comparison

| # | Proposal A (hackmd) | Proposal B (brainstorming) | Difference |
|---|---|---|---|
| Teaser | Full pipeline demo | Same | **None** |
| 1 | **calcfunction**, store data, verdi, provenance | **Run pre-built workflow**, verdi, provenance | **Significant**: write-first vs run-first |
| 2 | **External codes** (aiida-shell, CalcJob) | **calcfunction**, store data, verdi | **Reordered**: A does external codes early, B does calcfunction |
| 3 | **Parsing** (exit codes, parser, outputs) | **External codes** (aiida-shell, CalcJob) | **Reordered + merged**: A has a dedicated parsing module |
| 4 | **Data types** (ArrayData, Float, Dict) | **All data** (types + QueryBuilder + Groups + export) | **Significant**: A covers only types; B consolidates all data interaction |
| 5 | **Workflows** (WorkGraph) | **Workflows** (WorkGraph) | **None** |
| 6 | **Error handling** (handlers, debugging) | **Error handling** (handlers, debugging) | **None** |
| 7 | **High-throughput** + QueryBuilder + Groups | **High-throughput** + post-processing | **Minor**: A puts querying here; B already covered it in Module 4 |
| 8 | **Post-processing** + archives | **Advanced** (optional: daemon, remote, FFT) | **Minor**: A's post-processing can fold into 7 |

## What actually differs significantly

Only **three** things need a decision:

### 1. Entry point (Module 1): write or run first?

- **A**: Users write a `@calcfunction` in Module 1.
- **B**: Users run a pre-built workflow in Module 1, write their own later.
- **Resolution**: The **teaser** already serves the "run first" role. If the teaser shows the full pipeline, Module 1 can start with writing a calcfunction — users have already seen the end goal. This avoids needing a pre-built entry-point workflow (which doesn't exist yet).

### 2. Parsing: dedicated module or folded in?

- **A**: Module 3 is entirely about parsing and exit codes.
- **B**: Parsing is part of the external codes module.
- **Resolution**: Parsing is tightly coupled to CalcJobs — you write a parser *because* an external code produced output files. Folding parsing into the external codes module makes the narrative tighter: "run external code → get output files → parse them." One module instead of two.

### 3. Data management: split or consolidated?

- **A**: Data types in Module 4, querying in Module 7, archives in Module 8.
- **B**: All data interaction (types, querying, groups, export) in one module.
- **Resolution**: Consolidated is better. Users need to understand the full data picture in one place: what types exist, how to find data, how to organize it, how to export it.

## Merged proposal

Combines both, taking the best of each:

### Teaser: AiiDA in Action
- Full pipeline demo (parameter sweep → patterns → provenance → plots)
- Light on code, heavy on visual output
- Gray-Scott model explained briefly (dropdown for details)
- "By the end, you'll build this yourself"

### Module 1: Running Python code in AiiDA
- Profile setup (`verdi presto`)
- Storing data as nodes (`Dict`, `Float`)
- `@calcfunction` decorator
- `verdi process list`, `verdi process show`, `verdi node show`
- Provenance graph visualization
- *From A's Module 1*

### Module 2: Running external codes
- `aiida-shell` / `ShellJob` to run `reaction-diffusion.py`
- Computer & Code setup
- CalcJob concept (input files → scheduler → output files)
- `verdi calcjob inputcat / outputcat`
- **Parsing**: exit codes, writing a parser, structured outputs
- *Merges A's Modules 2+3*

### Module 3: Working with your data
- Data types: `ArrayData`, `Float`, `Dict`, visualization
- QueryBuilder: find, filter, project
- Groups for organizing runs
- `verdi process dump`
- Exporting `.aiida` archives
- *B's consolidated Module 4*

### Module 4: Building workflows
- WorkGraph basics
- Chaining calculations (simulate → parse → post-process)
- Context variables for data flow
- Simple branching
- *Same in both proposals*

### Module 5: Error handling & debugging
- `verdi process report`, `verdi process dump`
- Inspecting failed jobs (exit codes, stderr)
- Error handlers (retry with adjusted parameters)
- Re-submission strategies
- *Same in both proposals*

### Module 6: High-throughput & post-processing
- Parameter sweeps over F (loops in WorkGraph)
- Collecting and analyzing results across runs
- Variance vs F, mean vs F plots
- Representative pattern gallery
- *Merges A's Modules 7+8*

### Module 7: Advanced topics (optional)
- Multi-parameter sweeps (F × k phase diagram)
- Remote HPC execution
- Daemon (`submit()` vs `run()`)
- FFT analysis, dashboards
- *B's Module 8*
