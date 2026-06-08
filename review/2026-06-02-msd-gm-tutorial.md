# MSD GM Tutorial Meeting — 2026-06-02

## Content & structure

- Module 0 might be too long.
- Module 3 is very long — split into two?
- What is module "include"? Do we need it?
- Split long modules into sub-modules (e.g. Module X A, B, C).
- Rename "introduction" to "about".
- EB: introduce the leading example already in the index page, not just in Module 0. Move the description there.
- Add links for further reading at the end of every module. Consider footnotes, pop-ups, or fold-outs (with a way to jump back).
- Fewer modules visible on the home page.

### Quickstart & basic tutorial

- Drop the basic tutorial? Or rework it into an advanced module on provenance, or a subsection bundled under querying.
- Have a separate quickstart (~20 cells to go through), in addition to the full tutorial.
- We probably need two "demo" versions: one basic (quick start), one for QE users.
- What to do with `aiida-qe-demo`?

## Language & wording

Tune down technical wording, both AiiDA-specific and Python-specific. Simplify sentences: shorter, less technical lingo. Examples of overly technical phrasing:

- "they declare typed, validated input ports in their process spec"
- "that is where gsrd prints the headline scalars our parser regexes out."
- "the WorkGraph analogue of the WorkChain ctx" — we may never have discussed WorkChain by this point. Be careful not to reference unknown concepts in a tutorial.
- "So, gray_scott_pipeline is now a factory: call .build(...) to get a standalone WorkGraph you can run() or submit() directly, or call it inside a parent graph to embed it as a sub-task" — split into shorter sentences.
- "is then byte-for-byte identical" — do we need "byte-for-byte"? Not even fully true in a sense.

Whenever AiiDA-specific lingo is used (e.g. QueryBuilder), introduce it properly first.

## Code & notebook UX

- Keep Python code as simple as possible. Avoid advanced syntax (e.g. advanced string formatting). Better to have more lines than very long ones. Assign to variables before using them.
  - Example: `input_path = Path('include/input.yaml').resolve()` — should we just put an actual string there instead?
- Add more comments in the Python code explaining what each section does.
- `!` vs `%` — clarify and be consistent about usage.
- Missing `tree` command.
- Instead of `mkdtemp`, consider just using `!mkdir tmp`. If used multiple times, add a comment explaining what is happening for non-Python experts. Same for `Path(...).resolve()`, etc.
- People will copy-paste each cell, not download the Jupyter notebook. Don't make cells fully hidden, but folded.
- Is there always a copy button on RTD?
- Module 0: `pip install` the `gsrd` repository.
- Open issues for possible code simplifications (GP).

## API ergonomics

- `first_calc_node.base.extras.all.items()` is long. Make a list of API simplification suggestions for AiiDA 3 (OK to keep as-is for the current tutorial).
- Module 5: is the new filter syntax (instead of `filters={'attributes.value': {'>': 0.01}}`) available? Do we want to use it as the default?
- Joining: add a graphical visualization, but make it visually distinct from the provenance graph so people don't get confused.

## Installation & packaging

- Install everything in Module 7 with `pip install aiida`? If we're not sure, OK to just install `aiida-core` for now, but make sure it's part of the release process so we don't accidentally install version 1.0.1.
- Add a note on "installation" in the individual modules.

## Focus for reviewing modules

- Quickly read through the structure of the whole tutorial before working on a specific module (definitely the preceding ones, and skim through the following ones).
- Check and streamline text.
- Take notes on code that could be simplified (either now or for AiiDA 3.0).
