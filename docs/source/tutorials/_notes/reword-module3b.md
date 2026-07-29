---
orphan: true
---

# Reword pass: `module3b.md`

Same workflow as `reword-module3a.md`. Each item quotes the current text, says why
it is flagged, and offers options. Reply in the `> JG:` slot: a letter, your own
rewrite, or "leave". I then apply the picks and build-verify the module.

Tags: `[wording]` = jargon / sentence length / repetition. `[code]` = simplify an
advanced snippet. `[voice]` = tone / stylistic call.

First-pass read: 3b is already in good shape (no "handle" wording, `._value` reads
carry their explanatory comments, blueprint framing is clean). The main issue is
**repetition**: one idea ("the graph is parameter-agnostic, only the input dict
changes") is stated four times, and the two `:::{important}` boxes about `Map`
overlap heavily. That's most of what's below.

### New standing conventions that emerged this round (apply module-wide)

- **Drop titled `Setup` admonitions.** `:::{note} Setup` renders the title without
  the note styling, so use a plain `:::{note}` ("Note" header). Already propagated
  across M0-M7.
- **No "sweep" in structural elements** (titles, headings, admonition titles,
  objective / summary lists). Fine in flowing prose and in code identifiers
  (`gray_scott_sweep`, `param_sweep`). Open follow-up: the M6b heading
  `## Putting it together: an adaptive sweep` is coupled to the `adaptive_sweep`
  function name; decide (rename both, or accept the code-derived term) during the
  6a/6b pass.

---

## 1. Two overlapping `:::{important}` boxes on `Map` mechanics · [wording] (the big one)

The module has two `:::{important}` boxes about how `Map` works, one before the
code (L95-101) and one after (L169-175). They restate each other.

Box 1 (before, L95-101):
> Conceptually, a `Map` zone does three things:
> 1. It takes a **source collection** of the form `{key: value}` and runs the tasks inside the zone once per entry.
> 2. Inside the zone, it exposes the current key/value via `map_zone.item.key` and `map_zone.item.value`. These are sockets, so you can wire them into tasks just like any other output.
> 3. At the end of the zone, `map_zone.gather({...})` declares which per-iteration outputs to collect. The gathered outputs become accessible on `map_zone.outputs.<name>` as a namespace keyed by the original source keys.

Box 2 (after, L169-175):
> A few things to keep in mind about `Map`:
> - The source must be a mapping (a `dict` or a socket of a dynamic namespace). Iterating over a plain list is not supported directly. Wrap it into a dict first, using meaningful keys like `F_0_040` rather than integer indices, because those keys will show up in the provenance graph and as the names of the gathered outputs. **Avoid dots in keys**: WorkGraph treats dots as namespace separators, which will silently collapse your entries.
> - `map_zone.item.value` is the value for the current iteration, `map_zone.item.key` is its key. Both are sockets, so you can pass them as task inputs, but you cannot use them as ordinary Python values inside the graph function (no `if` on them, no string concatenation).
> - After the `with` block, `map_zone.outputs.<name>` gives you a namespace that behaves like a dict of AiiDA nodes, keyed by the original source keys.

Overlap: source-is-a-mapping (box1.1 / box2.1), item.key/value-are-sockets
(box1.2 / box2.2), outputs-namespace-keyed-by-source (box1.3 / box2.3). Box 2 adds
two genuinely *new* things the reader needs: the dots-in-keys gotcha, and "you
can't branch/string-format on the item sockets".

Options:
(a) **Keep box 1 as the conceptual intro; slim box 2 to pure gotchas** (drop the
    parts box 1 already covered):
> Two things to watch with `Map`:
> - The keys of your source dict become labels in the provenance graph and the names of the gathered outputs, so use meaningful, identifier-safe keys (`F_0_040`, not an integer index). **Avoid dots**: WorkGraph treats them as namespace separators and will silently collapse entries.
> - `map_zone.item.key` and `map_zone.item.value` are sockets, not Python values. You can pass them to tasks, but you cannot branch on them or build strings from them inside the graph function.

(b) Same as (a), and also **demote box 1 to plain prose** (drop the `:::{important}`
    wrapper): in 3a we made the important boxes headline-only, so two full
    multi-bullet important boxes here is a style mismatch. Box 1 becomes a short
    lead-in paragraph, box 2 (slimmed) stays the one `:::{important}`.

(c) Leave both.

> JG: (b)
>
> CC: Applied. Box 1 (L95-101) demoted to plain lead-in prose ("A `Map` zone works
> in three parts. ..."), no more `:::{important}` wrapper. Box 2 slimmed to the one
> `:::{important}` with just the two new gotchas (identifier-safe keys / avoid dots;
> item sockets aren't Python values).

---

## 2. "Parameter-agnostic" stated four times · [wording]

The idea "the graph doesn't hard-code what it sweeps; change only `param_sweep`"
appears four times:

- L38 (objective): "Reuse the same workflow for a 2D scan by changing only its input"
- L126 (tip): "The blueprint is parameter-agnostic: change the contents of `param_sweep` and you can scan a different parameter (or several at once) without touching the workflow."
- L299: "The point of wrapping the sweep as a `@task.graph()` was that it is parameter-agnostic; we can scan a 2D grid by changing nothing but the contents of `param_sweep`."
- L322: "The same `gray_scott_sweep` graph drives both the 1D and 2D scans; only the input dict changes."

Also "parameter-agnostic" is itself a slightly jargon-y coinage.

The objective (L38) and the 2D-scan lead-in (L299/L322) are the two places it
*earns* a mention (once to promise it, once to cash it in). The tip at L126 is the
redundant one: it makes the point before the reader has even seen the 1D sweep run.

Options:
(a) **Cut the tip (L124-127) entirely.** The `@task.graph()` signature and the
    L299 payoff carry the point; the tip pre-empts it.
(b) **Keep the tip but drop the word "parameter-agnostic"** everywhere, say it
    plainly ("nothing in the graph hard-codes *which* parameter varies"), and trim
    L299 so it doesn't re-explain, just: "As promised, we scan a 2D grid by changing
    only `param_sweep`."
(c) Leave.

> JG: (via chat) apply (a).
>
> CC: Cut the redundant `:::{tip}` entirely; the `@task.graph()` signature and the
> L299 payoff carry the point.

---

## 3. "What you will learn", first bullet · [wording]

Now:
> - Run a workflow over many input sets at once with WorkGraph's `Map`, replacing a plain Python `for`-loop with tracked, parallel, fan-out execution

Why: "tracked, parallel, fan-out execution" stacks three modifiers at the end of an
already-long bullet, and "fan-out" is jargon here (it's explained later via the
fork-out/join imagery, but lands cold in the first bullet).

Options:
(a) Split the promise from the payoff:
> - Replace a plain Python `for`-loop over parameters with WorkGraph's `Map`, so the sweep runs as one tracked workflow instead of a series of disconnected calls.
(b) Trim the tail only:
> - Run a workflow over many input sets at once with WorkGraph's `Map`, turning a plain Python `for`-loop into a single tracked, parallel workflow.
(c) Leave.

> JG: (via chat) don't like "fan-out".
>
> CC: Dropped the fan-out/fork-out/join imagery everywhere: L36 now "into a single
> tracked, parallel workflow", L115 "`Map` produces one variance per parameter set,
> and the plotting task combines them into a single figure", L250 "branches into one
> sub-workflow per `F` value and recombines through `make_transition_plot`". The
> remaining triple-modifier concern in this item is thus resolved too.

---

## 4. "Trivial steady state / order of magnitude" stated twice · [wording]

Nearly verbatim repeat:
- L302: "near the edge it drops by an order of magnitude as the V field starts decaying toward a trivial steady state."
- L363: "toward the upper-right corner, `variance(V)` drops by an order of magnitude as the V field begins decaying toward a trivial steady state."

L302 is in the setup prose *before* the 2D run; L363 is the payoff *after* the
heatmap. The physics explanation only needs to appear once.

Options:
(a) Keep it at L302 (where the grid choice is being motivated), and trim L363 to
    just read the picture: "High-variance cells (bright) form the spots, stripes,
    and labyrinths; the low-variance corner is where the pattern dies out.
    Twenty-five simulations, one workflow node, full provenance attached."
(b) Reverse: cut the physics from L302 (keep only "the grid straddles the boundary
    of the pattern-forming region"), let L363 carry the full explanation next to
    the heatmap that shows it.
(c) Leave.

> JG: (via chat) apply (a).
>
> CC: Kept the physics at L302; trimmed the post-heatmap line to "the low-variance
> corner is where the pattern dies out."

---

## 5. `dynamic()` / `namespace()` helper explanation · [wording] (low priority)

Now (L129-132):
> The signature of `gray_scott_sweep` uses two helpers from the WorkGraph type system (both already imported at the top of this module):
> - `dynamic(dict)` on the input tells WorkGraph that `param_sweep` is a dict whose keys are not known until runtime. Each value is itself a dict (the parameter set for one iteration).
> - `namespace(...)` on the return type declares multiple named outputs. Some are fixed (`transition_plot`), others are `dynamic(float)`, meaning the engine will create one output per Map iteration under that name.

Note: in 3a you had me *drop* a mention of these helpers because they weren't used
there. Here they genuinely appear in the signature (L143-148), so an explanation is
warranted, this is just about tightening it. It reads fine; flagging only because
"the WorkGraph type system" is a heavy label for two annotations.

Options:
(a) Tighten the lead-in and the second bullet:
> The signature of `gray_scott_sweep` uses two annotations you have not seen yet:
> - `dynamic(dict)` marks `param_sweep` as a dict whose keys are only known at runtime, one entry (itself a parameter dict) per iteration.
> - `namespace(...)` declares several named outputs at once: a fixed `transition_plot`, plus `dynamic(float)` outputs that the engine fills in with one value per iteration.
(b) Leave.

> JG: (via chat) apply (a).
>
> CC: Tightened the lead-in ("two annotations you have not seen yet") and both
> bullets; dropped "the WorkGraph type system" label.

---

## 6. Run/submit note partly re-explains 3a · [wording] (low priority)

Now (L230-235):
> We called `.run()`, which blocks your Python session until the whole graph has finished.
> The alternative, `.submit()`, hands the workflow to the AiiDA daemon and returns immediately, freeing your session while the daemon drives execution in the background.
> In both cases the sub-workflows inside the `Map` zone run concurrently (the engine schedules them as independent processes); the only difference is whether *your session* waits for the result or not.
> For a tutorial `.run()` is convenient because the outputs are available right away.

Why: 3a already introduced run-vs-submit. The genuinely new point here is the third
sentence (sub-workflows inside a `Map` run concurrently regardless). The first two
sentences repeat 3a.

Options:
(a) Compress to a callback + the new bit:
> As in Module 3a we used `.run()` (blocking) rather than `.submit()` (hand off to the daemon). Either way, the sub-workflows inside the `Map` zone run concurrently, as independent processes; the only difference is whether *your* session waits for them.
(b) Leave (a self-contained refresher is arguably worth the repetition).

> JG: (via chat) apply (a).
>
> CC: Compressed to a Module 3a callback plus the new "concurrent inside a `Map`"
> point; dropped the two sentences that repeated 3a.
>
> CC (follow-up, via chat): made the parallelism payoff explicit ("Unlike Module 2's
> loop, which ran one `F` at a time, the eight iterations ... run concurrently").
> Confirmed the framing is sound (M2 used blocking `launch_shell_job`, so it really
> was one-at-a-time). TODO at build-verify: check the eight iterations actually
> overlap under `.run()` in the sandbox profile; if they serialize, tie the
> "concurrently" claim to `.submit()` only.
>
> CC (final, via chat): **dropped the whole note.** JG: it doesn't directly relate to
> `Map`, and run-vs-submit is already covered in 3a. This retires the concurrency
> TODO above (no `.run()`-concurrency claim remains anywhere to verify).

---

## 7. "Time to bring out the binoculars" · [voice] (low priority)

L257:
> 🔭 Time to bring out the binoculars.

A playful aside before the provenance-graph render. Fits a friendly tutorial voice,
but it's the only emoji-led whimsy in the module, so it stands out. Purely your
call.

Options: (a) keep, (b) drop the line, (c) keep the sentiment, lose the emoji.

> JG: (via chat) keep the emoji, but move it to the end of the sentence; and 🔭 is a
> telescope, not binoculars.
>
> CC: Final: "Time to bring out the magnifying glass. 🔍" (JG: pick a word whose
> emoji actually exists; no binoculars emoji, and telescope reads as "far away".
> Magnifying glass fits examining the provenance up close; emoji at the sentence end).
