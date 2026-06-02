---
orphan: true
---

# Module 7 plan &mdash; Going further

Working title: **Module 7: Going further**.
Original scope was "Error handling" only.
This plan widens it into a survey module &mdash; the reader has built a full provenance-tracked, querying-able, adaptive workflow by the end of M6, and now needs pointers to the broader AiiDA world.
"Going further" framing keeps the door open: errors are one thread; CalcJobs, WorkChains, caching, and the plugin ecosystem are the others.

## What the reader has at the start of M7

- A working tutorial profile (sqlite-dos + zmq broker + daemon).
- The `gsrd` simulator wrapped via `aiida-shell` (M1), enriched with calcfunctions (M2), composed into a WorkGraph pipeline + sweep (M3), demonstrated on a remote cluster (M4), queried via QueryBuilder (M5), and made adaptive with `If`/`While`/dynamic construction (M6).
- An intuition for sockets, the build-vs-run distinction, and `wg.ctx`.
- Familiarity with `verdi process`, `verdi node`, `verdi process dump`, `verdi shell`.

## Goal

Give the reader a map of the rest of the AiiDA world.
Each section here is a short subsection: a paragraph of motivation, a code-or-config snippet (where applicable), and a link to canonical docs.
**No section is meant to be the definitive guide** &mdash; the canonical docs live in `topics/`, `howto/`, and on the plugin homepages.
M7 is the airport, not the destination.

## Proposed structure

### Sec 1: Error handling (~the original M7 scope, scoped down)

**Why first**: errors are the most concrete next step after building a workflow; the reader's intuition for sockets carries directly into "watching a socket for a non-success value".

**Inside**:

- Exit codes: `ShellJob` exposes one as `node.exit_status`; `gsrd` always exits 0 so this is a contrived example, but the *mechanism* is the same as for any CalcJob plugin. Tie to {ref}`topics:processes:concepts:exit_codes` in the core docs.
- WorkGraph error handlers: `ErrorHandlerSpec` from `node_graph.error_handler`. Attach to a task, get called on failure, inspect/modify inputs, optionally `retry`. Tie back to M6's adaptive sweep with one error-handler example.
- A pointer to {ref}`topics:workflows:concepts:errors` for WorkChain-style `@process_handler` (the older but still-supported API).
- "When to use which" tip: handlers for *transient* / *recoverable* failures (resource limits, retryable network blips). Hard programmer errors should fail loudly.

### Sec 2: Beyond aiida-shell &mdash; writing a CalcJob plugin

**Why second**: M1 framed `aiida-shell` as the "easy path"; for production codes the established way is a CalcJob plugin, and the reader deserves to know it exists.

**Inside**:

- Motivation: aiida-shell is great for prototyping but each invocation has to re-discover the command's interface. CalcJob plugins **capture that interface once**, expose typed `spec` inputs, ship a parser, and can be installed by entry point so other people can `pip install` your plugin.
- Shape of a `CalcJob` subclass (very brief): `define()`, `prepare_for_submission()`, parser class with `parse()`. Pointer to {ref}`topics:calculations:usage:calcjobs` and the {ref}`how-to:plugin-codes` guide.
- One short example: pseudocode for a `GsrdCalculation(CalcJob)` that does what we have been doing manually with `aiida-shell`. Side-by-side with the `aiida-shell` invocation to make the win obvious (or the cost).
- Pointer to `aiida-plugin-cutter` / the plugin registry for getting started.

### Sec 3: A note on WorkChain

**Why third**: M3 introduced WorkGraph but the existing ecosystem (aiida-quantumespresso, aiida-cp2k, etc.) is built on WorkChain. The reader will hit WorkChains the first time they look at a real plugin.

**Inside**:

- Two-sentence summary of WorkChain: imperative outline of steps (`outline`), submit-and-wait, context dictionary (`self.ctx`).
- One side-by-side: same trivial workflow in WorkGraph vs WorkChain. The reader should *see* the difference once.
- Decision guide:
  - **WorkGraph**: composing/customising as a user, exploratory work, dynamic graphs.
  - **WorkChain**: distributing a workflow as a plugin, established convention in the QE / CP2K / SIESTA ecosystem.
- Pointer to {ref}`topics:workflows:concepts:workchains`.

### Sec 4: Caching

**Why fourth**: caching is one of AiiDA's most powerful features and goes routinely overlooked. The reader needs to know it exists before they re-run the same expensive calculation by accident.

**Inside**:

- The core idea: AiiDA hashes a CalcJob's inputs (after well-defined normalisation); when you run the same inputs again, AiiDA *reuses the result* instead of re-running.
- Enable globally: `verdi config set caching.default_enabled True`. Inspect: `verdi process show <pk>` shows `Cached from: <pk>`.
> JG: Also `verdi process list` shows what was taken from the cache.
- The pitfalls (briefly): caching depends on the plugin author marking `Data` types as hashable, marking certain inputs as cache-relevant vs not. Pointer to {ref}`topics:provenance:caching`.
- One end-to-end demo: run a small ShellJob twice; second run is cached, returns in milliseconds.

### Sec 5: The plugin ecosystem (just-mention cards)

A 2x4 grid of `grid-item-card` entries, one paragraph + a link button each:

- **aiida-project**: project-scoped AiiDA environments. Lives in `~/.aiida-project/`. Solves the "I have ten ongoing investigations and want them in separate profiles + Python envs" problem. Link: <https://github.com/aiidateam/aiida-project>.
- **aiida-hyperqueue**: HyperQueue metascheduler integration. Run thousands of short jobs inside a single SLURM allocation. Link: <https://aiida-hyperqueue.readthedocs.io>. Cross-reference: {ref}`how-to:tune-performance` in the core docs already mentions this for many-short-calculation workloads.
- **aiida-workgraph**: not new to the reader at this point, but a card explicitly framing it as a separately maintained plugin is useful (manages reader expectations about which features are core vs plugin).
- **aiida-shell**: same &mdash; the reader has been using it since M1; it deserves to be on the plugin map.
- **aiida-submission-controller**: helper classes for managing very large submission queues. Link: <https://github.com/aiidateam/aiida-submission-controller>.
- **aiida-code-registry / aiida-resource-registry**: prebuilt computer & code definitions for common HPC machines. M4 already mentions one of these as a tip; the card consolidates.
- **AiiDAlab**: Jupyter-based front-end on top of AiiDA, used for the Quantum ESPRESSO apps and similar. Link: <https://aiidalab.net>.
- **Domain plugins**: `aiida-quantumespresso`, `aiida-cp2k`, `aiida-siesta`, `aiida-vasp`, `aiida-pseudo` &mdash; one card-of-cards or a one-paragraph paragraph + link to the plugin registry. The point is to show that the tutorial's `gsrd` example is a *miniature* of what the production plugins do.
> JG: Hm, we already have a docs page that shows that. keep this short, link to that. and search the blog post on `non-domain specific plugins to extend aiida functionality` (or so). add the link to the blog post, as well

### Sec 6: Where to go next

Closing pointers:

- The AiiDA Tutorials site (the "AiiDA School" materials): <https://aiida-tutorials.readthedocs.io>.
> JG: Don't link this, we want to archive that, in favor of these tutorial modules we've been working on
- The community: Slack invite link, GitHub Discussions.
> JG: No slack invite for anybody. instead, point to our discourse!
- Contributing: {ref}`internals` and the `CONTRIBUTING.md` workflow.
- A short "what *you* could write next" list: a CalcJob plugin for your favourite tool, a domain WorkChain, a parser for an existing code that does not have one.
> JG: yes, good!

## Tone and format

- Same shape as M1&ndash;M6: each subsection opens with one paragraph of "why", then code/config (if applicable), then a "Further reading" link.
- Plugin cards are display-only &mdash; no executable cells.
- Caching demo is the *only* live cell in M7. Everything else is prose + static code snippets.
> JG: Should it be though? make as much as you can / as is feasible actually executable!
- This is a survey module; do not try to teach `CalcJob` plugins or `WorkChain`s in depth here. The reader is being handed a map, not a textbook.

## Out of scope (explicitly)

- A full CalcJob plugin walkthrough (would double the module length; lives in {ref}`how-to:plugin-codes`).
- A WorkChain walkthrough (lives in {ref}`topics:workflows:concepts:workchains`).
- Anything that requires building a new code on the tutorial profile.
- Anything that requires the SLURM container (M4's territory).

## Open questions for JG

- Is "Going further" the right module title? Alternatives: "Module 7: The wider AiiDA world", "Module 7: Production AiiDA", "Module 7: Where to go next".
> JG: I'd vouch for "Module 7: Where to go next"
- The error-handling section needs a working `gsrd` failure to retry against. Either (a) construct a synthetic failure (e.g., a wrong parameter that triggers `DiffusionError`) and write a one-iteration retry handler, or (b) keep the section purely textual with pseudocode. Lean toward (a) for pedagogical concreteness.
> JG: Yes, (a)
- Caching demo: would it be more useful to demonstrate it on a *single* ShellJob, or to enable it on the M3 sweep and show "the second run of the same sweep is instant"? The sweep version is more dramatic but coupled to M3 state.
> JG: Hm, maybe add both for now. I will then decide later on.
- Should the plugin cards live in M7, or should we promote them to the tutorials landing page (`tutorials/index.md`) as a sidebar? They might earn their keep equally well in either place.
> JG: I'd say module 7 is enough. we also have the general docs page!
