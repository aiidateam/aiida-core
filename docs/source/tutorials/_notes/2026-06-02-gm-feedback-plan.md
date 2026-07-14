---
orphan: true
---

# GM feedback resolution plan (2026-06-02)

Working doc.
Source feedback: `review/2026-06-02-msd-gm-tutorial.md` (committed copy of `~/notes/2026/06-02-msd-gm-tutorial.md`).
Goal: turn the scrambled meeting notes into a concrete, per-issue plan so we can work through the modules one by one.

How to use this doc:

1. Read **Decisions needed** first and mark each call.
   Several downstream edits (module splits, quickstart, filter syntax) are gated on these.
2. **Cross-cutting checklist** is applied to *every* module during its pass.
   It is the bulk of "affects the whole tutorial".
3. **Issue-by-issue** gives every meeting item an ID (`Cn`/`Ln`/`Un`/`An`/`In`) with a concrete resolution.
4. **Per-module worklist** is the checklist for each sit-down, cross-referencing issue IDs.
5. **AiiDA 3.0 API wishlist** collects the "keep as-is now, simplify later" items.
6. **Build/config changes** and **Open questions** at the end.

---

## Decisions needed from you

These are product calls, not mechanical edits.
My recommendation is first; the rest are the alternatives that came up.
Reply inline with `> JG:` under each item.

- **D1 - Split Module 3 (631 lines)?** Rec: **yes**, into `3a` (linear pipeline: why + mental model + compose) and `3b` (parameter sweeps: `Map` + 2D scan). Natural break at line 343 ("Integrating the for-loop"). Present as one nav group, not two extra home-page cards (see C8).

> JG: agreed!

- **D2 - Split Module 6 (641 lines) too?** Rec: **maybe, later**, `6a` If/While, `6b` nesting + adaptive sweep. Decide after the M3 split lands. Same "sub-module, not new card" treatment.

> JG: also split, do it now.

- **D3 - Fate of the basic tutorial (`basic.md`, 776 lines)?** Rec: **keep but demote** for now; revisit after the new modules stabilize. Alternatives: drop it, or fold its unique provenance/querying content into M5 / an appendix.

> JG: let's not modify it for now. this will come later.

- **D4 - Build a separate ~20-cell quickstart?** Rec: **defer to a follow-up PR** (net-new content, not a fix to the existing modules). Would be a single linear page: install, run, provenance, one sweep, one workflow, one query.

> JG: where would this go? sounds interesting, please add the code, then i'll have a look (we can always delete / move to another PR later)
>
> CC: New page `docs/source/tutorials/quickstart.md`, its own card on the tutorials index above the modules. A single linear ~20-cell path: install, setup profile, run gsrd via aiida-shell, inspect provenance, one `Map` sweep, one query. I'll draft it *after* the module code is inlined (D8), so it reuses the same shown definitions instead of inventing a parallel copy. Trivial to move to a separate PR or delete.

- **D5 - What to do with `aiida-qe-demo`?** Rec: **out of scope here**; link it from the M7 ecosystem section as a real-plugin demo, and decide its fate separately. The "QE-user demo" version of the tutorial belongs in the plugin world, not aiida-core docs.

> JG: agreed. let's do it liko this

- **D6 - "Rename introduction to about": which label?** Rec: the docs landing card in `docs/source/index.rst:36` ("Introduction" to **"About"**). Confirm that is the intended target; it is *not* the tutorials index grouping ("Introductory modules").

> JG: yes, agreed. let's rename it (maybe will split off to a separate PR later)
>
> CC: Done. `index.rst` landing card "Introduction" to "About", and its button "To the introduction" to "To the overview". Kept as its own commit so you can cherry-pick it to a separate PR.

- **D7 - Adopt the new QueryBuilder filter syntax as the default?** Rec: **yes**, `orm.Float.fields.value > 0.01` works in 2.8.0 and is already documented (see A1). Affects M5 primarily, M2 secondarily.

> JG: yes, change the code to use that new syntax

- **D8 - `include/` directory: keep the name or rename?** Rec: **keep + explain once** (in M1, first appearance). Renaming to `shared/` touches every module's paths for little gain (see C3).

> JG: well, if we show all the code, why would we even need that still? for the yaml files? if it still earns its place, then we keep it for now. but, it should not contain any hidden python code.
>
> CC: Agreed, and it's a real X3 gap. `include/` today hides the *teaching* code, all imported invisibly: `tasks.py` (the calcfunctions `prepare_input`/`parse_output` + M6's `fft_peak_wavelength`, `bump_n_steps`, `identify_transition_region`), `workflows.py` (the `gray_scott_pipeline` WorkGraph), `constants.py` (`BASE_PARAMS`, `F_VALUES`, `VARIANCE_RE`, `MEAN_RE`), and `plotting.py`. Plan: **inline the teaching python where it is taught**, calcfunctions defined in M2, workflow in M3, M6's tasks in M6, the small constants shown where first used, so nothing the tutorial teaches is hidden behind an import. **Keep `include/` for**: the `.yaml` inputs + the `.png` images (data, not code), and the two setup scripts (`setup_tutorial.py` / `setup_slurm.py`, infra that's already run via a *visible* `%run` and is downloadable). **One edge case, your call**: `plotting.py` is ~9 KB of matplotlib boilerplate that isn't the teaching point and would drown the plot-heavy modules if inlined. I lean toward keeping it as an explicitly-acknowledged, downloadable helper (prose: "plotting helpers live in `include/plotting.py`, not the focus here"). Say the word if you'd rather inline it too for literally zero python in `include/`. The inlining rides along with each module's content pass (heaviest in M2/M3/M6).
>
> CC (resolved 2026-07-13): went with **keep + show via literalinclude** (Option A). Reuse forces it: `gray_scott_pipeline` and the calcfunctions are used across M3a/M3b/M6/M7, and separate notebook kernels cannot import each other, so `include/workflows.py` + `tasks.py` must stay as the shared reuse layer (deleting them would mean re-pasting the whole pipeline in every module). To honor "no hidden python" WITHOUT bloating modules (JG's worry): (1) show the code that a module *introduces* via `{literalinclude}` in that module (foldable), (2) keep *reused* code as `import` + a one-line acknowledgment, not re-shown, (3) fold boilerplate bodies (e.g. `make_transition_plot`'s matplotlib, the `plot_*` helpers), (4) inline only tiny constants (`base_params`, `f_values`, the regexes). Net: nothing hidden, modules stay lean. This revises the earlier "delete tasks/workflows from include/" idea, which the cross-notebook reuse makes impossible. Rule of thumb: **show where introduced, show folded where reused, always import from the shared file.**
>
> CC (pattern verified 2026-07-13): JG refined it, reused code should still be *shown* in the reuse module, just folded, so a cell-by-cell copier can grab it there too. This works with `{literalinclude}` inside a `:::{dropdown}`: builds cleanly and renders the `:pyobject:` source inside a collapsible, while execution still `import`s from the shared file (no duplication). Canonical pattern for any shared function:
> ```
> :::{dropdown} `gray_scott_pipeline` (defined in Module 3a)
> ​```{literalinclude} include/workflows.py
> :pyobject: gray_scott_pipeline
> ​```
> :::
> ```
> So: introducing module shows it (unfolded, or a plain `{literalinclude}`); every reusing module shows it folded via the dropdown+literalinclude; all of them `import` the real definition from `include/`. `include/` keeps `constants.py` / `tasks.py` / `workflows.py` / `plotting.py` (+ yaml + images + setup scripts) as the single source of truth, and nothing is hidden.

- **D9 - M7 install: `aiida` vs `aiida-core`?** Rec: **`aiida-core`** now; open a release-process item so the `aiida` PyPI name is handled deliberately (it currently resolves to the ancient 1.0.1 meta-package). See I1.

> JG: yes, aiida-core.

- **D10 - How to treat the per-module profile-setup cell (X3 sweep)?** The setup cell (`%load_ext aiida` + `%run -i include/setup_tutorial.py` + stale-profile cleanup) is currently fully hidden (`remove-cell`) in every module, and the reader is shown a `$ verdi presto` console block instead, exactly the M0 fake-console pattern. Rec: **make it one visible cell everyone runs**, and reframe the tutorial to use a dedicated **sandbox profile** (`tutorial-<hash>`, isolated + reproducible), moving the stale-cleanup into `setup_tutorial.py` so the cell stays short. Downloaded notebooks then run truthfully; nothing hidden. Alternatives: (b) visible reader path `%load_ext aiida; load_profile()` + a folded build-only override cell; (c) move all build-only profile creation out of the notebooks into the build harness so each setup cell is just `load_profile()` (cleanest, but needs new build wiring). See the **X3 sweep** section below for the full audit.

> JG:
> CC: Approved 2026-07-13, going with the sandbox approach (rec above). Implementing now.

---

## Cross-cutting checklist (apply to every module)

Run this list on each module during its pass.
These come straight from the "Language & wording", "Code & notebook UX", and "Installation" sections of the feedback.
**X3 is the governing rule**: the rendered page must be a complete, runnable artifact. Most other UX items serve it.

- **X1 Installation note.** Short admonition at the top of each module listing exactly what to `pip install` for it (M0: `gsrd`; M1: `aiida-core aiida-shell`; M3/M6: `aiida-workgraph`; etc.). Ties I1 + U8.
- **X2 Further reading + inline asides.** Every module ends with a consistent `## Further reading` bullet list (all modules already have one; standardize wording and make sure links resolve). For inline "by the way" references, use MyST footnotes `[^x]` (auto back-link to the text) or a `{dropdown}` fold-out, so the main narrative is not interrupted. Footnotes and `sphinx-design` dropdowns are both available in this build.
- **X3 The rendered page must be a complete, runnable artifact.** This is the north-star UX rule, not a styling preference. Readers do not get a curated `.ipynb`; they copy the visible cells one by one, or download the source, and it has to run locally as-is and reproduce what the page shows. So what is *shown* has to *be* what *runs*, with nothing load-bearing hidden.
  - **Folding output is fine; hiding input is not.** `hide-output` (collapsed, still present and copyable) is OK for noisy logs. `remove-input` / `remove-cell` on any cell a reader needs to reproduce the result is banned. Canonical anti-pattern: `module0.md` renders a non-executable ``$ gsrd input.yaml`` console block while the cell that defines `work_dir` (`remove-cell`, :75) and the cell that actually runs the simulation (`remove-input` `subprocess.run(..., cwd=work_dir)`, :91) are both hidden. Copy the visible cells and `work_dir` is undefined and nothing ever runs. Fix: make setup and run visible (ties X7: visible `!mkdir -p tmp` then a real `!gsrd input.yaml` / plain Python run), and fold only the noisy *output*.
  - **Build-only machinery leaves the notebook flow entirely, it does not become a hidden cell.** Profile/computer cleanup, dropping the scheduler poll interval to 1s, SSH-to-container plumbing, fresh-profile-per-build: a real user must not run these, and a downloaded source notebook carries hidden cells too, so a `remove-cell` cleanup that deletes profiles would fire on someone's real machine on download. Consolidate all of it behind a single visible, honest `%run include/setup_*.py` line (already the pattern for profile setup), keep the destructive bits inside that script scoped to tutorial-only profiles, and add a comment giving the reader's local equivalent (`verdi presto` / `load_profile()`).
  - **Per-module acceptance test.** A fresh reader who copies the visible cells top to bottom (or downloads and runs the notebook) reproduces the shown results, and nothing they run touches or deletes their real profile/data. Check this at the end of every module pass.
- **X4 `!` vs `%`.** Explain once, early (M1): `%verdi`, `%run`, `%load_ext` are IPython magics; `!cmd` runs a shell command. Then audit for consistency (we currently use `%verdi` everywhere, good; `!tree` is a shell command, correct). Do not mix `!verdi` and `%verdi`.
- **X5 Simple Python in visible cells.** Assign to variables before using them. Prefer more short lines over one long line. Avoid comprehensions, advanced f-string formatting, and `Path(...).resolve()` in cells the reader is meant to read; push cleverness into `include/` helpers or hidden cells. Put a plain-language comment at the top of each visible cell saying what it does.
- **X6 Wording.** Shorter sentences, less jargon (AiiDA-specific *and* Python-specific). Introduce every AiiDA term at first use. No forward references to concepts not yet taught (the big one: WorkChain, first introduced in M7, must not be used to *explain* WorkGraph in M3/M6). See L-series for the specific flagged phrases.
- **X7 Temp dirs.** Replace `tempfile.mkdtemp(...)` in *teaching* cells with a visible `!mkdir -p tmp` and a plain `tmp/` path, plus a one-line comment. Keep `mkdtemp` only in hidden setup cells.

### X3 sweep: hidden-cell audit (modules 1-7)

Full inventory of `remove-*` cells and fake `console` blocks. Finding: **almost everything is already X3-compliant.** The only fully-hidden cells are the profile-setup cells and Module 4's CI-container plumbing; every other folded cell uses `hide-output` / `hide-input` / `hide-cell`, which keep the input present and copyable. Module 0 is already fixed.

- **Category 1: profile setup** (m1:55, m2:47, m3:46, m5:38, m6:33, m7:38, m4:47). Fully hidden (`remove-cell`). Two problems: copy-pasters never get `%load_ext aiida` (so `%verdi` fails), and a downloaded notebook carries the docs-build profile creation + `tutorial-*` cleanup. Treatment gated on **D10**; whatever we pick, apply it identically to all seven.
- **Category 2: M4 CI-container plumbing** (m4:55 SSH `~/.ssh/config`, m4:101 stale-computer cleanup, m4:239 poll-interval=1s, m4:264 transport `whoami()` fail-fast). Genuine build-only, and M4 is not executed at build time anyway (`nb_execution_excludepatterns`). Problem: a downloaded M4 notebook would rewrite the reader's `~/.ssh/config` and SSH to a container they do not have. Treatment: `remove-cell` to `hide-input` (folded, present, copyable); the comments already say "CI container; on your own cluster do X". No decision needed, do it with the sweep.
- **Category 3: console blocks.** m1:47 `$ verdi presto` is the same fake-console pattern as M0 (shown, but the build runs the hidden setup); it resolves once D10 lands (presto becomes "the general way to make a profile", the visible setup cell becomes the runnable path). m4:151 / 176 / 340 are legitimate *illustrative alternatives* (YAML config, export-to-YAML, a `daint` real-cluster example), not stand-ins for hidden runs, so they stay as `console`.
- **Not touched (already compliant):** every `hide-output` / `hide-input` / `hide-cell` in m1-7. Output/whole-cell folding keeps the input present and copyable, which is exactly what X3 asks for.

---

## Issue-by-issue resolutions

### Content & structure

- **C1 Module 0 too long (316 lines).** Trim the three run sections (run / run again / run into errors) to their essentials and condense "How this becomes worse at scale" + "How AiiDA solves these problems" into one tighter motivation. Front-load the payoff. Target ~20-25% shorter. Keep it a single module (do not split).
- **C2 Module 3 too long.** See D1: split into 3a/3b.
- **C3 "What is module include?"** `include/` is not a module; it is the shared-code directory (`constants.py`, `tasks.py`, `workflows.py`, `plotting.py`, `setup_*.py`, `input*.yaml`, images) that modules import or `%run` so cells stay short and DRY. Two problems: the name reads like a Sphinx directive, and it is never explained. Fix: explain it once in M1 at first appearance ("`include/` holds helper scripts and input files shared across modules; each file is downloadable via the link below"). The `inline_downloads` extension (`docs/source/_ext/inline_downloads.py`) already exposes these as downloads, so reference that. Rename only if D8 says so.
- **C4 Split long modules into sub-modules.** Principle behind D1/D2. Apply to M3 now, M6 later; leave M7 as an intentional "menu" module but trim it.
- **C5 Rename "introduction" to "about".** `docs/source/index.rst:36` grid card and `:51` link text. Confirm via D6.
- **C6 Introduce the leading example on the index page (EB).** Move a short description of the Gray-Scott reaction-diffusion running example (with one pattern image) into the tutorials `index.md` intro, above the module cards. Currently the intro is two generic sentences. Trim the moved copy out of M0's opener so it is not duplicated verbatim.
- **C7 Further-reading links at the end of every module.** Covered by X2.
- **C8 Fewer modules on the home page.** On the main docs landing and the tutorials index, reduce visual load: keep the four introductory modules prominent, collapse the advanced four into a compact list or a single expandable card, and fold any M3a/M3b (D1) under one entry so a split does not add cards. Do not surface all 8 modules as equal top-level cards.

### Quickstart & basic tutorial

- **C9** Basic tutorial: D3.
- **C10** Separate quickstart: D4.
- **C11** Two demo versions (basic + QE): the generic quickstart lives here; the QE-user demo stays in the plugin ecosystem. Tied to D4/D5.
- **C12** `aiida-qe-demo`: D5.

### Language & wording

Each of these is a specific flagged phrase with a suggested rewrite; finalize wording during the module pass.

- **L1** `module2.md:244` "they declare typed, validated input ports in their process spec" to: "real CalcJob plugins check the inputs for you and reject bad or unknown parameters before the calculation runs."
- **L2** `module3.md:206` "that is where gsrd prints the headline scalars our parser regexes out" to: "that is where gsrd prints the summary numbers our parser reads out." (Drop "headline scalars" and "regexes out".)
- **L3** WorkChain forward-reference. "the WorkGraph analogue of the WorkChain `ctx`" appears at `module3.md:93`, `module3.md:247`, `module6.md:64`, `module6.md:282`. WorkChain is not introduced until M7, so it cannot carry an explanation in M3/M6. Rephrase `ctx` on its own terms ("a shared key-value store the tasks can read and write"); move any WorkChain comparison to M7 or a `{dropdown}`.
- **L4** `module3.md:260` "So, `gray_scott_pipeline` is now a factory: call `.build(...)` ... embed it as a sub-task." Split into short sentences and either explain "factory" plainly or drop the word: e.g. "`gray_scott_pipeline` does not run anything by itself. Calling `.build(...)` gives you a ready-to-run `WorkGraph`. You can `run()` or `submit()` that graph directly, or drop the same call inside a bigger graph to reuse it as one step."
- **L5** `module4.md:381` "is then byte-for-byte identical" to: "is exactly the same as the local run from Module 1." (Drop "byte-for-byte": jargony and not strictly true.)
- **L6** Introduce AiiDA lingo at first use (QueryBuilder, calcfunction, CalcJob, provenance, ORM, WorkGraph, Map, port, extras, group). Covered by X6; the specific offender flagged was QueryBuilder in M5.

### Code & notebook UX

- **U1** Simplify Python: X5. Flagged example `input_path = Path('include/input.yaml').resolve()` (M1:117, M4:391, M0:81-82). Verify aiida-shell accepts a plain relative string `'include/input.yaml'`; if yes, use the string and drop `.resolve()`. If the resolve is genuinely needed (cwd ambiguity), keep it with a one-line comment.
- **U2** More comments in visible cells: X5.
- **U3** `!` vs `%`: X4.
- **U4** Missing `tree`. `!tree` is used (M1:322) but `tree` is **not installed** in the RTD build (`.readthedocs.yml` apt_packages has only `graphviz`), so it fails there. Fix: add `tree` to `apt_packages` in `.readthedocs.yml` (and the CI docs-build env). Fallback if we would rather not add a system package: a tiny Python tree helper in `include/`.
- **U5** `mkdtemp` to `!mkdir -p tmp`: X7. Locations M0:80, M1:316, M2:77.
- **U6** Complete/runnable page (fold output, never hide load-bearing input): X3. Module 0 is the first and worst offender.
- **U7** Copy button on RTD. `sphinx-copybutton` is enabled (`conf.py:84`, `copybutton_selector` at `:225`), so yes, there is a copy button. Verify it actually renders on executed notebook code cells and that the prompt-stripping regex leaves `%verdi` / `!` intact (we *want* those copied). One quick visual check on a built page.
- **U8** M0: `pip install` the gsrd repo. Add an install cell/note at the top of M0 (`pip install gsrd @ git+https://github.com/aiidateam/gsrd`, or from PyPI if published). Ties X1.
- **U9** Open aiida-core issues for code simplifications (GP). Action item, not a doc edit: seed from the AiiDA 3.0 wishlist below and file issues.

### API ergonomics

- **A1** New filter syntax (M5). Confirmed available in 2.8.0: `orm.Float.fields.value > 0.01` returns a `QbFieldFilters` accepted by `filters=`, supports `&` / `|` / `~`, and is already documented in `howto/query.rst` + `topics/database.rst`. Adopt as the default in M5 (and M2:429, M5:85/242, M7:359). Optionally show the dict form once as "you may still see the older `{'>': 0.01}` form". Gated on D7.
- **A2** `first_calc_node.base.extras.all.items()` is long (M2:382). Keep as-is for this tutorial; add to the AiiDA 3.0 wishlist.
- **A3** Joining visualization (M5, "Joining across the graph", line 134). Add a small schematic (e.g. Group to CalcJob to Float) styled **distinctly** from the graphviz provenance graphs (rounded colored boxes, different palette) so readers do not confuse it with provenance. No Mermaid in this build, so hand-author an SVG in `_static/` (e.g. `join_schematic_module5.svg`).

### Installation & packaging

- **I1** M7 install. Use `pip install aiida-core` (plus the extras the tutorial needs), not `pip install aiida` (resolves to the ancient 1.0.1 meta-package). Open a release-process item to decide deliberately whether/how to own the `aiida` name. Gated on D9.
- **I2** Per-module installation note: X1.

---

## Per-module worklist

Cross-references the issue IDs above. `X*` = the whole cross-cutting checklist.

| File | Items |
|---|---|
| `index.md` (tutorials) | C6 (running-example blurb + image), C8 (fewer/grouped cards) |
| `index.rst` (docs landing) | C5 (Introduction to About, D6) |
| `module0.md` | C1 (trim), U8 (install gsrd), X1, X3, X5, X6, X7 |
| `module1.md` | X4 (explain `!` vs `%`, first time), C3 (explain `include/`), U4 (`tree`), U1 (`.resolve()`), X1, X2, X5, X6, X7 |
| `module2.md` | L1 (typed ports), A2 (extras wishlist), U1 (comprehension at :382), A1 (filters at :429), X1, X5, X6, X7 |
| `module3.md` | D1 (split 3a/3b), L3 (WorkChain `ctx` fwd-ref), L4 (factory sentence), X1, X2, X5, X6 |
| `module4.md` | L5 (byte-for-byte), X3 (many `remove-cell`; keep genuine plumbing, fold the rest), U1 (`.resolve()`), X1, X6 |
| `module5.md` | A1 (new filter syntax, default), A3 (join schematic), L6 (introduce QueryBuilder), X1, X2, X5, X6 |
| `module6.md` | D2 (maybe split 6a/6b), L3 (WorkChain `ctx`), L4-style `.build()` sentences, X1, X2, X5, X6 |
| `module7.md` | I1 (`aiida-core` not `aiida`), D5 (link aiida-qe-demo), A1 (filters at :359), X1, X6 |

---

## AiiDA 3.0 API simplification wishlist

"OK to keep as-is for the current tutorial." File as issues (U9). Seeded from the feedback + `_notes/api-discrepancies.md`.

- Shorter extras access: `node.base.extras.all.items()` to something like `node.extras.items()` (A2).
- Unified run/submit for WorkGraph: `engine.run(wg)` / `engine.submit(wg)` instead of instance methods (api-discrepancies item 1; PR open).
- `verdi process dump` support for WorkGraph ([#7196](https://github.com/aiidateam/aiida-core/pull/7196)).
- Public accessor for gathered `Map` outputs instead of the private `._value` unwrap (M3:490 note).
- Confirm aiida-shell accepts plain relative path strings, so tutorials can drop `Path(...).resolve()` (U1).
- New QueryBuilder filter syntax is already shipped (A1), so it is an adopt-now item, not a wishlist item.

---

## Build / config changes

- `.readthedocs.yml`: add `tree` to `build.apt_packages` (U4). Mirror in `.github/workflows/docs-build.yml` if it installs system packages there.
- Notebook cell tags: audit every `remove-input` / `remove-cell` against X3. Reader-facing cells become visible (fold *output* only); build-only machinery moves into `include/` setup scripts behind a visible `%run`. Module 0 is the first and worst offender.
- Possible new asset: `_static/join_schematic_module5.svg` (A3).

## Open questions to verify

- U7: does the copy button actually render on executed nb code cells on a built page?
- D6: confirm "introduction to about" targets the `index.rst` landing card, not the tutorials index grouping.
- A1: confirm the new filter syntax renders and executes cleanly inside the notebook build (not just in a REPL).
- api-discrepancies open questions 1-4 (run/submit PR merge timing, where error handling lives, WorkChain-vs-WorkGraph comparison boxes, `orm.Dict` wrapping vs plain dicts) still apply and intersect M4-M7.
- M0 gsrd install note: it points at the canonical `github.com/aiidateam/gsrd`, but `pyproject.toml` currently pulls gsrd from the `GeigerJ2/gsrd@fix/dont-raise-on-trivial-state` fork (with a TODO to revert once the PR merges). Should the reader-facing note point at the fork until then, or does `aiidateam/gsrd@main` already behave identically on the bad-input case shown in M0? (Verified locally that the fork gives exit 0 + `ERR: field values departed manifold` + no `results.npz`, matching the prose.)

## Progress log

- **M0 (done, pending your review):** X3 completeness rewrite (all executed cells visible, no fake `console` blocks, noisy `gsrd` runs folded not hidden), X7 visible `tmp/` scratch dir, X1/U8 install note, X4 first `!` note, X5 simpler code (dropped `.resolve()`/`mkdtemp`). Built in isolation with `raise_on_error=True`, outputs match prose. `docs/source/tutorials/tmp/` gitignored. **Deferred to our joint M0 pass:** C1 (trim length), X6 (wording polish), and the gsrd-repo question above.
- **X3 sweep (D10, done + verified):** the profile-setup cell is now visible in all 7 modules and reframed as an isolated sandbox profile (M1). Stale-profile cleanup moved into `setup_tutorial.py`; fixed a pre-existing bug where `get_config()` crashed on a fresh `AIIDA_PATH` (new reader / CI with no `~/.aiida`), now `get_config(create=True)`. M4's 4 CI-container cells folded (`hide-input`), not removed, plus its note reworded. Verified: M1 isolated build green (`raise_on_error`); M1 to M2 chained build shares one profile with 36 processes, so M2's per-module cleanup preserves M1's data. Fixed 3 stale "hidden cell" prose refs (M3 x2). This is a second commit, separate from M0.
- **D6 (done, staged):** `index.rst` landing card "Introduction" to "About", button to "To the overview". Own commit (cherry-pickable to a separate PR).
- **D8 decided:** inline teaching python (calcfunctions/workflow/constants) where taught; keep `include/` for `.yaml` + images + the visibly-`%run` setup scripts; `plotting.py` stays as an acknowledged downloadable helper (user may still ask to inline it). Rides along with each module pass.
- **M1 content pass (done + verified):** install note (X1), dropped `.resolve()` (U1, plain string path), inlined the parsing regex + unfolded that cell (D8/X3), acknowledged `plot_provenance` helper, dump now writes a visible `tmp/dump` (X7). Isolated build green.
- **M2 content pass (done + verified):** install note, inlined `base_params`/`f_values`/`variance_re`/`mean_re` (removed all `include.constants` imports), visible `tmp/` sweep dir (X7), fixed L1 "typed, validated input ports" wording, "grep/regex out" to "read". M1+M2 chained build green. D7 filter-syntax deferred to the M5 pass (its primary home).
- **M3 split (D1, done + verified):** split into `module3a.md` (why + mental model + single pipeline) and `module3b.md` (`Map` sweep + 2D scan) at the natural boundary. Index keeps one "Module 3" card to 3a (no extra panel, per C8); toctree gets 3a/3b; `tutorial:module3` aliased to 3a. Shared code shown folded via `{literalinclude}` in dropdowns (`gray_scott_pipeline`, `make_transition_plot`), imported from `include/`. Fixed L2 ("regexes out"), L3 (WorkChain `ctx` forward ref), L4 ("factory" sentence), install notes, and a `plot_provenance` import the split exposed. Also standardized inlined constants to UPPERCASE across M1/M2/M3 (they are constants; matches `constants.py`). Clean isolated build green (3a 12s, 3b 134s incl. 2D scan).
- **Wording/simplification sweep (X5/X6) deferred (JG, 2026-07-13):** the deeper "tune down technical wording + simplify code" pass (e.g. M3's dense socket/zone prose and the advanced `_get_keys()`/`getattr` inspection cell, the `._value` unwrap) is a *separate cross-module sweep* done AFTER the structural passes, so all wording tuning happens once, consistently. So the per-module structural passes below stay scoped to: split (where applicable), inline/shared-code pattern, install notes, the *specifically-flagged* phrasings, and D-items. General jargon/code simplification is left for the sweep.
- **M4 pass (done; not build-verified, needs SLURM container):** inlined the parsing regexes, install note, L5 "byte-for-byte" to "exactly the same", dropped `.resolve()`, pointed the `gray_scott_sweep` ref to 3b.
- **M5 pass (done):** adopted the new QueryBuilder filter syntax throughout (D7) `orm.<Type>.fields.<name> <op> <value>`, including extras subkeys via `.fields.extras['key']`, verified all forms construct; updated the syntax-explaining prose (noting the dict form still works); inlined `VARIANCE_RE`; install note.
- **M7 pass (done):** install note (D9, `aiida-core` not `aiida`), inlined `BASE_PARAMS`/`F_VALUES`, `gray_scott_pipeline` shown folded, aiida-qe-demo link added to "Where to go next" (D5).
- **M6 split (D2, done):** split into `module6a.md` (If + While) and `module6b.md` (If-in-Map + adaptive sweep). Index keeps one "Module 6" card to 6a; toctree gets 6a/6b; `tutorial:module6` aliased to 6a. Reused `pipeline_with_optional_fft` re-shown folded in 6b (separate kernel); inlined constants; L3 (three WorkChain-`ctx` refs) removed; `fft_peak_wavelength` shown folded.
- **Still to do:** D4 quickstart page (net-new, deferred), then the cross-module wording/simplification sweep (X5/X6).
- **Verification:** M5/M7 via a M1->M2->M5->M7 chained build; 6a/6b via a standalone chained build. M4 cannot be build-verified locally (needs the SLURM container).
