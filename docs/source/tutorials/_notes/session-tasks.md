---
orphan: true
---

# Session task tracker

Living checklist for the current batch of tutorial work. Updated by Claude as items land.

## In flight

- [x] **M7 implementation landed** at `tutorials/module7.md` (594 lines). All six planned sections live, all four JG open questions resolved in the implementation:
  - Title: "Where to go next" (JG's pick).
  - Error-handling demo: synthetic instability (`dt = 10.0`), `add_error_handler` halves `dt`, ShellJob retries successfully. Both attempts in provenance.
  - Caching demo: single-ShellJob *and* sweep variants, both with timing comparison and `cached_from` column shown via `verdi process list`.
  - Plugin cards: kept in M7 (per JG); domain-plugins card is short and points at `reference:core_plugins` plus the 2024-12-13 blog post on non-domain-specific plugins.
  - Closing pointers: Discourse (not Slack), CONTRIBUTING.md (not the archived aiida-tutorials site), per JG's notes.
- [x] **M7 expanded plan** drafted at `_notes/module7-plan.md`. Six proposed sections: (1) Error handling, (2) Beyond aiida-shell &mdash; writing a CalcJob plugin, (3) A note on WorkChain, (4) Caching, (5) The plugin ecosystem as a grid of cards (aiida-project, aiida-hyperqueue, AiiDAlab, domain plugins, submission-controller, code-registry), (6) Where to go next. Plus four open questions for JG (module title, error-handling demo concreteness, caching demo scope, plugin-card placement).
- [x] **`tutorials/index.md` Module 7 card** updated: title "Where to go next", description rewritten (error handlers, CalcJob plugins, WorkChains, caching, plugin ecosystem), "Coming soon" replaced with a live `button-ref` to `module7`.
- [x] **KISS audit** across M3, M5, M6.
  - Refactored: M6 adaptive-sweep coarse+refined plotter (28 lines, hide-input, pure plotting) &rarr; new `plot_adaptive_sweep(coarse_variances, refined_variances)` in `include/plotting.py`. M6 cell collapses to a two-line import + call.
  - Left inline (pedagogical): M3 `wg_preview` introspection cell (teaches `.inputs` / `.outputs` / `.tasks` access), M6 `descendants` diff cell, M6 iteration-recovery cell (teaches provenance traversal), M3 `param_sweep` dict comprehension (trivial). All remain behind their existing `hide-input` toggles.
  - No further candidates found in M5.
- [x] **M3 `summary_plot` dereference** (line ~500). Smoke test confirmed `wg_sweep.outputs.summary_plot.value` now returns the `SinglefileData` correctly (must have been fixed in a more recent aiida-workgraph). Uncommented the block, dropped the TODO comment. The transition curve PNG is now embedded inline at the end of the sweep section.
- [x] **`TRACKING.md` update** &mdash; landed under Module 1 (`verdi shell` tick), Module 3 (workflows.py + viz cells + 2D scan + summary_plot embed), Module 6 (help cells + viz cells + ctx + get_current_graph admonitions + FFT plot), and Cross-cutting (`workflows.py` addition, new plotting helpers, gsrd `TrivialStateError` removal).
- [x] **M1 `verdi shell` subsection** added as a foldable `:::{tip} :class: dropdown` admonition right before the "Dumping calculation data" section. Covers `load_node`, output/input traversal, and `QueryBuilder` usage, frames it as the day-to-day shell alternative to the `%load_ext aiida` Jupyter setup.
- [ ] **M1 / M2 sanity check** after the gsrd `TrivialStateError` removal. Both use safe default parameters so should be unaffected, but worth re-running once.

## Pre-existing RTD blocker, fix queued upstream

- [x] **Admonition syntax fix** (`-W` blocker, pre-dated M7): M1:261, M6:60, M6:344 used `:::{tip}/:note: <title>` *with* a `:class: dropdown` option, which sphinx-design treats as "splitting content across first line and body with options" and emits a warning. RTD's `-W` turned every one of those into a hard fail. Converted to plain `:::{dropdown} <title> :icon: info` across M1, M6, and the five new M7 admonitions. Local `sphinx-build -W --keep-going` on M1+M6+M7 succeeds.
- [ ] **M3 2D heatmap crash on RTD** &mdash; this one is upstream of the docs build. RTD pins `gsrd@main = 568d521`, which still raises `TrivialStateError` on trivial-state grid points. M3's 2D F-k scan is designed to *straddle* the pattern-forming boundary, so several iterations land in the trivial regime, raise, ShellJob exits 303, the WorkGraph `Map` drops the entire gather, and `plot_2d_variance_heatmap` raises "No positive variance values to plot". The fix (remove the `TrivialStateError` raise) is committed locally in `~/aiida_projects/aiida-dev/git-repos/gsrd` but **not pushed to `aiidateam/gsrd:main`**. JG will branch + push + open a PR (commit msg drafted in `gsrd/COMMIT_EDITMSG`); RTD picks up `gsrd@main` automatically once merged.

## Resolved this session

- [x] M6: `namespace` import missing for `adaptive_sweep` return annotation &mdash; added to the `Map, dynamic` import line.
- [x] M3: `wg_2d.run()` timing out at 120s &mdash; bumped frontmatter `execution.timeout` to 300s.
- [x] M6: parenthetical "aiida-workgraph calls these *zone tasks*..." converted to a foldable `:::{tip} A note on terminology :class: dropdown` admonition.
- [x] M6: "What you will learn" bullets 2 and 3 generalised away from the F-sweep / "adaptive sweep" / "physics" example-specific phrasing.
- [x] M6: extended the central `:::{important}` mental-shift admonition with "building the graph and running the graph are separate steps; inside a `@task.graph()` body you are handling sockets, not values".
- [x] Moved the build-vs-run / sockets-vs-values framing to **Module 3** (where WorkGraph is first introduced) by expanding the existing `:::{important}` admonition. Trimmed the M6 admonition to its M6-specific content (control-flow regions) with a back-reference to M3.
- [x] M6: replaced the `pprint` output with a compact comma-joined diff (`Only in F = 0.040: fft_peak_wavelength`), making the pedagogical point of the `If`-gated FFT explicit.
- [x] **FFT plot**: new `plot_fft_spectrum(results_npz)` helper in `include/plotting.py` &mdash; 2D power spectrum + radial profile with peak annotation. Wired into M6 right after the descendants-diff cell, fed from `wg_strong`'s `ShellJob.outputs.results_npz`.

## Pre-existing build warnings (NOT regressions, flagged for the user)

- `howto/archive_profile.md`: hardcoded path `/home/geiger_j/dev/aiida-dev/aiidateam/aiida-core.worktrees/feature/cheat_sheet/docs/source/howto/process.aiida` &mdash; refers to a different worktree, doesn't exist here. Pre-existing, unrelated to tutorial work.
- `tutorials/module4.md`: SSH transport to `127.0.0.1:5001` fails because the SLURM service container isn't running. M4 is built live against `xenonmiddleware/slurm`; the user runs the container locally before building M4.
