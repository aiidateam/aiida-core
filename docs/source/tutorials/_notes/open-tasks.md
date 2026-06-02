# Open tutorial tasks

In-flight session tracking. Module-level TRACKING.md remains the canonical content checklist; this file holds the granular work items + their state. Update both when something lands.

## Module 1

- [ ] **#17 `verdi shell` subsection** — address TODO at `module1.md:250-251`. Short subsection introducing `verdi shell` for interactive DB exploration (load nodes by PK, inspect attributes, follow links).
- [ ] **#18 Handling failures section** — address TODO at `module1.md:276-278`. Re-run with bad params (`F=0.1`), show AiiDA records the failed CalcJob (exit code, stderr in provenance), contrast with Module 0 where the failure left no trace.

## Module 3

- [ ] **#19 `summary_plot` SinglefileData dereference** — address TODO at `module3.md:434-442`. `wg_sweep.outputs.summary_plot.value` currently returns `None`; settle the correct access path with aiida-workgraph upstream, then uncomment the cell that displays the transition-curve PNG.

## Module 4

- [ ] **#12 `verdi computer/code search` mention** — forward-looking only. JG has an unreleased PR adding the endpoint. Until it merges + releases: mention as "coming", do **not** demo.
- [ ] **#16 Code-registry vs resource-registry merge view** — one or two sentences (likely inside the existing dropdown around `module4.md:144-170`) noting that `aiida-code-registry` and `aiida-resource-registry` overlap and (JG view) should be merged. Light touch; don't present them as two separate stable things.
- [ ] **#14 Promote Module 4 index card** — content side is now done. Update `docs/source/tutorials/index.md:140` to swap the Module 4 `*Coming soon*` placeholder for an active `button-ref` pointing at `tutorial:module4`.

## Cross-cutting

- [ ] **#20 Compare new modules against `basic.md`** — per 2026-05-12 boss notes. Diff modules 0-4 against legacy `tutorials/basic.md`, capture findings in TRACKING.md cross-cutting section.

---

## Recently completed

- [x] **#8 Module 2 Extras subsection** — `module2.md:330-345`.
- [x] **#9 Module 2 Groups subsection** — `module2.md:347-368`.
- [x] **#10 Module 2 built-in data types table** — `module2.md:170-181`.
- [x] **#15 Module 4 SLURM container timeout** — cherry-picked `8f8d816a0` (PR #7380, asyncssh+StrictHostKeyChecking) onto the docs branch. Uncommented the remote-submission sections; added a fail-fast cell after `verdi computer test` so silent connection failures don't hide behind notebook timeouts. Module 4 builds clean in 9.2s.
- [x] **Module 4 production-ready additions** — added per-calculation scheduler options (`metadata.options`: resources / queue_name / account / max_wallclock_seconds), production-rate-limit warning (`--safe-interval`, `set_minimum_job_poll_interval`), computer-level `prepend_text`/`append_text` tip, `verdi code test` cell, multi-computers-per-profile prose.

Plus closed-as-superseded:

- ~~#11 ship CSCS registry YAMLs~~ — superseded by the xenonmiddleware/slurm path.
- ~~#13 xenonmiddleware/slurm "run it for real" dropdown~~ — decided + implemented, now the primary live path.
