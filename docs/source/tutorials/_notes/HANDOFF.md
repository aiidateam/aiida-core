---
orphan: true
---

# Tutorial rework: handoff / resume-here

Resume point after context compaction.
Full decision log + JG/CC threads live in `2026-06-02-gm-feedback-plan.md`; this is the tight "where we are, what's next" summary.

---

## LATEST ROUND: module3a deep content pass (resume here, next = module3b)

We did a full line-by-line content/wording pass on **module3a** with JG, driven by `_notes/reword-module3a.md` (items 1-9 + a "mental model" block, **all resolved**, CC notes in the doc). Plus many live ad-hoc edits. **module3a is content-complete pending a real build-verify.**

### Durable conventions established this round (APPLY THESE TO 3b AND BEYOND)

- **No "handle" wording.** Calling a task returns its **output sockets** (a `TaskSocketNamespace`), not a "handle". Say "output sockets" / "the task's outputs".
- **Avoid private (`._foo`) and dunder (`type(x).__name__`) in *shown* code**, where a clean public/domain accessor exists:
  - process-node type → `node.process_label` (e.g. `WorkGraph<gray_scott_pipeline>`), NOT `type(x).__name__`.
  - socket-name listing → `wg.get_input_names()` / `wg.get_output_names()`, NOT `._get_keys()`.
  - prefer readable names + list slices over `next(gen)` (`[child for child in ... ][0]`, not `next(c for c in ...)`).
  - **Exceptions that MUST stay (no public alternative, verified):** (1) gathered `Map`/dynamic-namespace outputs are read via private `._value` (public `.value` raises `AttributeError`, node-graph bug, issue drafted) — module3b:243,356 and module6b:258,259,272 keep `._value` with their explanatory comments; (2) module1:211 uses `type(output_node).__name__` for a *data* node's class (data nodes have no `process_label`; kept, it's standard introspection).
- **`orm.Dict` inputs kept explicit** in build calls (we verified plain dict auto-converts, but chose to keep `orm.Dict(...)` — do NOT switch to plain dicts). `parameters=orm.Dict(BASE_PARAMS)` in 3b's build calls stays.
  - (module3a specifically ended up passing `parameters=BASE_PARAMS` plain in its two `.build()` calls + a bullet teaching auto-conversion; that was a module3a-local choice. For 3b keep whatever is already there unless JG says otherwise.)
- **blueprint → build → run framing:** the `@task.graph` function (`gray_scott_pipeline`) is the *blueprint*; `.build(...)` makes it *concrete* (a runnable `WorkGraph`); `.run()`/`.submit()` executes. Don't call the built graph the "blueprint".
- **Don't name AiiDA link types** (`CALL_CALC`, `RETURN`, `INPUT_WORK`) in prose, they were never taught; say it plainly ("linked to each child it called and back to the outputs it returned"). module1:164's forward-promise of those names was removed.
- **Reading-time + difficulty badges** are on every module H1: `{bdg-secondary}⏱️ ~N min read` `{bdg-<color>}<Tier>` (Beginner=success/green, Intermediate=primary/blue, Advanced=warning/amber). `.sd-badge` is bumped in `_static/aiida-custom.css`. JG will tune numbers.
- **`shelljob()`**: describe as "a convenience that handles the actual `ShellJob` setup for you behind the scenes and adds it to the active graph" — a light parenthetical, NOT a big note.
- General wording aesthetic JG applied relentlessly: cut repetition (don't restate the same idea twice), plain English over jargon, no forward-refs to things introduced later, split overlong bullets, one point per sentence.

### `include/` state (done earlier this session)

`tasks.py` split into: `tasks.py` (core: `prepare_input`, `parse_output`, `ParseOutputs`) + `tasks_module_3b.py` (`make_transition_plot`) + `tasks_module_6.py` (`fft_peak_wavelength`, `bump_n_steps`, `identify_transition_region`). All `.md` imports / `{literalinclude}` / `{download}` repointed. `workflows.py`'s `gray_scott_pipeline` docstring trimmed to one line.

### Cross-cutting propagations DONE across all modules

- All install notes use `uv pip install ...` (not `pip install`).
- Setup comment collapsed to `# Set up the tutorial's isolated sandbox profile (see Module 1 for details).` in M2/M3a/M3b/M4/M5/M6a/M6b/M7 (M1 keeps the full explanation, it's where setup is taught).
- `conf.py` `nb_execution_mode` was toggled to `'off'` during the prose sweep and **REVERTED** — execution is back ON (default `auto`). Rebuilds re-run notebooks.

### New draft issues written this round (in `_notes/`, as JG, ready to post; NOT posted)

- `aiida-workgraph-shelljob-task-issue.md` — fold `shelljob()` into `task(ShellJob, outputs=...)`; only ShellJob's dynamic-output namespace isn't auto-discoverable.
- `node-graph-namespace-value-issue.md` — public accessor for namespace socket `value` (currently only private `._value`; pure-node-graph MWE verified). The wishlist in the plan doc has the `._value` finding + adjacent upstream refs (node-graph #155/#156, aiida-workgraph #786/#779).

### NEXT: module3b

Same treatment as 3a. 3b covers `Map` (turning the Module-2 `for`-loop into a parallel workflow) + `make_transition_plot` reduction. Things to watch:
- Apply all conventions above (esp. no "handle", plain link-type language, blueprint framing, private/dunder rules).
- 3b's `._value` reads (lines ~243, ~356) STAY (documented exception).
- 3b already has uv + one-line setup + badge (`~70 min` Intermediate).
- Work from any GM-feedback items still open for 3b (check the plan doc's per-module worklist).
- module3a is NOT yet build-verified after this round's edits — a real build of M1→M2→M3a (chained data) should be run at some point to confirm cells execute.

---

## Where we are

Reworking the new AiiDA tutorials (`docs/source/tutorials/module*.md`) against group-meeting feedback (source: `review/2026-06-02-msd-gm-tutorial.md`).
The modules are now:

- `module0.md` calculations without AiiDA
- `module1.md` calculations with AiiDA
- `module2.md` structured data + calcfunctions
- `module3a.md` writing a workflow / `module3b.md` running it over many inputs with `Map` (split from module3)
- `module4.md` remote submission
- `module5.md` querying + analysis
- `module6a.md` If / While / `module6b.md` workflows that build themselves (split from module6)
- `module7.md` where to go next

## Commit state (branch `docs/integrate-tutorials`)

Committed, in order:

1. `make the rendered pages runnable` (M0 rewrite + X3 sweep across all modules)
2. `mod 1 & 2 rework` (M1/M2 inline pass)
3. `rename "Introduction" card to "About"` (D6, `index.rst`)
4. `structural pass, split M3 and M6` (the big batch: M3/M6 splits, M4/M5/M7 passes, UPPERCASE constants)

**Staged, not yet committed:** the `/tmp/aiida-tutorial` scratch-dir change (M0/M1/M2 + `.gitignore`), message ready in `COMMIT_EDITMSG` (`git commit -eF COMMIT_EDITMSG`).

## What's DONE

All **structural** GM-feedback work across every module: splits (M3, M6), the shared-code/inline pattern, install notes, the specifically-flagged phrasings (L1-L5), the new QueryBuilder filter syntax (M5, D7), UPPERCASE constants, sandbox-profile setup, `/tmp` scratch. See the plan's progress log for the per-module detail.

## What's LEFT (the content work to continue)

1. **Commit the staged `/tmp` change** (message ready).
2. **D4 quickstart**: a net-new ~20-cell single page (`docs/source/tutorials/quickstart.md`), its own index card. Should reuse the now-inlined code. JG wants to see a draft.
3. **Cross-module wording + code-simplification sweep (X5/X6)** — the deferred big one. "Tune down technical wording (AiiDA- and Python-specific), shorter sentences", plus simplify advanced code (e.g. M6b's `_get_keys()`/`getattr` graph-inspection cell, the `._value` unwraps). Deferred to ONE consistent pass across modules (JG's call). Heaviest in the WorkGraph modules (M3a/b, M6a/b): sockets, zones, dynamic namespaces.
4. **M4** could not be build-verified locally (needs the SLURM container); its changes are prose + inline-regex, low risk, but give it a real build when the container is up (`bash docs/source/tutorials/_notes/start-slurm-container.sh`).

## Key conventions / decisions (don't re-litigate)

- **X3 (governing UX rule):** the rendered page must be a complete, runnable artifact. What is shown must be what runs. Fold output (`hide-output`/`hide-input`/`hide-cell`), never `remove-cell`/`remove-input` on anything load-bearing. Downloaded notebook / copy-pasted cells must reproduce.
- **Sandbox profile (D10):** every module's setup cell is visible: `%load_ext aiida` + `%run -i include/setup_tutorial.py`. It creates an isolated `tutorial-<hash>` profile (SQLite + ZMQ), separate from the reader's real profiles. `setup_tutorial.py` uses `get_config(create=True)` and cleans up stale `tutorial-*` profiles itself.
- **D8 shared-code pattern:** `include/` (`constants.py`, `tasks.py`, `workflows.py`, `plotting.py`) stays as the single source of truth (separate notebook kernels can't import each other). Rule: **show where introduced** (inline cell or `{literalinclude}`), **show folded where reused** (`{literalinclude}` inside a `:::{dropdown}`, or a `hide-input` cell), always `import` from `include/`. Inline only the tiny constants (`BASE_PARAMS`, `F_VALUES`, the regexes), kept **UPPERCASE** (they are constants; match `constants.py`). `plotting.py` stays an acknowledged, downloadable helper.
- **Splits:** one home-page card per module group (no extra panels, per C8); `toctree` lists the a/b halves; `(tutorial:moduleN)=` aliased onto the "a" half so old cross-refs resolve. Git tracks them as renames.
- **Scratch:** notebooks use `/tmp/aiida-tutorial` (not a local `tmp/`, which sphinx would scan).
- **Wording is deferred** to the single sweep (item 3 above). Per-module passes only touched flagged phrasings + structure.

## How to verify a module (isolated build)

Real docs build is slow and pulls the whole tree. To verify one/few modules, build an isolated minimal project:

- Temp dir with the module `.md`(s), a copy of `include/`, a minimal `conf.py` (`extensions = ['myst_nb','sphinx_design','sphinx_copybutton']`, `myst_enable_extensions=['colon_fence','deflist']`, `nb_execution_mode='auto'`, `nb_execution_raise_on_error=True`, `nb_execution_timeout=900`, `html_theme='alabaster'`), and an `index.md` toctree listing them.
- Set `AIIDA_PATH` to an isolated scratch dir so it never touches `~/.aiida`.
- `READTHEDOCS=1 uv run sphinx-build -b html <src> <out>` (READTHEDOCS=1 turns on tracebacks).
- Chain modules that share data: M5 needs M2's sweep, so build M1→M2→M5; M6a/b and M7 are self-contained (they run their own gsrd). M4 is excluded (container).
- **Always `verdi daemon stop` the isolated profile afterward** and check no scratch `circusd` lingers; don't leave daemons in `~/.aiida`.
- `re-run cp -r include` into a FRESH temp dir each time (copying into an existing one nests `include/include` and breaks `%run include/...`).

## Gotchas

- Each notebook = its own kernel; cross-notebook reuse must go through a file in `include/`.
- `nb_execution_show_tb` must be a real bool; don't pass it via `-D` as a string.
- `verdi process dump` writes a `README.md`; keep dump output under `/tmp` so sphinx doesn't treat it as a doc.
- A stray `tutorial-*` profile may sit in `~/.aiida` from testing; harmless, auto-cleaned on the next real build, or `verdi profile delete tutorial-<hash>`.
- Use `uv run` for everything.
