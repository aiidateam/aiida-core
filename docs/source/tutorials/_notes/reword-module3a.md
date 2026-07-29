---
orphan: true
---

# Reword pass: `module3a.md`

Wording + code-simplification sweep (X5/X6). Each item quotes the current text,
says why it is flagged, and offers options. Reply in the `> JG:` slot: a letter,
your own rewrite, or "leave". I then apply the picks and build-verify the module.

Tags: `[wording]` = jargon / sentence length. `[code]` = simplify an advanced snippet.

---

## 1. "What you will learn" objective · [wording]

Now:
> Connect tasks by passing one task's output socket as another task's input, so
> the whole pipeline is tracked as a single named process you can query and restart

Why: "output socket" / "input socket" land in the very first bullet the reader
hits, two sections before sockets are introduced.

Options:
(a) Connect your existing calcfunctions and CalcJob into one workflow that AiiDA
    tracks, queries, and can restart as a single unit.
(b) Chain your existing tasks into one reusable workflow, recorded in the
    provenance graph as a single named process.

> JG: just drop "sockets" here
> Connect tasks by passing one task's output as another task's input, so
> the whole pipeline is tracked as a single named process you can query and restart
>
> CC: Applied your wording (dropped "socket").
> JG: and, anything else we should add?
>
> CC: Added a third objective, since the module's back half is all inspection:
> "Inspect the workflow as a single process node and drill into its individual
> child steps". Veto if it's one too many.

> JG: Also, this is just one sentence, "Setup" is not visually distinct: "Setup This module uses AiiDA, aiida-shell, and aiida-workgraph:"
> JG: And, we recommend `uv` throughout, so put the `uv` command
>
> CC: Switched to `uv pip install ...` and split the run-on so the body reads
> "...Install them with:" on its own line, clear of the "Setup" title. If you want
> "Setup" itself more prominent (bigger/bolder than a plain note title) tell me and
> I'll change the admonition. Cross-cutting: `uv` throughout means M0/M1/M2/M4/M7's
> `pip install` notes should switch too; I'll do that in the sweep.

> JG: This should not always be repeated in full
>
> CC: Collapsed to one line pointing at Module 1, dropped the %load_ext/%run
> explanation. This same one-liner should replace the full comment in
> M4/M5/M6a/M6b/M7 (Module 1 keeps the full version); I'll propagate in the sweep.

> # Set up the tutorial's isolated sandbox profile (same as Module 1). <- (see Module 1 for details)
> # `%load_ext aiida` enables the `%verdi` magic; `%run` creates or loads the  <- drop
> # shared `tutorial-<hash>` profile, so data from earlier modules is available. <- drop
> %load_ext aiida
> %run -i include/setup_tutorial.py
---

## 2. "Why workflows?" gap list · [wording]

Now (the four bullets):
> - **No single pipeline object**: the data links between `prepare_input`, the
>   `ShellJob`, and `parse_output` are already in the provenance graph (AiiDA
>   chained them automatically as data flowed through). What is missing is a
>   single *workflow node* that owns the three steps as one unit, that you can
>   query, restart, or hand to a colleague as "the pipeline".
> - **No CALL hierarchy**: the existing links are data links between siblings.
>   There is no orchestrator above them with `CALL_CALC` links pointing down, so
>   listing "everything that belongs to this run of the pipeline" requires
>   reconstructing the chain by hand from the data links.
> - **Sequential by construction**: the Python loop blocks until each iteration
>   finishes, whereas a workflow submitted to the AiiDA daemon can run
>   independent iterations in parallel.
> - **No single entry point**: you can't re-run "the same workflow" with
>   different parameters as one operation.

Why: the densest jargon cluster in the module (CALL_CALC, siblings, orchestrator,
"chained them automatically as data flowed through"), and it lands before the
reader has any workflow vocabulary. The first two bullets say almost the same
thing at different depths.

Options:
(a) Tighten to plain language, drop the internal link-type names:
> - **No single pipeline object**: the individual steps are linked in the
>   provenance graph, but nothing ties them together as "the pipeline", one node
>   you can query, restart, or share.
> - **No overview of a run**: to list everything belonging to one run, you have
>   to walk the links between steps by hand; there is no parent process that owns
>   them.
> - **Sequential only**: the Python loop waits for each iteration to finish; a
>   workflow can run independent iterations in parallel.
> - **No single entry point**: you can't re-run "the same pipeline" with new
>   parameters in one call.

(b) Same as (a) but keep one precise mention of the mechanism in the second
    bullet: "...no parent process holding `CALL` links down to them." (keeps one
    term for readers who will meet it in `verdi process status`).

> JG: (a), but maybe condense to 3 points?
>
> CC: Done, 3 bullets. Merged (a)'s "no single object" + "no overview of a run"
> into one (they're the same gap), kept parallelism and re-run entry point:
> "No single pipeline object", "Sequential only", "No single entry point".
> Also cut the lead-in sentence "the pipeline itself is invisible" (dup of bullet 1)
> and the "walk those links by hand" tail (clear without it).
> JG: bullets 1 and 3 still overlap; fold 3 into 1 ("run with new parameters,
> restart, or query"), then add a fresh third bullet.
>
> CC: Done. Final 3: "No single pipeline object" (now folds in run-with-params),
> "Sequential only", "Tied to your session" (daemon/background survival). Offered
> composability as an alternative third bullet (forward hook to 3b).

---

## 3. WorkChain vs WorkGraph note · [wording] (low priority)

Now:
> **WorkGraph** (declarative, graph-based) was added more recently as a simplified
> API for composing tasks, and is what this tutorial uses; it is more intuitive
> for composing tasks and scales naturally to complex graphs.

Why: "composing tasks" appears twice in one sentence; "scales naturally to
complex graphs" is vague sell.

Options:
(a) **WorkGraph** (declarative, graph-based) is a newer, simpler API for building
    workflows by connecting tasks in a graph, and is what this tutorial uses.
(b) Leave (it is inside a `:::{note}` and reads fine folded into context).

> JG: (via chat) are imperative/declarative correct?
>
> CC: Yes, both accurate and consistent with M7's comparison table (WorkChain =
> imperative; WorkGraph mental model = declarative). Rewrote the note to unpack
> both labels in plain words. Two related additions from chat:
> - Separate-package + "planned for aiida-core 3.0" note added, placed under the
>   `uv pip install` line (your call) rather than in this note.
> - Reframed the concept-mapping dropdown from "AiiDA core ↔ WorkGraph" to
>   "`WorkChain` ↔ `WorkGraph`" and adapted every row to a WorkChain-vs-WorkGraph
>   pairing.

> JG: (a)

---

## mental model
> JG: It's not necessarily a "top-level process node", for nested workgraphs.
> JG: drop "like prepare_input" (no forward-references to something the reader has not seen)
> JG: same for socket bullet, simplify
>
> CC: All applied. WorkGraph bullet: "one process node" (dropped "top-level").
> Task bullet: dropped "(like `prepare_input(...)` below)". Socket bullet: replaced
> the `prepare_input(...).result` example with "A task's arguments are its input
> sockets, and the values it produces are its output sockets."

## 4. "Building vs running" admonition, the comparison example · [wording]

Now:
> That separation is why a comparison like `parsed.variance_V > threshold`
> produces a new socket (a comparison task) rather than a Python `bool`.
> It is also why iterating a socket with a Python `for`, or branching on it with
> a plain `if`, does not work the way you might expect.

Why: forward-references comparison / branching, which only appear in Module 6a.
Vivid, but the reader has not seen `.variance_V` compared to anything yet.

Options:
(a) Re-anchor to this module's own code:
> That separation is why, in the code below, `prepared.result` is a placeholder
> you pass to the next task, not a file you can open yet. Real values appear only
> after `wg.run()`.
(b) Keep as-is (deliberate teaser for the control-flow you'll meet in Module 6).

> JG: (a)
> AiiDA float / dict / singlefiledata -> AiiDA orm nodes
> you are handling sockets (placeholders)
>
> CC: Applied (a) for the comparison/branching sentences. Also in the admonition:
> "AiiDA `Float`/`Dict`/`SinglefileData` *values*" -> "AiiDA ORM nodes", and
> "you are handling *sockets* (placeholders)". Dropped "control flow" from the
> closing sentence since the for/if teaser (M6 forward-ref) is now gone.

---

## 5. "Default-output convention" restatement · [wording]

Now (lines directly after the input/output-socket bullets):
> The default-output convention is the same as for the plain calcfunctions in
> Module 2: when a wrapped function returns a single (unnamed) value, WorkGraph
> exposes it via the `.result` socket on the task handle, mirroring how
> `node.outputs.result` worked there.
> A structured-typed return (TypedDict, dataclass, Pydantic model) creates one
> named socket per field instead.

Why: restates the two bullets immediately above it ("A single annotated return
type produces one output socket named `.result`... a TypedDict... produces one
named socket per field"). Pure repetition.

Options:
(a) Cut both sentences (the bullets already said it).
(b) Replace with one linking sentence: "This is the same `.result` convention you
    saw for the plain calcfunctions in Module 2."

> JG: (a)
>
> CC: You later said "this can be shortened" rather than fully cut, so I kept a
> one-line Module-2 callback ("This is the same `.result` convention you saw for
> the plain calcfunctions in Module 2 (there, `node.outputs.result`)") and cut
> only the redundant structured-return sentence (it just repeats the bullet above).

---

## 6. Graph-introspection cell · [code]

Now:
```python
wg_preview = gray_scott_pipeline.build(
    parameters=orm.Dict(BASE_PARAMS),
    command=gsrd_code,
)

print('Graph inputs (bound from .build()):')
for name in wg_preview.inputs._get_keys():
    if name == 'metadata':
        continue
    bound = getattr(wg_preview.inputs, name).value
    print(f'  - {name:<11} = {bound.__class__.__name__}')

print('\nGraph outputs:')
for name in wg_preview.outputs._get_keys():
    print(f'  - {name}')

print('\nTasks in the graph:')
for t in wg_preview.tasks:
    print(f'  - {t.name:<20} ({t.task_type})')
```

Why: this is the flagged advanced cell. `._get_keys()` is private API, `getattr`
+ `.value.__class__.__name__` + column-aligned f-strings are a lot of Python
noise for "show me what's in the graph". The interactive graph viewer cell right
after shows the same inputs/outputs visually.

Options:
(a) Trim to the task list only (the part that best illustrates "the graph is a
    real object"); let the viewer cell below carry inputs/outputs:
```python
wg_preview = gray_scott_pipeline.build(
    parameters=orm.Dict(BASE_PARAMS),
    command=gsrd_code,
)

print('Tasks in the graph:')
for task in wg_preview.tasks:
    print(f'  - {task.name} ({task.task_type})')
```
(b) Keep inputs/outputs but drop the `getattr` / class-name / alignment noise,
    just list the socket names:
```python
print('Graph inputs: ', [n for n in wg_preview.inputs._get_keys() if n != 'metadata'])
print('Graph outputs:', list(wg_preview.outputs._get_keys()))
print('Tasks:        ', [task.name for task in wg_preview.tasks])
```
(c) Keep as-is.

Note: both (a) and (b) still touch `._get_keys()`. If there's a public accessor
for socket names I'll switch to it before applying (I'll verify against the
installed `aiida-workgraph`).

> JG: (b), and, yes, check if there's public api. you know where to check for the workgraph src?

---

## 7. "Task inputs accept both..." bullet · [wording]

Now:
> Task inputs accept **both plain Python values and sockets**. Above we passed
> `parameters` (a wrapped `Dict`), `command` (a real `InstalledCode` node), and
> `prepared.result` (a socket from the `prepare_input` task, wired through the
> `nodes` dict of the `shelljob` call). For socket arguments WorkGraph creates a
> link from the producing task to this one; for plain values it stores them
> directly as the task's input data. The graph definition does not care which
> kind you pass; only at execution time does the engine resolve sockets to the
> values flowing through them.

Why: one ~90-word bullet, three parentheticals deep. Hard to parse in a single
breath.

Options:
(a) Split into short sentences:
> Task inputs accept **both plain values and sockets**. Above, `parameters` and
> `command` are real AiiDA nodes, while `prepared.result` is a socket from an
> upstream task. For a socket, WorkGraph adds a link from the producing task; for
> a plain value, it stores the value on the task. The definition treats both the
> same; only at run time does the engine resolve sockets to the values flowing
> through them.
(b) Same split, but drop the parenthetical node-type names entirely and let the
    code above speak for itself.

> JG:
>
> CC: Resolved via chat when you caught that `orm.Dict`/`InstalledCode` aren't
> "plain Python values". Reworded to "concrete data and sockets": `command` = node,
> `parameters` = plain dict AiiDA coerces, `prepared.result` = socket.

---

## 8. "Built-ins" bullet · [wording]

Now:
> The task list includes a handful of **built-ins** that WorkGraph adds to every
> graph: `graph_inputs` and `graph_outputs` expose the graph's own I/O as
> pseudo-tasks so that links into and out of the graph look like ordinary
> task-to-task links, and `graph_ctx` is a shared key-value store that tasks can
> read and write, reachable via `wg.ctx.foo`, covered in Module 6.

Why: long, and "expose the graph's own I/O as pseudo-tasks" is jargon-on-jargon.

Options:
(a) Break up and de-jargon:
> The list also shows a few **built-ins** WorkGraph adds to every graph.
> `graph_inputs` and `graph_outputs` stand in for the graph's own inputs and
> outputs, so connections into and out of the graph look like ordinary links
> between tasks. `graph_ctx` is a shared key-value store tasks can read and write
> (via `wg.ctx`), covered in {ref}`Module 6 <tutorial:module6>`.
(b) Leave.

> JG: (a)
>
> CC: Applied (a): de-jargoned, dropped "pseudo-tasks" and "I/O".

---

## 9. Picking the ShellJob child · [code] (low priority)

Now:
```python
shelljob_node = next(c for c in wg.process.called if isinstance(c, orm.CalcJobNode))
```

Why: a `next()` over a generator with `isinstance` is idiomatic but slightly
dense for a tutorial reader; the single-letter `c` doesn't help.

Options:
(a) Spell it out with a readable name and a comment:
```python
# The workflow called three children; grab the one that is the ShellJob.
shelljob_node = next(
    child for child in wg.process.called if isinstance(child, orm.CalcJobNode)
)
```
(b) Leave (it's fine, and the surrounding comment already explains intent).

> JG: (via chat) do it without `next`, list slice `[0]`?
>
> CC: Done: `shelljob_node = [c for c in wg.process.called if isinstance(c, orm.CalcJobNode)][0]`.
