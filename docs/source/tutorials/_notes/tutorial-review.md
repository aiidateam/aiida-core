# Tutorial self-review — candidate improvements

Covers modules 0, 1, 2, 3 and cross-module concerns. Each item is a candidate, not a decision. Resolved items are kept around with `~~strikethrough~~` and a dated note so context isn't lost. Add `> JG:` comments under each item to record your take.

---

## Module 0

### Prose / content

- **M0-A. The "real-world scale" bullets (lines 218-225) overlap strongly with "How AiiDA solves these problems" (233-239).** Each pain point has a near-1:1 mapping to an AiiDA solution. Options: cut the most redundant 2-3 (e.g. "Scattered data", "Code versions", "Post-processing at scale"), or fold the two sections into one bullet list of "problem → AiiDA's answer".
  > JG:

- **M0-B. Lines 145-154 — the `:::{note}` ("During the exploratory phase…") and the `:::{admonition} warning` ("No systematic record…") sit back-to-back saying related things.** Fold one into the other, or drop the note.
  > JG:

---

## Module 1

### Prose / content

- **M1-A. Line 238 feels misplaced.** *"From the command line, `verdi calcjob gotocomputer <PK>` SSHes into the Computer..."* sits inside `### From Python` but talks about a CLI command. Move to `### From the command line`, or drop it.
  > JG:

### Pedagogy / output

- **M1-B. `verdi process show` output (line 206) is long but pedagogically essential — keep visible. No fold.**
  > JG:

---

## Module 2

### Structural / flow

1. ~~**"What you will learn" bullets don't mirror section headings.**~~ *Resolved 2026-05-12.* Kept the (already-reworked) bullets and aligned section headings to them. Dropped the vague 4th bullet ("Run a parameter sweep with richer provenance") since bullets 1-3 cover the new concepts; the sweep is the application.
   > JG:

2. ~~**"### The idea" is a weak subsection title.**~~ *Resolved 2026-05-12.* Split into `### Structured data nodes` (mirrors bullet 3) and `### Tracking Python steps with @calcfunction` (mirrors bullet 2). Connector sentence updated.
   > JG:

3. ~~**Hierarchy mismatch:** "Structured data nodes" was a subsection of "Richer provenance with calcfunctions" but the bullets list them as siblings.~~ *Resolved 2026-05-12.* Lifted `Structured data nodes` to top-level, renamed the parent → `## Tracking Python steps with @calcfunction`, swapped bullets 2 and 3 (data motivation first, mechanism second).
   > JG:

4. ~~**The "Compare this to the first sweep" beat appears twice**~~ *Resolved 2026-05-12.* Dropped the second (redundant) phase-transition plot — same F values through the same simulation give an identical curve. Replaced the trailing "Compare this to the first sweep…" paragraph with one sentence noting the curve is the same but the *access path* changed (`Float` nodes from the database instead of YAML file parsing).
   > JG:

### Prose tightening

5. **The `:::{important}` block at line ~141** over-explains. The `file in → ShellJob → file out` diagram works; the surrounding sentences can be trimmed.
   > JG:

6. **Line ~53** ("Let's start varying our simulation parameters: scan the feed rate `F`...") is slightly stilted. Could collapse to one sentence.
   > JG:

7. **The `note` at lines ~202-211 is long — three paragraphs.** Candidates:
   - Paragraph 1 (params are nodes inside calcfunctions) stays as a 1-line callout.
   - Paragraph 2 (auto-serialize) is already footnoted; trim to one sentence.
   - Paragraph 3 (Dict vs Float/Int) speculates about an alternative the reader didn't ask for — cut or move to a `:::{tip}`.
   > JG:

### Content / pedagogy

8. **The QueryBuilder tip (current line ~320) is currently theoretical** — just code in a tip box. Running an actual query (`qb.append(...).all()` returning two rows) would land the "queryable results" payoff harder. Also addresses the inline TODO about benchmarking retrieval at scale.
   > JG:

9. **`enriched_nodes = [(f_val, parsed), ...]`** would be slightly cleaner as a list of dicts (mirror `sweep_results` above), or unify the two structures.
   > JG:

10. **The footnote `[^data-types]` and the "built-in data types" TODO overlap.** Either keep the footnote and drop the TODO, or land the table now.
    > JG:

11. ~~**Add `verdi process show` for the enriched single-run pipeline (CalcJob + calcfunction).**~~ *Implemented 2026-05-12, revised same day.* First attempt added two cells (calcjob + `parse_output`), but the calcjob view was structurally identical to module 1's process show — same input/output labels, no visible creator/consumer linkage — so it added nothing pedagogically. Final state: one cell showing `parse_output` as a first-class process node with `Float` outputs, which is the genuinely new content.
    > JG:

### Pedagogy / output

12. ~~**Hide the first `%verdi process list -a` output (line ~138).**~~ *Resolved 2026-05-12.* Added `:tags: ["hide-output"]` so the output is collapsed by default, matching the closing `%verdi process list -a -p 1` cell.
    > JG:

### Minor

13. **Line ~70:** `f'input_F{f_val}.yaml'` produces `input_F0.04.yaml` — the dot is ugly. Use `.replace('.', '_')` like module 3 does for sweep keys.
    > JG:

14. **`## Footnotes` empty heading at the end** (same in module 1) — confirm it's intentional rather than leftover from a previous structure.
    > JG:

15. ~~**Too many `###` subsections under `Tracking Python steps with @calcfunction`.**~~ *Resolved 2026-05-12.* Dropped all four subsection headings, replaced with prose connectors. Matches module 1's pattern of using `###` only for genuine categorical splits.
    > JG:

---

## Module 3

### Structure / heading

- ~~**M3-A. Drop `## Summary` for consistency.**~~ *Resolved 2026-05-12.* Dropped Summary heading + bullets; kept the `:::{seealso}` as a standalone admonition before `## Next steps`.
  > JG: apply!

- ~~**M3-B. Too many `###` subsections under `## Turning the for-loop into a workflow`.**~~ *Resolved 2026-05-12.* Dropped all four (`The problem with loops`, `Using Map`, `Running and inspecting the sweep`, `Analyzing results`); replaced with prose transitions.
  > JG: apply

- ~~**M3-C. `## Building the workflow` has 4 subsections.**~~ *Resolved 2026-05-12.* Dropped all four (`Preparing tasks and inputs`, `Defining the graph task`, `Two ways to use a graph task`, `Running and inspecting`); replaced with prose transitions ("With the tasks wrapped...", "`gray_scott_pipeline` is now a factory...", "For now, let's exercise the standalone form...").
  > JG: apply

- ~~**M3-D. "What you will learn" has 5 bullets vs 3 in modules 1/2.**~~ *Resolved 2026-05-12.* Compressed to 3 bullets matching modules 1/2 cadence: build a workflow, inspect hierarchical provenance, map over parameter sets.
  > JG: apply

### Length / density

> JG: General comment here: this is on purpose quite lengthy, to explain the new concepts, and motivate / explicitly explain the way workgraph works. i want user to really understand it, and be able to construct their own workflows after this module!

- ~~**M3-E. The two `:::{dropdown}` blocks (lines 190-213 and 215-279) together add ~100 lines of optional detail.**~~ *Resolved 2026-05-12.* "Declaring graph-level inputs and outputs explicitly" dropped entirely; replaced with footnote `[^explicit-io]` on `@task.graph` pointing to the aiida-workgraph docs. "Peeking inside the graph" inlined as a runnable code cell with condensed prose (build + 1 print, 3 takeaways), `demo_graph` aside dropped (its point is covered by the `:::{important}` block at the top of the WorkGraph mental-model section).
  > JG:  maybe the "declaring graph-level inputs and outputs explicitly" can be made a footnote? or, if we don't need it here at all, we just refer to the aiida-workgraph documentation?

- ~~**M3-F. Inline comments in the Map sweep code cell (lines 362-377) are heavy.**~~ *Resolved 2026-05-12.* First cell: 11-line comment block trimmed to one line; the genuinely unique "why plain dicts, not orm.Dict" point lifted to prose just above the cell. Second cell: 3 inline comment blocks trimmed to one short comment about `map_zone.item.value`.
  > JG: yes, agreed, best to move them out of the code

- ~~**M3-G. The three-step pipeline named 4 times in prose.**~~ *Resolved 2026-05-12.* Trimmed line ~266 (post-provenance-graph) from "the workflow clearly shows that prepare_input, the simulation, and parse_output are part of a single logical operation" to "the workflow clearly shows the three steps as part of a single logical operation". One explicit chain mention remains in "Why workflows?" (line 53) where it's needed to recall the Module 2 pipeline.
  > JG: ok, agreed. apply as you deem best.

### Cell output / folding

- ~~**M3-H. The single-run `%verdi process show` — keep visible.**~~ *Confirmed 2026-05-12* — no change.
  > JG: good

- ~~**M3-I. Map sweep cell, sweep `process status`, sweep `process show` are all already `hide-output`.**~~ *Reviewed 2026-05-12* — the sweep `process status` was subsequently **unhidden** as part of M3-J (it's now the closing visual of the section). Sweep cell and sweep `process show` remain hidden.
  > JG: good

- ~~**M3-J. The transition curve plot at the end is the *third* identical curve in the tutorial.**~~ *Resolved 2026-05-12.* Dropped the closing plot. Unhid the sweep `verdi process status` so the hierarchical tree (1 sweep workflow → 8 sub-workflows × 3 steps each) is the new closing visual. Reordered: print loop with variance values first (numbers same as Module 2's sweep), then the visible `process status` driving home the *structural* difference, then a tip about how to explore the full graph interactively. Sweep `process show` still hidden (long output, not needed here).
  > JG: yes, drop the plot... and, verdi process status should be shown in this module at least once, for sure!

### Prose tightening

- ~~**M3-K. "Preparing tasks and inputs" section has a lot of text before the first code cell.**~~ *Resolved 2026-05-12.* Compressed the prose between import cell and wrap cell from ~10 lines (intro + numbered list + two paragraphs) to 2 short paragraphs covering the core idea (`task()` wraps to defer + returns socket-bearing handle) and the prepare_input-vs-parse_output distinction. Also trimmed the code-cell's 9-line comment block to a 2-line note on the `*_task` naming convention.
  > JG:

- ~~**M3-L. Lines reintroduce `verdi process show` as a "companion command".**~~ *Resolved 2026-05-12, revised same day.* Final wording (after JG correction): "We can again use the familiar `verdi process show` command here to get a full overview of the workflow. It shows the individual steps as well as the graph-level inputs and outputs we declared." Acknowledges recurrence with "again use the familiar"; names what's new (individual steps + declared graph-level I/O).
  > JG:

### Content / pedagogy

- **M3-M. Add a `verdi process show` of one *sub-node* (e.g. the ShellJob inside the WorkGraph).** Same logic as we just did in module 2 — currently the reader only sees `verdi process show` on the *top-level* workflow node. Showing that a child step is still a first-class process node, but now has a `caller` pointing to the workflow, would land the hierarchical-provenance point textually, complementing `plot_provenance`.
  > JG:

- ~~**M3-N. No footnotes pointing to deeper docs.**~~ *Resolved 2026-05-12.* Added four footnotes total: `[^workflows-topic]` on "workflow" → `topics:workflows`; `[^explicit-io]` on `@task.graph()` → aiida-workgraph docs; `[^calcjobs]` on `ShellJob` recall → `topics:calculations:concepts:calcjobs`; `[^calcfunctions]` on calcfunctions recall → `topics:processes:functions`. Also added the `## Footnotes` heading at the end of the module for sphinx-footnote rendering, matching modules 1 and 2.
  > JG:

### Inconsistencies

- ~~**M3-O. `&rarr;` HTML entity vs `→` Unicode mix.**~~ *Resolved 2026-05-12.* Per JG preference, kept `&rarr;` (easier to type on standard keyboards). Added missing backticks around `ShellJob` in the same line for consistency with the other component names.
  > JG: i prefer html bc that's easily type-able on a normal keyboard. fix!

- ~~**M3-P. `@task.graph()` (with parens) vs `@task.graph` (no parens) mix.**~~ *Resolved 2026-05-12.* Standardized on `@task.graph()` with parens everywhere — matches the code-cell convention (where parens are explicitly used and known to work). Updated prose mentions to also use parens.
  > JG: what is the common way to apply decorators? with or without? depending on that, let's use that. make it consistent, then

- ~~**M3-Q. `## Setup` — same name as module 2 (also flagged as CM-A).**~~ *Resolved 2026-05-12.* Dropped the `## Setup` heading entirely; the one-line prerequisite reminder is now a `:::{note}` admonition right after "What you will learn". Same change applied to module 2.
  > JG:

- ~~**M3-R. `## Next steps` at the end is generic.**~~ *Resolved 2026-05-12.* Rewrote to acknowledge the reader has the core building blocks now, then list modules 4-7 as independent threads ("can be tackled in whatever order matches your needs"). Each bullet names the focus: advanced patterns (4), remote HPC (5), QueryBuilder (6), error handling (7).
  > JG: yes, apply. keep in mind that after this module, they don't necessarily have to be followed in order. people can continue with advanced workflows, if that's what they want to do, or go to remote submission, if they need to go to HPC.

---

## Cross-module

- ~~**CM-A. Setup section names differ.**~~ *Resolved 2026-05-12.* Decided not to harmonize — module 1's `## Setting up your AiiDA profile` is genuine teaching content; modules 2/3 only needed a one-line prerequisite reminder, so their `## Setup` headings were dropped in favour of a `:::{note}` admonition. Asymmetric heading structure now matches asymmetric content depth.
  > JG:

- **CM-B. Module 0 has no `## What you will learn`** while modules 1, 2, 3 do. Probably intentional (module 0 is motivational, not pedagogical), but worth confirming, or adding a one-liner for symmetry.
  > JG:

- **CM-C. Module 1: `python_code` comes "out of nowhere"** in the first `launch_shell_job` call. ~~Add a footnote explaining where it comes from.~~ *Implemented 2026-05-12* (`include/setup_tutorial.py` creates it via load/fallback `InstalledCode`).
  > JG:
