# Draft issue for `aiidateam/aiida-workgraph`

Target repo: [aiidateam/aiida-workgraph](https://github.com/aiidateam/aiida-workgraph/issues)

**Title:** Fold `shelljob()` into `task()` (dispatch on `ShellJob`)?

---

Right now there are two entry points for putting an AiiDA process into a graph: `task(...)` for calcfunctions, CalcJobs, and nested WorkGraphs, and a separate `shelljob(...)` for `ShellJob`. I went looking for why `ShellJob` needs its own function and I think it mostly doesn't.

For a normal CalcJob, `task(SomeCalcJob)` already auto-discovers inputs and outputs from the process spec (`from_aiida_process`), no annotation needed. `ShellJob` is special only in two small ways:

- its output namespace is dynamic (`spec.outputs.dynamic = True` in `aiida_shell/calculations/shell.py`), so the concrete output sockets can't be discovered statically, you have to name the files you want with `outputs=['results.npz']`; and
- `shelljob(command='gsrd')` resolves a command *string* into an `InstalledCode`, whereas `ShellJob`'s real input is a required `code`.

So the only thing that genuinely can't be auto-discovered is the dynamic-output selection. Everything else `shelljob()` does is `from_aiida_process(ShellJob)` plus the input translation via the shared `prepare_shell_job_inputs` helper. That makes me think it could fold into `task()`:

```python
# today
simulation = shelljob(command=code, arguments=['{input}'], nodes={'input': prepared.result}, outputs=['results.npz'])

# proposed
simulation = task(ShellJob, outputs=['results.npz'])(command=code, arguments=['{input}'], nodes={'input': prepared.result})
```

Exact spelling is up for debate (`task(ShellJob).with_outputs([...])`, or call-time dispatch inside `task`). The point is: only `outputs` needs supplying by hand; `command` could stay a normal input with optional string coercion.

Two smaller motivations:

- The names `shelljob` and `ShellJob` differ only by capitalization, which is easy to misread in code and in review. Folding into `task(ShellJob, ...)` removes the lowercase twin entirely. If a standalone function stays, something like `add_shelljob_task` / `make_shelljob` would at least disambiguate.
- One entry point is easier to teach and document: "wrap any process with `task()`", no special case.

Not urgent, mostly an API-consistency question, but I hit it while writing tutorial material and it stuck out.
