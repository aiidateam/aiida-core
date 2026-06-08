# Full readthrough &mdash; Module 2

- [x] did we create a `python_code`? now it's `gsrd_code`, or just `gsrd`? previously, we didn't have a proper `gsrd` package, so we were using a `python` code. can you fix here, and check if this text is also still outdated in the other following modules?
    - fixed in mod2 (line 26), mod3 (line 26), and mod6 (line 20): `python_code` &rarr; `gsrd_code`. Confirmed via `grep -n 'python_code' module*.md` (now 0 hits). The `setup_tutorial.py` already creates the `gsrd_code` variable with label `gsrd@localhost`, consistent across all modules.

- [x] before this code snippet:
  "# Plot variance_V vs F to show the phase transition. ..."
  add some prose. otherwise it's just code and more code, without comments...
    - added a lead-in: "Plotting `variance_V` against `F` shows what we are after: a sharp drop somewhere along the swept range, marking the boundary between the 'pattern forms' and 'pattern dies out' regimes:"

- [x] We reference `gsrd_code` before, but `verdi process list` shows `gsrd@localhost`: `5  28s ago    ShellJob<gsrd@localhost>       ⏹ Finished [0]` which one is it?
    - clarified in M1 (the variable's single source of truth) by extending the intro to: "...a pre-registered `gsrd_code` object: an `InstalledCode` pointing at the `gsrd` CLI binary, set up by the hidden cell above (see `include/setup_tutorial.py`) and registered under the AiiDA label `gsrd@localhost` (which is what you will see in `verdi` output later on; the Python variable `gsrd_code` is just a local handle for the same Code object)."

- [x] maybe, before dropping this, show again the provenance graph of one run:
  "What if, instead of just files in and files out, we could register the simulation's inputs and outputs as structured AiiDA data nodes?"
  and highlight that all inputs and outputs are just files at that point. Then use the sentence there rn, about making it tracked structured aiida data nodes?
    - added a `plot_provenance(calc_nodes[0][1])` cell right before the "Structured data nodes" header, plus the framing prose: "Every input and every output is a `SinglefileData` blob &mdash; the YAML on the left, `results.npz` and `stdout` on the right. The simulation ran with full provenance, but as far as the database is concerned, the values that we actually care about are buried inside opaque files." Then the next H2 leads with "What if we could register the simulation's inputs and outputs as **structured AiiDA data nodes** instead?"

- [x] "types like Dict, Float, Int, Str, List, and SinglefileData " -> (and more)
- [x] include also "RemoteData" in that table row: Opaque binary or text files, directory trees
    - extended the Files row: `SinglefileData`, `FolderData`, `RemoteData`; "Opaque binary or text files, directory trees, pointers to files on a remote machine".

- [x] "Let's write two: one for input preparation, one for output parsing." -> "Let's write two: one for input preparation, and one for output parsing."
- [x] Mention around this snippet here:
  "# Define prepare_input: a calcfunction that converts a Dict to a YAML file. ..."
  that, to achieve this, we first express the parameters as a dict / Dict, and then dump them to the input file. this is common, the binaries often use input files, but the preparation (if done through python) holds the values as variables (dicts, with floats, ints, etc., lists, etc)
    - added the framing prose above the cell: "The first, `prepare_input`, bridges the two natural representations of a simulation's parameters: the dictionary of typed values we want to *think* in (floats, ints, strings) and the YAML input file the binary actually *reads*. Most scientific codes take an input file on disk, but the values that drive them naturally live as Python variables (dicts, floats, lists). Doing the conversion inside a `calcfunction` keeps both representations in the provenance graph: the `Dict` is queryable, the rendered file is what `gsrd` consumes."

- [x] maybe we show those once, where they are first used, but then not anymore, and just refer to the fact that we use those regex?
  "_VARIANCE_RE = re.compile(r'Variance of V field\s*:\s*([\d.eE+-]+)')
  _MEAN_RE = re.compile(r'Mean\s+of V field\s*=\s*([\d.eE+-]+)')"
    - defined `_VARIANCE_RE` *and* `_MEAN_RE` in the early manual-sweep block (with a comment "we reuse them later when we promote the parser into a calcfunction"); removed the redefinition in `parse_output` (cells share state in IPython/jupyter-book, so the names carry over). Added a comment in `parse_output` saying so.

- [x] maybe we can make this more readable? first assing the variables, and then on the return wrap them in orm and construct the dict, rather than doing everything inline in the return?
    - assigned `variance_v` and `mean_v` as plain floats first, then constructed the return dict with the `orm.Float(...)` wrappers on the right-hand side. Cleaner stack of two reads + a single return.

- [x] this reads weird: "This is the small price of wrapping a code that prints headline numbers only to stdout: a custom parser." what's the point? -> i'd say it's common to write parsers, no? the alternative would be to have some structured, schema-based output format, rather than just plain text...
    - rephrased to: "Writing a small parser is a common cost when wrapping codes that emit their results in unstructured text (the alternative being a schema-defined output format like XML or HDF5, which not every code provides). What is new here is that the parser itself becomes a tracked AiiDA process..."

- [x] "Now chain them:" -> "Now, we can chain them:"

- [x] In this section "Organizing your results", maybe we should have better introductions to the subsections, e.g., extras, Groups, etc., why would one use those, what do they add? (edit: well, i see the motivation is always written at the end. so, it's not missing, but, it would make the transitions into the topics nicer, if the motivation for covering these topics would be put at the beginning)
    - rewrote the section so the motivation leads each subsection. Added a top-level intro paragraph ("three needs show up: tagging, bundling, searching &mdash; one tool each") and rewrote Extras and Groups so the *why* (post-hoc tagging / bundling related runs) comes before the *what* / *how*.

- [x] This snippet:
  "# Collect all enriched-sweep CalcJobs into a Group. ..."
  is clear to me as an aiida core developer. but, for external people, maybe some type annotations could be useful?
    - added explicit annotations and a comment explaining the `(Group, bool)` return tuple: `sweep_group: orm.Group / created: bool` before the unpack, plus `# get_or_create returns a (Group, bool) tuple: the group itself and a flag indicating whether it was just created (True) or already existed (False).`

- [x] this transition is shitty, QueryBuilder just falls from the sky? "belong to multiple groups. This is what QueryBuilder enables: structured search over the provenance graph. ..."
    - dropped the `---` divider and promoted QueryBuilder into a proper `### Searching with QueryBuilder` subsection with its own motivation lead-in: "Tags and groups are how you *organize* nodes; QueryBuilder is how you *find* them. It is AiiDA's structured-search API over the provenance graph...".

- [x] Maybe introduce this with, something like: "now, after this module, we can see that our profile is filling up fast. to list all the processes we ran so far, let's run":
    - added the lead-in "After all this activity, our profile is filling up. To list every process we have run so far across all modules:" right before the final `%verdi process list -a -p 1` block.

- [x] "We now have a tracked pipeline with structured data, but " -> "We now have a tracked pipeline with structured data, however, "

- [x] the link text is a bit weird here: Auto-serialization of plain Python types in calcfunctions: introduced in v2.1
    - rewrote so the descriptive phrase is the hyperlink, version note in parens: `{ref}`Auto-serialization of plain Python types in calcfunctions <topics:calculations:concepts:calcfunctions:automatic-serialization>` (introduced in v2.1)`.
