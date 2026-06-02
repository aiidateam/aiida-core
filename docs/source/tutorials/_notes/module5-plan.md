# Module 5 plan — Querying and analysis (`QueryBuilder`)

Living plan for Module 5. Edit freely; the agent picks up from this file after compact and starts writing the module against the storyline below.

## What the reader already has at the start of Module 5

Across Modules 1–4 the tutorial profile has accumulated:

- Many `CalcJobNode` / `ShellJob` instances from the F-sweep (Modules 1, 2).
- `CalcFunctionNode` instances from `prepare_input` and `parse_output` (Module 2).
- `Float` and `Dict` nodes — structured outputs of the sweep (Module 2).
- `Group` `tutorial/F-sweep` holding the sweep `CalcJob` nodes (Module 2).
- Extras `F`, `sweep='F_scan'` on each `parse_output` calcfunction node (Module 2).
- A `WorkChainNode` (the WorkGraph) plus its child workflow + task processes (Module 3).
- One `CalcJob` on the remote `slurm-ssh` Computer (Module 4) with its `RemoteData`.

Module 5 should exercise QueryBuilder against this real, populated provenance, not toy data.

## Storyline (proposed spine — edit me)

1. **Why query?** — recall Module 2's "regex every stdout" pain and the `Float` nodes we got out of `parse_output`. Frame QueryBuilder as: *the database is already queryable; you don't have to materialise every node.*
2. **Basics on a single node type**: `QueryBuilder().append(orm.Float, ...)`. Cover `filters`, `project`, `count`, `all`, `iterall`. Use the F-sweep `Float`s already in the profile.
3. **Filtering by attributes, extras**: pick up the extras tagged in Module 2 (`F`, `sweep='F_scan'`). Filter and project.
4. **Traversing the provenance graph**: `with_outgoing` / `with_incoming` / `with_ancestors` / `with_descendants`. Example questions:
   - "Given a sweep workflow node, find all its `Float` outputs."
   - "Given a `Float`, find the workflow that produced it."
5. **Joins across multiple types**: stitch two or three `.append(...)` calls, e.g. *"all `Float` outputs of any `parse_output` calcfunction whose process is tagged `sweep='F_scan'`"*.
6. **Aggregation / statistics**: count, project numeric attributes. (Open question below: SQL-style `func.*` or Python-side?)
7. **Scale teaser**: per 2026-05-12 boss notes — querying N `Float` nodes via QB vs. opening N files from disk. Show the wall-time difference on the existing N=10 sweep, sketch how it would matter at N=10⁴.
8. **Export & share** (light touch): `verdi archive create` from a QB selection. (Open question below: full round-trip or pointer?)
9. **Next steps + Further reading**.

## Tone & format

- Same shape as other modules: surface a pain point inline, then the QueryBuilder fix, then build complexity gradually.
- Live executable cells throughout. No illustrative-only `{code-block}` for the QB examples — data is already in the profile.
- Semantic linebreaks (one sentence per line, applied via `_notes/semantic_linebreaks.py`).
- No em-dashes (per project convention).
- Admonitions: blue `note` for definitions, green `tip` for optional improvements, orange `important` for *one* central abstraction message (yet to be defined — likely about "the provenance graph itself is queryable, not just nodes you happen to hold a Python reference to").
- also 'important' admonitions

## Coverage to surface from TRACKING.md

- [ ] QueryBuilder basics (`append`, `filters`, `project`).
- [ ] Filtering by node type, attributes, extras.
- [ ] Traversing relationships (inputs, outputs, ancestors, descendants).
- [ ] Aggregation and statistics.
- [ ] Exporting and sharing results (AiiDA archive).
- [ ] Benchmark/speed: result retrieval at scale, QueryBuilder vs file I/O (light teaser only; full benchmark is Module 5 territory but kept light per 2026-05-12 notes).

## Open judgment calls (please decide before I start)

### 1. Aggregation depth — SQL-side or Python-side?

- **SQL-side** (`func.count`, `func.max`, `func.avg` from `sqlalchemy.func`): correct answer for "scale teaser"; computation happens in the database, doesn't materialise nodes.
- **Python-side** (`.all()` then `statistics.mean`, `numpy.max`): simpler API surface; readers don't need to know about `sqlalchemy.func`.

> JG: only python side, no sql

### 2. Archive export depth

- **Pointer**: one paragraph + one `verdi archive create` invocation, no round-trip.
- **Worked example**: create archive, optionally re-import into a fresh profile, verify content.

My instinct: pointer-only. Full round-trip would distract from the QB story, and Module 7 / a future "sharing" module is a better home.

> JG: agreed! not sure where archive creation / import should actually go, tbh

### 3. Should the module conclude with a small data analysis?

- Currently Module 2 already plots the transition curve from the F-sweep using `enriched_results` in Python.
- Module 5 could rebuild the same plot purely from QueryBuilder (no `enriched_results` list, just the database), as a satisfying payoff — "you no longer need to hold Python references to the nodes you want to analyse".

> JG: yes, good idea. apply!

## Things to verify before writing

- Anchor `topics:database:querybuilder` exists in aiida-core's source (used in Further reading).
- Anchor `how-to:query` exists (used in Module 2 already; reused here).
- `aiida-shell`'s ShellJob node class — confirm it's `CalcJobNode` (so `.append(orm.CalcJobNode, filters={'attributes.process_label': 'ShellJob'})` works) or whether it has its own node class.
- Confirm `Group.collection.get_or_create('tutorial/F-sweep')` from Module 2 actually has nodes (depends on whether the sweep cells executed in the current build cache).
- YES, verify with existing docs and tracking md file. make sure we don't forget anything, but are more concise than the full docs, and it integrates nicely into the story line.

## Files to create / modify

- `docs/source/tutorials/module5.md`: replace the stub with the full module.
- `docs/source/tutorials/TRACKING.md`: tick off the items listed under Module 5 as they land.
- `docs/source/tutorials/index.md`: once Module 5 is functional, swap its `*Coming soon*` card for a `button-ref` (matching the Module 4 promotion done at the end of the Module 4 work).

## Out of scope (explicitly)

- Re-explaining the F-sweep, the calcfunctions, the workflow — only refer back via `{ref}` to Modules 2/3.
- The scale benchmark beyond a one-cell wall-time comparison.
- Cross-profile archive workflows.
- Anything related to Modules 6/7 (advanced workflow patterns, error handling).
