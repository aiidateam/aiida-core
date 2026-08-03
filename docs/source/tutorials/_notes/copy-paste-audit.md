---
orphan: true
---

# Copy-paste self-containment audit

Lens: a reader who **creates their own fresh Jupyter notebook and copy-pastes the
code-cell contents** (not a repo clone, not the downloaded `.ipynb`). Do the cells
run, make sense, and stand alone?

Source: three parallel deep-reads (M0-M2, M3a-M4, M5-M7), each verifying against
`pyproject.toml`, the build venv, and (for the crash claims) actual execution.

**Verdict:** the bootstrap fixed *code* self-containment, cell ordering is clean
everywhere, and there are **no hidden load-bearing cells except in M4 and M6b**. The
real blockers are now (1) the **install instructions** (missing `matplotlib` and
`gsrd`), (2) **M5** which recreates no data and hard-crashes on an empty DB, (3) two
**`hide-input` cells that later visible cells depend on** (M6b, M4), and (4) **M4**
needing a SLURM container + repo key it can't get.

---

## Cross-cutting: install-instruction gaps (highest impact)

These hit almost every module because the docs build venv has extras a reader's
`uv pip install ...` line does not.

- **[BLOCKER] `matplotlib` is never in an install note.** `include/plotting.py`
  imports `matplotlib.pyplot` at module top level, so *any* `from include.plotting
  import ...` raises `ModuleNotFoundError`. It affects **M1, M2, M3a, M3b, M5, M6a,
  M6b** (all import `include.plotting`). `matplotlib` lives in aiida-core's
  `atomic_tools` extra (in the build venv, so CI is green), not in
  `aiida-core aiida-shell [aiida-workgraph]`. Fix: add `matplotlib` to every install
  note that plots.
- **[BLOCKER] `gsrd` is missing from the M1-M7 install notes.** Only M0 has
  `uv pip install git+https://github.com/aiidateam/gsrd`. M1-M7 list only
  `aiida-core aiida-shell [aiida-workgraph]` (M5: just `aiida-core`). Without the
  `gsrd` binary, `setup_tutorial.py` raises `RuntimeError` in the setup cell. It is
  self-explaining (the error prints the pip line) but avoidable. Fix: add the `gsrd`
  install to every module's note.
- **[FRICTION] `plot_provenance` needs the Graphviz *system* binary (`dot`).** The
  `graphviz` Python package is a core dep, but `dot` is not; without it the
  provenance-graph cells raise `ExecutableNotFound`. Affects M1/M2 (and any
  `plot_provenance` use). Fix: note `apt install graphviz` / `brew install graphviz`
  / `conda install graphviz` near the first graph cell.

Suggested one-liner for the plotting modules:
`uv pip install aiida-core[atomic_tools] aiida-shell aiida-workgraph git+https://github.com/aiidateam/gsrd`
(plus a system-Graphviz note). M5 additionally needs `aiida-shell` (its setup builds
`gsrd_code`).

---

## Module-specific blockers

### Module 5 — not self-contained; hard crash on empty DB  [BLOCKER]
M5 **creates zero data**: every cell is a read-only `QueryBuilder` query or a plot of
query results. It depends entirely on **Module 2**'s Float nodes, `sweep='F_scan'`
extras, and the `tutorial/F-sweep` Group (and incidentally M3's sweep).
- `module5.md:353` `f_values, variances = zip(*rows)` with `rows == []` →
  `ValueError: not enough values to unpack`. A hard traceback, not just empty output.
- L91-92, L101-136, L165-222: queries return empty standalone; the surrounding prose
  ("the number is higher than eight", "returns only the Module 2 sweep") is then false;
  `tutorial/F-sweep` Group doesn't exist in a fresh profile.
- The intro note (L19-29) *does* disclose the M1/M2 dependency, so a reader is warned,
  but it neither prevents the empty results nor the L353 crash.
- Fix options: (a) at minimum, guard the L353 unpack and add "run M2 first or you'll
  see empty results"; (b) better, have M5's setup re-run a small F-sweep so it stands
  alone. (a) is cheap; (b) matches "self-contained".

### Module 6b — load-bearing code hidden from copy-paste  [BLOCKER]
- `module6b.md:87-102` (`hide-input`) redefines `pipeline_with_optional_fft`, and the
  **visible** `conditional_sweep` cell (L111-135) calls it (L120/L131). A reader who
  copies only visible cells gets `NameError: pipeline_with_optional_fft`. The prose at
  L85 even claims "repeated here (folded) so this notebook runs standalone", which
  `hide-input` defeats. Fix: change L88 `hide-input` → `hide-output` (show the code).

### Module 4 — remote module, three blockers  [BLOCKER x3]
M4 is remote-HPC submission; it is *not* meant to run without a cluster, but it should
fail gracefully and its non-remote cells should still work.
- Live cells need the tutorial's **SLURM Docker container** (`xenonmiddleware/slurm`,
  SSH port 5001) **and the repo SSH key** `.github/config/slurm_rsa`, which
  `_ensure_tutorial_helpers` does *not* fetch (it only pulls `include/`). A copy-paste
  reader has neither → `verdi computer test` / transport / `launch_shell_job` fail or
  hang. Fix: an upfront admonition that the remote cells only run against your own
  SSH-reachable cluster.
- `setup_slurm.py:46` `repo_root = pathlib.Path(__file__).resolve().parents[5]` runs
  *before* the container-reachable guard and raises `IndexError` for any notebook path
  shallower than 6 components (verified). Even on a deep path it points at the wrong
  dir. Fix: move/guard the key-path derivation inside the reachable branch.
- `module4.md:405` (`hide-cell`) is the ONLY definition of `node`/`results`, but the
  visible cell at L519-520 and the `hide-output` cell at L537 depend on `node` →
  `NameError`. Fix: make the `launch_shell_job` payoff cell a normal visible cell.

### Module 1 — `!tree` absent by default  [BLOCKER]
- `module1.md:326` `!tree /tmp/aiida-tutorial/dump` needs the `tree` binary, absent on
  macOS, minimal Linux, and Windows. Fix: `!find`, Python `os.walk`, or `!ls -R`
  (apt-installing `tree` fixes the docs build but not a reader's laptop).

---

## Friction (works, but rough for copy-paste)

- **[FRICTION] M6a: three `hide-input` cells show output a reader can't regenerate**
  (L210-234 helpers+table, L242-253 FFT plot, L428-447 n_steps/variance table). Not
  load-bearing for later *visible* cells, so not crashes, but the visible output isn't
  reproducible without expanding the fold. Fix: `hide-input` → `hide-output`.
- **[FRICTION] Unix-only shell escapes + hardcoded `/tmp`** in M0 (`!mkdir`, `!cp`,
  `!cd … && gsrd`, `!ls`), M1, M2. Break on native (non-WSL) Windows. Fix: mention WSL,
  or use `pathlib`/`tempfile`.
- **[FRICTION] M4** L443 `hide-cell` parsing block also depends on `node`; a
  visible-only reader misses the "results identical to Module 1" demonstration.

## Cosmetic

- **M2 / M3a "run Module 1 first" notes overstate the prerequisite.** Both setup cells
  recreate the profile + `gsrd_code` idempotently and (M2) re-run their own sweep, so
  they are standalone. Soften to "the setup cell recreates everything; Module 1 first
  is optional." (M2 note: L28-30; M3a note: L28-38, also drops a "downloaded notebook"
  reference irrelevant to copy-paste.)
- **M0**: `{image} include/reaction-diffusion-fields*.png` (L34, L194) aren't fetched
  by the input-fetch cell; broken only if a reader also copies the markdown. Optional:
  fetch the two PNGs alongside the YAMLs.
- **M3a** L176 `prepare_input_task = task()(prepare_input)` defines vars no later cell
  uses and differs in form from `workflows.py` (`task(prepare_input)`); mildly
  confusing, harmless.

---

## Recommended fix order

1. **Install notes** (matplotlib + gsrd on every module; Graphviz system note). One
   sweep, unblocks 7 modules. Cheap, highest impact.
2. **M6b** `hide-input` → `hide-output` at L88. One-line, removes a NameError.
3. **M5** guard the L353 unpack + strengthen the note (cheap); decide separately
   whether M5 should re-create a small sweep to be truly standalone.
4. **M1** replace `!tree` with a portable listing.
5. **M4** upfront remote-only admonition; make the `node` cell visible; guard
   `setup_slurm.py` `parents[5]`.
6. **M6a** `hide-input` → `hide-output` on the three output-reproducibility cells.
7. Cosmetics: soften M2/M3a prerequisite notes; optional M0 image fetch.

Clean throughout: cell ordering (setup always first), no cross-module data reads
except M5, no hidden load-bearing cells except M6b/M4.
