# Full readthrough &mdash; Module 0

- [x] move the 'more about the model' to below the following paragraph, and refer to `gsrd`, not, 'the simulation'
- [x] move this text about the pain points: "The simulation is invoked like a typical scientific code: a single positional argument, no --help to guide you, and whatever real documentation exists buried in a separate manual. It reads an input file and writes its output to the current directory." to the paragraph above that already lists the pain points. The sentence here should say instead that we call it from the command line with the `input.yaml`. Also, make foldable a view with the `input.yaml` contents, with comments for each input param.
- [x] also this: "Expand the output above and you'll see how much there is: a banner, a citation block, per-iteration progress, and a diagnostics box at the end, all interleaved on stdout. This is a deliberately tame example; many production codes produce considerably more." less focus on the pain points. just mention that there is this additional text...
- [x] "headline scalars" this sounds weird. use more normal phrasing. also, explain what these two scalars mean, what they describe. it's not clear from the current text?
    - replaced "headline scalars"/"headline numbers" with "summary diagnostics"/"summary numbers" throughout; added a one-liner explaining variance(V) (pattern contrast across the grid) and mean(V) (average V concentration).
- [x] this "Editing inputs by hand has its own hazard: like many scientific codes, gsrd silently ignores keys it doesn't recognize, so a mistyped parameter name runs cleanly using the default value instead of raising an error." falls a bit from the sky, how should we make the transition better?
    - softened with "The natural thing to do is to open `input.yaml` in a text editor..." and "Editing inputs by hand like this is convenient, but it has its own hazard: ...".
- [x] 'tends to look in' -> 'tends to look like in'
- [x] 'below easy to walk into.' easy to walk into sounds weird, other phrasing!
    - reworded to "which is precisely why the pain points below are so common."
- [x] elided -> hidden; no need to use fancy words...
- [x] 'in a sea of progress output.' "sea" sounds weird. other word?
    - now "easy to miss amongst the rest of the progress output."
- [x] just a thought, if we mention this here: "but for 100 different parameter combinations." we should probably, somewhere, actually run that, and show how easy and seamless it is with aiida, to close the circle, no?

    > CC: This is already covered: M2 does the sweep with an `aiida-shell` `for`-loop and M3 promotes it to `Map`. Want me to add an explicit forward-reference in the M0 "100 parameter combinations" admonition (e.g. "&rarr; we will do exactly this in {ref}`Module 2 <tutorial:module2>`")? Yes/no.
    > jg: no, all good then as it is. just, the sweep we do there is much smaller...

- [x] again, 'and the headline numbers come out of stdout.' 'headline numbers'; also, this is just a quirk we introduced here, not super specific. it's just one (of many) potential quirks. don't phrase it like it's the default mode those codes operate (e.g., vasp gives you a structured xml output file, that makes this whole problem go away)
    - renamed bullet to "Heterogeneous output formats" and reframed: some codes are structured (XML/HDF5), others (`gsrd` included) are not.
- [x] here: 'Post-processing at scale: aggregating a single number from each of hundreds of output files requires custom scripts that might break when the output format changes.', also, what happens when the script gets interrupted, or crashes in the middle? i had this issue in the past, one needs to make it idempotent, skipping all already retrieved values, etc.; no need to add that explicitly, but just a thought
    - per your note, not addressing in M0.
- [x] "How AiiDA solves these problems" in this section, verify that all the failures / pain points introduced above in the module are addressed / referenced.
    - cross-checked. The "unreliable exit codes" pain point (from the Running into errors admonition) wasn't explicitly addressed; added a new "Reliable failure detection" bullet that references the `*** JOB DONE ***` marker pattern we saw earlier. Provenance / overwriting / multi-step / scattered data / handover are all covered by existing bullets.
- [x] 'without ever opening a single file.' -> 'without ever manually opening a single file.'
- [x] maybe some bold highlighting or admonition or so, to make the main points stand out? here: "The promise is not just "more throughput". ..." and re-evaluate in general.
    - wrapped the promise paragraph in `:::{important}` and bolded the key phrases ("scaffolding around your simulations", "stops being your problem"). Strengthened the first AiiDA bullet ("Provenance tracking") with a concrete payoff list ("no overwriting, no orphaned files, no need to keep input YAMLs around by hand").
