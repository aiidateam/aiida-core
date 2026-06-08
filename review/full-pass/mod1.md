# Full readthrough &mdash; Module 1

- [x] here: "A Computer defines where calculations run, specifying the hostname, transport, and scheduler. When you set up a profile with verdi presto, a localhost Computer is created automatically.

  A Code defines what executable runs on that computer. aiida-shell creates this automatically from the command you pass to launch_shell_job."
  if one has a `Code`, that already points to a `Computer`. in the end, one just has to pass the former... should we rephrase? good to keep as is?
    - kept the Computer/Code distinction (still useful as a mental model) but added a follow-up sentence making the relationship explicit: "In day-to-day use you only ever pass the `Code` to a process; the Computer comes along for the ride because the Code already points at it." Reframed the Code bullet to "wraps an executable bound to a specific Computer".

- [x] here: "In the graph:

  Green ellipses are data nodes (inputs and outputs)

  Rectangles are process nodes (the computation)

  Arrows show the data flow"
  maybe we should also mention the link labels? they are also shown in the plotted graph
    - extended the arrows bullet: "labelled with the **link label** that the input or output is registered under (e.g. `input`, `results_npz`, `stdout`). These are the same labels you use to access the nodes in Python via `node.inputs.<label>` / `node.outputs.<label>`."

- [x] "the process moves through" -> "the process moves through the states: "
- [x] maybe we should introduce PK (and, possibly, UUID), before we use them throughout?
    - added a `:::{note}` admonition right after the first `Process PK:` print, before "What just happened?": PK = profile-local int, UUID = globally unique; `load_node(<PK or UUID>)`.

- [x] "We can also access them programmatically:" -> "We can, of course, also access them programmatically through the Python API:"
- [x] "AiiDA replaces dots with underscores because link labels must be valid Python identifiers." -> "AiiDA replaces dots and other special characters with underscores because the resulting link labels must be valid Python identifiers." (or similar wording, but you get the gist!)
- [x] This is not shown how to retrieve via the Python API? falls a bit from the sky here? "retrieved: a FolderData containing everything AiiDA fetched back from the working directory.
  remote_folder: a RemoteData pointing to the working directory on the Computer where the job ran (typically a remote HPC):
  " so maybe we show how they can be obtained from the node in the python snippet above, so it maps one-to-one?
    - merged the two access patterns into one code cell: `for label, ... in results.items()` then `node.outputs.remote_folder.get_remote_path()` in the same block, with a lead-in explaining they expose the same set of outputs. Dropped the standalone `remote_folder` cell below.

- [x] ah, i see `remote folder` is shown below. your call, make things consistent and the flow good!
    - covered by the merge above; the bullet for `remote_folder` now says "the path we just printed above".

- [x] "the binary file is a SinglefileData node, and stdout is a captured-text node we can open just like any other." actually, aiida-shell also creates a SinglefileData from stdout, so tehy way these are captured is actually the same
    - verified against `aiida_shell.parsers.shell.ShellParser.parse` (stdout is wrapped as `SinglefileData(handle, filename=filename_stdout)`); rewrote to "Both are now tracked by AiiDA as `SinglefileData` nodes (`aiida-shell` captures stdout as a file just like any other output), so we can open either of them the same way."

- [x] drop em-dash: "For reference, this is what gsrd actually printed — the banner, the parsed parameters, the periodic progress lines, and the diagnostics block at the end:"
    - reframed the whole lead-in (no em-dash) as part of the next item.

- [x] maybe we introduce that and say that the raw stdout output is still retrievable via this: "print(node.outputs.stdout.get_content())", to pass the message, but then, the actual output is folded by default, because it's already shown in full once in module 0, and is quite the wall of text?
    - applied `:tags: ["hide-output"]` to the `print(node.outputs.stdout.get_content())` cell; new lead-in: "The full raw stdout text we already saw printed inline in Module 0 is still retrievable via `node.outputs.stdout.get_content()`. We collapse the cell output here, since it is the same wall of text as before."

- [x] "In later modules we extract just the diagnostics block from this text, so the banner and progress lines are elided from the displayed output. They are always present in the captured stdout node, just collapsed for readability." -> replaced "elided"
    - "elided" &rarr; "hidden".

- [x] should we made this block auto-folded, and just introduce with "how we extract the actual values"?
  """# Pull the final V field out of the .npz, and grep the scalars out of stdout. ..."""
    - applied `:tags: ["hide-input"]` to the extraction block; added lead-in "Here is how we extract the actual values:" before it.

- [x] "That regex is the price of admission for a code that prints its headline scalars only to stdout. We did exactly the same thing manually in Module 0; the difference now is that the stdout text, the regex result" -> "The regex above"; and, how is the regex result part of the provenance graph? it is not, only if we'd have been using an actual parser, no? can you rephrase / make more precise?
    - "That regex" &rarr; "The regex above"; rewrote the provenance claim: stdout text and input file are tracked nodes, but the two floats we computed are *not* in the graph &mdash; they are transient Python locals; capturing them properly requires a parser (which is what M2 introduces).

- [x] node.outputs.stdout.get_content() # follow output links -> Comment is not right, no?
    - changed to `# read the content of an output node`.

- [x] shorten the list: "The shell pulls in load_node, load_code, load_computer, Dict, Int, QueryBuilder, User, etc., so you do not need from aiida import ... boilerplate. It is the same Python environment as %load_ext aiida gives you inside Jupyter; pick whichever feels right"
    - "Common helpers like `load_node`, `Dict`, `QueryBuilder`, etc. are pre-imported, so you do not need `from aiida import ...` boilerplate."

- [x] "In Module 2, the regex we just wrote by hand turns into a tracked parsing step" -> "In Module 2, we will turn the regex we just wrote by hand into a tracked parsing step", and combine better with the following sentence, don't use ":"
    - merged the two sentences: "In Module 2, we will turn the regex we just wrote by hand into a tracked parsing step, so the scalar results from each simulation become individual database entries searchable across runs without opening any output file, and the Python that prepares inputs and parses outputs gets tracked as part of the same provenance."
