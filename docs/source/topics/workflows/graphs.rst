.. _topics:workflows:graphs:

Graphs
======

.. versionadded:: 3.0

A graph is a workflow written as a plain Python function that connects individual steps, called tasks.
Two decorators define them:

* ``@task`` marks a step, a function whose body is ordinary Python.
* ``@graph`` marks a workflow that connects tasks, written in a small subset of Python.

For example, to construct our favorite multiply-add workflow:

.. code:: python

    from aiida.engine import graph, task

    @task
    def multiply(x: int, y: int) -> int:
        return x * y

    @task
    def add(x: int, y: int) -> int:
        return x + y

    @graph
    def multiply_add(x: int, y: int, z: int) -> int:
        product = multiply(x=x, y=y)
        return add(x=product, y=z)

Various other examples live in the :ref:`topics:workflows:graphs:gallery` at the end of this page.

.. _topics:workflows:graphs:contract:

The contract
------------

A ``@graph`` body is never executed as Python.
It declares orchestration in a small subset of Python; every name resolves to a task, a graph input, or an inline value, and anything else fails when the graph is validated with ``build()``.
Tasks are the only place that runs Python, creates data, and records provenance.
The full rule list lives under :ref:`topics:workflows:graphs:language`.

Each call to a task or graph in a body is a placement.
Calling the same task twice creates two placements, each running as its own child process with its own inputs, outputs, and provenance links; name repeated placements with distinct ``.alias('name')`` calls, as a bare second call fails when the graph is built.
A named value passed between placements is a wire.
Nested graphs, branch arms, loop iterations, and map items run as scopes of the same graph process: no intermediate process nodes, with hierarchical call labels preserving the scope identity.

.. _topics:workflows:graphs:recipe:

Authoring recipe
----------------

The following workflow example moves a value toward a target, stopping when it reaches the target or uses its step budget. Later sections refer back to it:

.. code:: python

    from aiida.engine import graph, run_get_node, task


    @task
    def step_toward(value: int, target: int) -> int:
        """Move one unit toward the target; staying put at the target avoids overshoot."""
        if value < target:
            return value + 1
        if value > target:
            return value - 1
        return value


    @task
    def summarize(value: int, target: int, attempts: int, status: str) -> dict[str, int | str]:
        """Record the final value, target, attempts, and status as one report."""
        return {'value': value, 'target': target, 'attempts': attempts, 'status': status}


    @graph
    def converge(initial: int, target: int, max_steps: int) -> dict[str, int | str]:
        """Step ``initial`` toward ``target`` at most ``max_steps`` times, then report."""
        value = initial
        attempts = 0
        while value != target and attempts < max_steps:
            step = step_toward(value=value, target=target)
            value = step
            attempts = attempts + 1
        if value == target:
            status = 'converged'
        else:
            status = 'exhausted'
        report = summarize(value=value, target=target, attempts=attempts, status=status)
        return report

The task bodies compute the next value and the final report.
The graph only connects them: its counter and condition are inline orchestration state, while each call to ``step_toward`` runs a calculation and records its result.
When the loop ends, ``summarize`` creates the report node that the graph returns.

Validate the graph before launching it:

.. code:: python

    converge.build()  # silent on success; raises GraphLanguageError naming the offending source line on failure

This checks supported syntax, wiring, and static contracts without running tasks.
It does not execute the task bodies or guarantee that a run will succeed.
With an AiiDA profile loaded, run a representative case and inspect the result:

.. code:: python

    outputs, root = run_get_node(converge, initial=0, target=3, max_steps=10)
    assert root.is_finished_ok
    assert outputs['result'].get_dict() == {
        'value': 3, 'target': 3, 'attempts': 3, 'status': 'converged'
    }
    assert root.inputs.initial.value == 0


.. _topics:workflows:graphs:why:

Why graphs
----------

A ``WorkChain`` spells orchestration as outline steps with explicit ``submit`` and ``to_context``, keeping resume state in ``self.ctx``.
The sketch below builds an equivalent workflow to the ``converge`` recipe above, step for step:

.. code:: python

    from aiida.engine import WorkChain, calcfunction, while_
    from aiida.orm import Dict, Int

    @calcfunction
    def make_report(value: Int, attempts: Int) -> Dict:
        return Dict({'value': value.value, 'attempts': attempts.value})

    class Converge(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input('initial', valid_type=Int)
            spec.input('target', valid_type=Int)
            spec.input('max_steps', valid_type=Int)
            spec.output('report', valid_type=Dict)
            spec.outline(cls.init, while_(cls.has_steps_left)(cls.step, cls.update), cls.report)

        def init(self):
            self.ctx.value = self.inputs.initial
            self.ctx.attempts = 0

        def has_steps_left(self):
            return self.ctx.value.value != self.inputs.target.value and self.ctx.attempts < self.inputs.max_steps.value

        def step(self):
            self.to_context(stepped=self.submit(StepToward, value=self.ctx.value, target=self.inputs.target))

        def update(self):
            self.ctx.value = self.ctx.stepped.outputs.result
            self.ctx.attempts += 1

        def report(self):
            self.out('report', make_report(self.ctx.value, Int(self.ctx.attempts)))

The same workflow as a graph (see :ref:`topics:workflows:graphs:recipe`) reduces the boilerplate.

Each ``WorkChain`` concept has a counterpart in a graph:

* ``spec.input``/``spec.output`` become function parameters and the return annotation: ports are plain annotations, checked at ``build()`` instead of at first launch (see :ref:`topics:workflows:graphs:validation`);
* ``spec.outline`` steps become straight-line code: ``if_`` becomes ``if``, ``while_`` becomes ``while``, with no step functions to name and order (see :ref:`topics:workflows:graphs:control_flow`);
* ``self.submit(...)`` plus ``to_context`` becomes a direct call: outputs arrive as named values, so downstream wiring is type-checked instead of looked up in ``self.ctx`` at run time (see :ref:`topics:workflows:graphs:task_kinds`);
* ``self.ctx`` resume state becomes carried loop state and inline values: counters and flags checkpoint without stored nodes (see :ref:`topics:workflows:graphs:inline`);
* ``self.out(...)`` becomes ``return``: the graph returns existing nodes instead of attaching outputs by hand (see :ref:`topics:workflows:graphs:outputs`);
* ``spec.exit_code`` for expected failures becomes ``Result[..., Errors]`` with ``Err`` returns, or ``errors=`` on a task wrapping a process class: declared outcomes branch and retry in the graph instead of needing a restart work chain (see :ref:`topics:workflows:graphs:declared_failures` and :ref:`topics:workflows:graphs:retries`).

As compared to work chains, graphs provide: less code to write, static pre-runtime validation with actionable error messages, and on-the-fly construction without the need for entry point registration. Tasks stay processes with full provenance, executed by daemon workers.

Graphs do not do:

* arbitrary Python (method calls and imports belong in tasks; list and dict comprehensions are inline, see :ref:`topics:workflows:graphs:inline_collections`);
* dynamic submission (the placements are fixed when the graph is built -- a ``WorkChain`` can instead submit a number of processes computed at run time, or pick the process class from an intermediate result);
* unstored runs (see :ref:`topics:workflows:graphs:limitations`).

.. _topics:workflows:graphs:validation:

Validation
----------

Validation happens at three points as a graph moves from template to run: placements and wiring are fully known at ``build()`` time.
``build()`` checks syntax, wiring, and static contracts without running anything or creating nodes.
A passing ``build()`` means the graph is well-formed, not that it will succeed.
Launch fills inputs and defaults, binds ``runtime_config`` per placement, and rejects unknown placements or missing execution inputs.
Absent graph inputs are reported together at launch, and a task whose wired inputs leave a required port empty never dispatches.
At runtime the engine re-checks branch condition types, fails tasks with missing outputs, and maps declared failures to error arms; only values, such as how many iterations a loop takes, materialize at run time.
The checkpoint keeps finished task nodes, scope progress, and inline values, so a restarted graph reuses work instead of resubmitting it.

For example, returning a name bound in only one arm fails at ``build()``, before anything runs:

.. code:: python

    from aiida.engine import graph, task

    @task
    def add(x: int, y: int) -> int:
        return x + y

    @graph
    def bad(x: int, flag: bool) -> int:
        if flag:
            chosen = add(x=x, y=1)
        return chosen

Building it reports the exact validation error, with the offending source line and a caret:

.. code:: text

    aiida.common.exceptions.GraphLanguageError: /path/to/file.py:9:5: __main__:bad: without an `else`
    arm the branch keeps the prior binding, so `chosen` must be assigned
    before the `if`; assign it first or add an `else` arm instead
        if flag:
        ^

Both fixes from the message build.
Binding the name first keeps the incoming value when the branch is skipped:

.. code:: python

    @graph
    def good(x: int, flag: bool) -> int:
        chosen = x
        if flag:
            chosen = add(x=x, y=1)
        return chosen

Adding an ``else`` arm binds it on that path instead:

.. code:: python

    @graph
    def good_else(x: int, flag: bool) -> int:
        if flag:
            chosen = add(x=x, y=1)
        else:
            chosen = x
        return chosen

.. _topics:workflows:graphs:language:

Graph language
--------------

AiiDA compiles the ``@graph`` source for the engine; the compiled representation stays an implementation detail.

The graph body supports:

* calls, ``name = task(...)`` with keyword or positional arguments; calling another graph works the same way and places it as a subgraph (:ref:`topics:workflows:graphs:control_flow`);
* graph inputs and earlier-bound names as arguments, plus literals (``1``, ``'done'``, ``True``, ``None``) and scalar bindings (``attempts = 0``);
* ``if``/``elif``/``else``, ``while``, and ``x if condition else y``, with inline expressions and task calls directly in the tests (:ref:`topics:workflows:graphs:control_flow`);
* inline arithmetic, comparisons, and unary operators (:ref:`topics:workflows:graphs:inline`);
* collection expressions over typed lists and mappings: integer indexing with negatives, string-key lookup with runtime keys, public annotated item reads such as ``item.value``, and filtered, nested list and dict comprehensions with ``mapping.items()`` pair iteration (:ref:`topics:workflows:graphs:inline_collections`);
* an explicit ``return`` on every path, either at the end or from inside an ``if``, ``elif``, ``else``, or ``while`` region; return a name, a field, a call, or a ``dict`` of those with literal string keys (``return {}`` for no outputs);
* field and namespace selection (``.key``, ``['key']``, ``.result``; ``.result`` on a single-output call is optional) and multi-output unpacking (``first, second = step(...)``);
* module-qualified calls (``my_module.add(...)``) and explicitly aliased placements (``decl.alias('name')(...)``), required whenever one task or graph is placed twice in the same body;
* namespace ``dict`` literals (``nodes={'text': text}``) and ``**bundle`` spreading (:ref:`topics:workflows:graphs:spreading`);
* ``after=`` ordering: ``add(x=x, y=1, after=prepared)`` waits for the ``prepared`` placement without using its outputs; ``after=(first, second)`` waits for both; ``after`` is reserved and cannot be a task parameter;
* ``partial`` bindings: ``configured = partial(add, y=y)`` fixes some inputs of a task or graph once and reuses the binding for ordinary calls and maps (:ref:`topics:workflows:graphs:partial`); ``partial`` needs no import and cannot name an input, wire, or binding;

Each call is assigned to a name, including calls to tasks without outputs; ``return`` and the tests of ``if`` and ``while`` also take inline expressions and calls directly.
Each name is bound once; only ``if`` arms and ``while`` bodies rebind names bound before them.
Anything else fails when the graph is validated with ``build()``, naming its source line.

.. _topics:workflows:graphs:inline:

Inline operations
^^^^^^^^^^^^^^^^^^

Arithmetic, comparisons, and unary operators compute orchestration state inline, without a task: ``+ - * // %``, ``< <= > >= == !=``, and unary ``+ - not``.
Operands are graph inputs, names bound on an earlier line, or literals.
A ``while`` tests an inline comparison directly and steps its counter with inline arithmetic:

.. code:: python

    @graph
    def count_down(n: int) -> None:
        while n > 0:
            n = n - 1
        return {}

Scalar literals bind the same way, without a task, such as ``attempts = 0``, ``running = False``, or ``mode = 'square'``.
A bound name wires its value into task arguments, branch arms, and loop state exactly like a computed inline result.
Only finite numbers, strings, booleans, and ``None`` bind; anything else (formatting, method calls, nested task calls) still belongs in a task, while collections use the inline forms below.

Inline results are ephemeral orchestration state, not scientific data:

* **No provenance:** inline values never become data nodes and never carry links. Only task outputs are stored.
* **Checkpointed, not stored:** the scheduler keeps inline values in its scope state, so restarts resume counters and conditions, but the provenance graph shows only the tasks that ran.
* **Root graphs never return a newly computed scalar:** returning ``n`` above would publish a value with no creator, breaking the rule that workflows return existing data while only tasks create new data. A root graph returns task outputs, graph inputs, or collector-built containers, or nothing, declared explicitly with ``return {}``. Use an explicit task for a scientific result computed from inline state. Returning a bound literal directly fails when the graph is built, for the same reason.
* **Nested helpers may return control state:** a subgraph can return an inline value for its caller to consume as orchestration state, since the caller scope, not the provenance, receives it.
* **Explicit tasks are never inlined:** a ``@task`` function always runs as its own child process, even when its body is a single expression. Inlining never invents a calculation absent from the source.
* **Cheap by construction:** inline expressions run inside the graph process, so keep them to the supported operators. Anything else (formatting, method calls, nested task calls, slices, set and generator comprehensions, private attribute reads) belongs in a task and still raises ``GraphLanguageError``. Division by zero and non-finite results fail the run.

Loop iterations run one at a time and each iteration completes its whole scope before the next begins, so placements without a data dependency still run sequentially.
For example, stepping an inline counter after a calculation needs no ``after`` edge: the next iteration starts only after the calculation scope completes.

.. _topics:workflows:graphs:inline_collections:

Inline collections
^^^^^^^^^^^^^^^^^^

Typed lists and mappings thread through inline expressions without a task: annotate the port as ``list[T]`` or ``dict[str, T]`` on a graph input, a task input, or a task output, and every use below reads the declared element type.
A missing element annotation fails the build, so spell the member type instead of guessing.
Index a list with an integer, where negative positions count back from the end, and index a mapping with a string, where the key itself can be a wired value resolved at runtime.
Read public annotated item state directly, such as ``item.value`` on an owned ``Int`` member, while private names and method calls stay task concerns.
Collect filtered and nested results eagerly with list and dict comprehensions, including ``for key, value in mapping.items()`` pair iteration over a mapping; iterating a mapping directly yields its keys.
Comprehensions size themselves at runtime, so empty inputs simply collect empty results.
Collection literals inside these expressions must have one declared element type; standalone literal bindings remain unsupported.

.. code:: python

    from aiida.engine import graph, task

    @task
    def sum_values(values: list[int]) -> int:
        return sum(values)

    @graph
    def scaled_filtered(values: list[int], scale: int) -> int:
        scaled = [item * scale for item in values if item > 0]
        return sum_values(values=scaled)

The graph filters and scales its inputs inline, then the consumer task stores the scientific result.
A comprehension over a task-produced list reads the packing task's element hint without re-annotation, so ``[item * scale for item in packed]`` types its members from a ``pack`` task returning ``list[int]``.
Comprehensions over owned members keep the owned contract when they forward the members themselves, so ``[item for item in values]`` over ``list[Int]`` validates against a downstream ``list[Int]`` consumer; unwrapped or computed members fall back to plain contracts, so ``[item.value + 1 for item in values]`` feeds a ``list[int]`` consumer instead.
Inline indexing and comprehensions require Python container hints such as ``list[orm.Int]``. Pass ``orm.DataList`` and ``orm.DataList[T]`` wires whole instead.
Task or method calls inside an expression, slices, set or generator comprehensions, private attribute reads, and nested boolean combinations or conditional expressions inside a comprehension all stay task concerns and fail the build.
The engine semantics match scalar inline operations: expressions evaluate inside the graph process with no child processes, no ``CREATE`` links, and no provenance of their own; their values checkpoint with the scope while only task outputs are stored.
A root graph never returns a newly computed collection or scalar; route the value through a task and return the task output instead.
Returning an existing owned member itself stays under the unchanged owned-container contract and fails at launch, so consume it in a task first.

.. _topics:workflows:graphs:control_flow:

Subgraphs, branches, and loops
------------------------------

Calling a graph inside another graph places it as a subgraph, which runs as a scope of the same graph process:

.. code:: python

    @graph
    def outer(x: int, y: int, z: int) -> int:
        inner = multiply_add(x=x, y=y, z=z)
        return add(x=inner, y=x)

An ``if`` tests a bound name, a field, an inline expression such as ``x > 0``, a task call, or boolean combinations of those with ``and`` and ``or``, such as ``value != target and attempts < max_steps``.
Each ``and``/``or`` pair selects one side at runtime with short-circuit semantics: the right side runs only when the left side selects it, so a task call or a guarded operation there never runs when skipped.
Every operand must read as a boolean; Python operand tricks such as ``1 and 2`` fail when the graph is built.
Presence and member tests (``is None``, ``is not None``, ``is`` and ``is not`` against a declared error member, optionally under ``not``) lower to ephemeral boolean control values wherever a boolean reads: they work in an ``if`` or ``while`` test, on either side of ``and``/``or``, as named wires such as ``present = value is not None``, and inside selections.
Only these supported identity forms read as booleans; arbitrary ``x is y`` identities never run and fail when the graph is built.
Both arms are compiled; at runtime, only the selected arm runs, as a scope of the same graph process.
With an ``else``, both arms bind the same name to values of the same type:

.. code:: python

    @graph
    def choose(x: int, flag: bool) -> int:
        if flag:
            chosen = add(x=x, y=1)
        else:
            chosen = add(x=x, y=2)
        return chosen

Without an ``else``, the arm rebinds a name bound before the ``if``; when the test fails, the prior value is kept:

.. code:: python

    @graph
    def maybe_bump(x: int, flag: bool) -> int:
        total = add(x=x, y=1)
        if flag:
            total = add(x=total, y=10)
        return total

In a branch without an early return, each arm holds one statement: an assignment of a call, an assignment of a name bound earlier, such as ``chosen = first``, which runs no task, an assignment of one field of those, such as ``chosen = pair.sum``, an assignment of a whole namespace, such as ``chosen = pair``, an assignment of an inline expression, such as ``n = n - 1``, a ``while`` loop that rebinds one name bound before the ``if``, or another ``if``, such as an ``elif``, whose arms follow the same rules.

A return from a branch or loop exits the current graph invocation, and only continuing arms need to bind names used after the branch.
All successful returns must provide compatible graph outputs.
A taken return blocks later placements, including subsequent loop iterations, but does not cancel work that already started.
In a ``Result``-annotated graph, use ``Ok(...)`` for success or ``Err(Errors.MEMBER)`` for a declared failure.
A caller can handle the latter with ``catch_error``.
Whole-namespace arms on both sides must share the same fields.
The branch reserves the name ``condition`` for its test, so the arms cannot read a value of that name.
A conditional expression ``x if condition else y`` selects one value the same way, without running the unselected side:

.. code:: python

    @graph
    def choose_either(x: int, y: int, flag: bool) -> int:
        return add(x=x, y=1) if flag else add(x=y, y=2)

The condition follows the same rules as an ``if`` test, and each arm follows the same rules as an ``if`` arm: calls, constants, names, fields, namespaces, and inline expressions.
Both arms must expose the same wire, and only the taken arm ever runs, as a scope of the same graph process:

.. code:: python

    @graph
    def choose_scaled(value: int, flag: bool) -> int:
        chosen = (value + 1) if flag else (value - 1)
        return add(x=chosen, y=0)

A ``while`` tests a bound name, an inline expression such as ``n > 0``, a task call, or boolean combinations of those with ``and`` and ``or`` before every iteration.
A joined test re-evaluates from the rebound names each pass, so a bounded loop steps toward its target until it matches or the attempt budget runs out:

.. code:: python

    @graph
    def bounded_count(value: int, target: int, max_steps: int) -> int:
        attempts = 0
        while value != target and attempts < max_steps:
            value = value - 1
            attempts = attempts + 1
        return add(x=value, y=attempts)

The body rebinds names bound before the loop, with task calls, inline assignments such as ``n = n - 1``, scalar literal bindings such as ``attempts = 0``, ``if`` branches, or nested ``while`` loops.
A tested name must be rebound in the body; a tested call runs again after every iteration.
An inline test re-evaluates from the rebound names.
Names the body assigns without an enclosing binding are iteration-local, such as ``step`` below: declared on their first write, fresh every pass, never carried across iterations or visible after the loop.
Reading one before its write, assigning it on only one branch path, or reading it after the loop fails when the graph is built:

.. code:: python

    @task
    def trial(x: int) -> int:
        return x - 1

    @task
    def positive(x: int) -> bool:
        return x > 0

    @graph
    def stepped(x: int, keep_going: bool) -> int:
        while keep_going:
            step = trial(x=x)
            x = step
            keep_going = positive(x=x)
        return x

Counters and conditions stay inline: they need no ``@task``, and each ``@task`` runs as its own child process with its own provenance nodes.
Keep orchestration inline and scientific work in tasks, so the returned value is still a stored task output:

.. code:: python

    @graph
    def refine(x: int, rounds: int, attempt: int = 0) -> int:
        value = add(x=x, y=0)
        retry = attempt < rounds
        while retry:
            value = add(x=value, y=1)
            attempt = attempt + 1
            retry = attempt < rounds
        return value

The counter seeds from its default graph input (``attempt: int = 0``); a bare ``0`` literal leaves no trace.
Each iteration steps the counter with inline ``+`` and recomputes the ``<`` comparison, while ``add`` remains the only task.

``while`` takes no ``else``.
Each iteration runs as a numbered scope of the same graph process, with hierarchical call labels such as ``loop_1_iteration_0__add`` that preserve the iteration identity.
A loop that never runs leaves its names at their values from before the loop, as in Python.
A loop still running after 1000 iterations fails the graph process.

Launching
---------

Graphs can be launched like any other process, with a loaded AiiDA profile:

.. code:: python

    from aiida.engine import run_get_node, submit
    from my_module import multiply_add

    outputs, node = run_get_node(multiply_add, x=2, y=3, z=4)
    assert outputs['result'].value == 10

    # or

    node = submit(multiply_add, x=2, y=3, z=4)

* ``run_get_node`` blocks until the graph finishes in the current interpreter.
* ``submit`` returns the process node immediately and the daemon runs the graph in the background.
* Calling ``multiply_add(x=2, y=3, z=4)`` directly raises a :py:class:`~aiida.common.exceptions.GraphError`, because the graph body is never executed as Python.
* Graph inputs are the function parameters; an input omitted at launch takes its literal default.
* Graphs and tasks take no ``*args`` or ``**kwargs``, because every input needs its own declared port.
* Graph outputs can be task outputs or graph inputs; a graph with no outputs ends with an explicit ``return {}``.
  A root graph never returns a newly computed inline scalar (use an explicit task for a scientific result); a nested graph may return inline control state for its caller (see :ref:`topics:workflows:graphs:inline`).
* A graph is a workflow, so it returns existing data nodes -- the recipe's ``summarize`` report, for example; only tasks create new data (see :ref:`topics:provenance:concepts`).

Tasks can be run independently: ``run_get_node(add, x=1, y=2)`` launches a single task.
Function-based tasks require a type annotation for every parameter, including those with defaults, and for the return value.
Missing annotations raise ``GraphTypeCheckError`` when ``@task`` is applied, before graph build.
Calling ``add(x=1, y=2)`` directly raises a :py:class:`~aiida.common.exceptions.GraphError`, as for graphs.

.. _topics:workflows:graphs:where_to_define:

Where to define graphs
^^^^^^^^^^^^^^^^^^^^^^

Graphs and tasks can be defined in a module, a script, or a notebook.
No entry points or plugin packaging are needed: a graph is submitted directly from where it is defined, and the daemon only needs to import the module.
Each submission carries the graph structure and a pickled copy of every task, so the daemon needs no access to the files that define them.
These copies include helpers defined in the same file as the task.
Helpers imported from other files are referenced by name, so the daemon imports them; those files must be installed or on the daemon's ``PYTHONPATH``.

.. _topics:workflows:graphs:inspecting:

Validating graphs and inspecting runs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Call ``workflow.build()`` while developing a graph, or from a test, to catch unsupported syntax, bad wiring, and static contract mismatches without launching anything.
It returns ``None``; problems raise, naming the offending source line.
``build()`` only validates the declaration; the representation it compiles is an implementation detail user code never touches.
Then run a representative case and check its outputs before trying boundary cases, as shown in :ref:`topics:workflows:graphs:recipe`; runtime failures are not caught by ``build()``.
Inspect execution results through the launch outputs and the stored graph node: ``outputs['result']`` reads what tasks produced, while ``root.inputs.initial`` reads the flat workflow argument the run was launched with.

.. _topics:workflows:graphs:task_kinds:

Task kinds
----------

The ``task`` decorator accepts three kinds of objects:

* **Function**, ``@task``: runs its Python body and records a ``CalcFunctionNode``.
* **CalcJob**, ``add_calc = task(MyCalcJob)``: places a ``CalcJob`` subclass in the graph.
* **WorkChain**, ``add_chain = task(MyWorkChain)``: places a ``WorkChain`` subclass in the graph.

Each placement is a single task in the graph, with named inputs and a fixed set of outputs.
At runtime it runs as a child process of the graph.
A work chain keeps its own outline and child processes, so it appears in the provenance as a workflow nested under the graph.
Task and graph names become link labels in the provenance graph, so they must consist of alphanumerics and underscores and must not start or end with an underscore.

Calls resolve by declaration name, not by what a module-global variable happens to hold:

* a plain ``add(...)`` resolves because ``add`` is the declared ``@task`` name;
* a ``task(ArithmeticAddCalculation)`` factory variable such as ``add_calc`` resolves under its assigned variable name;
* rebinding either under another module-global name does not declare a new task: ``alias = add`` and ``alias = nested_graph`` fail when the graph is built, as does a stored ``alias = add.alias('scf')`` handle or a renamed import.
  Name repeated placements inline at the call site with ``add.alias('scf')(...)`` instead;
* enum members in member tests, module-qualified targets such as ``tasks.add``, and the callable mapped with ``par_map`` keep their existing resolution;
* values that are not declarations (module-global numbers, nodes, mappings, or attributes) are not wires.
  Pass them as graph inputs instead of reading a global, which the build reports as a missing graph input rather than a name to assign on an earlier line.

When the defining source cannot be read (for example a handle installed by a test double after import), function and graph names still match on their public name, while a source-less factory handle stays permissive: identity alone cannot tell a factory alias from its declaration, so no ordering heuristic is attempted.

Explicit placement names
^^^^^^^^^^^^^^^^^^^^^^^^

A task or graph called through ``.alias('scf')`` names its placement explicitly instead of reusing the task name:

.. code:: python

    @graph
    def two_steps(x: int, y: int) -> int:
        first = add.alias('scf')(x=x, y=y)
        return add.alias('nscf')(x=first, y=y)

* The constructor works for function tasks, ``CalcJob`` and ``WorkChain`` tasks, nested graphs, generic tasks, dotted and module call targets such as ``tasks.add.alias('scf')``, and the callable mapped with ``par_map``.
* Each placement in one graph body needs its own name: calling one task or graph twice without aliases fails when the graph is built, as does reusing one alias for two placements or mixing a bare call with an alias on the same name.
* The same rule covers maps: two default ``par_map`` placements over one callable share one map name and fail, so pass the alias on the callable (``par_map(task.alias('name'), values)``), which names the map placement exactly.
* Names are scoped to their body: branch arms, loop bodies, and nested graphs each keep their own placements, so both arms of an ``if`` or a loop body may reuse an outer alias.
* Generated branch, loop, and inline-operation names, as well as runtime map items and loop iteration labels, keep their automatic numbering.
* The alias is local to the call: it never mutates the task handle, so a later plain ``add(...)`` still places under its own name.
* It accepts only a non-empty string literal following the link-label contract; a variable or an invalid name fails when the graph is built.
* The compiled template, the provenance call labels, and the ``runtime_config`` entries below all carry the alias.
* This is unrelated to the module-level ``Forward`` input alias under :ref:`spreading <topics:workflows:graphs:spreading>`, which reuses an input declaration across graphs.

.. _topics:workflows:graphs:runtime_config:

Runtime configuration
^^^^^^^^^^^^^^^^^^^^^

Graphs submit like any other process: ``run_get_node(multiply_add_calc, x=2, y=3, z=4)`` takes flat workflow arguments, or the same mapping under ``inputs=``. Execution settings travel separately, under the launch-only ``runtime_config`` channel: they never masquerade as scientific inputs, though the snapshot itself is stored on the graph node so restarts keep working.
Each process placement takes an ordinary process input mapping, including a nested ``metadata`` mapping:

.. code:: python

    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    add_calc = task(ArithmeticAddCalculation)

    @graph
    def multiply_add_calc(x: int, y: int, z: int) -> int | float:
        product = multiply(x=x, y=y)
        total = add_calc(x=product, y=z)
        return total.sum

    outputs, node = run_get_node(
        multiply_add_calc,
        inputs={'x': 2, 'y': 3, 'z': 4},
        runtime_config={
            'add_calc': {
                'code': code,
                'metadata': {
                    'label': 'addition',
                    'options': {'resources': {'num_machines': 1}, 'withmpi': False},
                },
            },
        },
    )

Here ``code`` is an existing ``orm.Code`` instance, not an identifier encoded in a dictionary node.
Both ``run`` and ``submit`` accept the same separate launch channels.
Flattened workflow arguments such as ``x=2`` remain supported; ``runtime_config`` is never a workflow argument.
Standard root ``metadata`` such as ``label`` applies to the graph process itself.

Configuration-capable inputs are inferred from the concrete process specification:

* Inputs declared by the base ``CalcJob`` or ``WorkChain`` class, when still present in the concrete class. Base namespaces include their descendants and plugin extensions. This covers process metadata and, for ``CalcJob``, ``code``, ``monitors`` and ``remote_folder``.
* Inputs accepting only ``orm.Code`` subclasses, optionally together with ``None``, at any namespace depth. Mixed types such as ``Code | Int`` and opaque ``Dict`` inputs do not qualify.
* Execution inputs carried through ``spec.expose_inputs(...)``, including nested exposure chains. Scientific siblings in the exposed namespace still need graph wiring.

These rules apply to ``task(CalcJobSubclass)`` and ``task(WorkChainSubclass)``, not plain function tasks.
Explicit graph wiring always owns an input, including an executable or import folder.
Supplying that same input through configuration is an error, not an override or fallback, even if the values agree.
A whole-namespace wire reserves all its descendants; dictionary-valued leaf ports are atomic.
Separate namespace siblings can be wired and configured independently.
Ordinary process defaults apply after combining the bindings.

Nested graph placements introduce a configuration mapping level:

.. code:: python

    runtime_config = {
        'relax': {
            'add_calc': {
                'code': code,
                'metadata': {'options': {'resources': {'num_machines': 1}}},
            },
        },
    }

Here ``relax`` names a nested graph placement containing ``add_calc``.
For a WorkChain task, its exposed namespaces instead belong directly in its process input mapping, for example ``{'relax': {'base': {'pw': {'code': code}}}}``.
Configuration never reaches through an opaque WorkChain to its unexposed children.
Branch, loop and mapped-graph bodies introduce no configuration level; iterations and map items reuse the same static bindings.
Aliases name placements in the template.
Labels the engine generates at runtime (loop iterations, map items) keep their automatic names.

``workflow.build()`` needs no runtime configuration.
Launch validates supplied addresses, ownership and independently complete execution namespaces across all static branches, including bodies that may never execute.
Validation requiring scientific task outputs occurs when the complete child inputs are available, through the normal process launch machinery.
Missing required execution inputs fail validation; an omitted or empty placement entry is otherwise allowed.
Unknown placements and scientific input paths are rejected.
Child ``metadata.call_link_label`` belongs to the graph; child provenance suppression and dry runs are not supported.

Configured nodes retain ordinary child provenance input links.
The root records a configuration snapshot separately from its scientific inputs, preserving entity references through checkpoints and ``get_builder_restart()``.
Changing caller-owned mappings after launch does not change the snapshot.


Static optional inputs, such as a restart folder, need no declaration: wire `None` and the input stays out of the launch; wire a node and it arrives.
Unwired optional inputs were already left out; `None` now means the same.

Execution environments and memory recovery
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use an :class:`~aiida.engine.ExecutionEnvironment` to select a graph's execution configuration and recovery policy at launch.
It keeps resource requests and recovery out of the scientific graph definition.

.. code-block:: python

    from aiida.engine import ExecutionEnvironment, IncreaseMemory, RetryPolicy, SchedulerFailure, submit

    environment = ExecutionEnvironment(
        runtime_config={
            'solver': {
                'code': code,
                'metadata': {
                    'options': {
                        'resources': {'num_machines': 1},
                        'max_memory_kb': 8_000_000,
                    },
                },
            },
        },
        execution_policy={
            'solver': RetryPolicy(
                max_attempts=3,
                on={SchedulerFailure.OUT_OF_MEMORY: IncreaseMemory(factor=2, maximum_kb=32_000_000)},
            ),
        },
    )
    node = submit(workflow, inputs={'structure': structure}, execution_environment=environment)

Alternatively, pass the two mappings directly as ``runtime_config=`` and ``execution_policy=``.
Do not combine either direct channel with ``execution_environment=``.
Policies use the same static placement addresses as runtime configuration and cannot replace graph-wired inputs.

Initially, recovery applies only to scheduler-backed ``CalcJob`` placements, not function tasks or jobs hidden inside WorkChains.
Built-in recovery uses confirmed Slurm accounting records; scheduler stderr alone and a matching numeric exit status do not trigger it.
Set an explicit ``metadata.options.max_memory_kb`` in runtime configuration and a ``maximum_kb`` no higher than the chosen queue's limit.
AiiDA does not discover queue limits from Slurm; site integrations can impose additional limits via `Scheduler.get_effective_memory_request`.
The next request grows by the factor, rounded up to a whole kB and clamped to the ceiling.
If it is invalid or does not increase the effective scheduler request (for example due to Slurm's MiB rounding), the placement stops.
Each loop iteration or mapped item starts with a fresh budget, and the original attempt counts toward ``max_attempts``.

Each attempt has its own calculation node, stored inputs and outputs, and call label of the form ``graph_attempt_2__solver``.
Inspect ``node.execution_attempts`` for the child UUID, effective settings, classification, and decision for each attempt.
The graph exposes only the terminal attempt to downstream placements, with the same output and error contract it uses without a policy.
Completing an attempt does not rerun upstream work or roll back external side effects.
The resolved runtime configuration and policy are stored separately from scientific inputs, and checkpoint restoration reattaches dispatched attempts.

Scientific protocol preparation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A plugin-owned protocol resolver can return a :class:`~aiida.engine.PreparedRun` containing explicit scientific ``inputs``, an ``execution_environment``, a protocol identifier and version, and JSON-compatible ``overrides``.
Launch with ``submit(workflow, prepared_run=prepared)`` instead of passing the inputs and environment separately.
The graph node records the protocol metadata; the resolved scientific inputs still appear as ordinary graph inputs.
The resolver owns the mapping from semantic roles to placement names and should use provenance-producing processes for scientific transformations where needed.


.. _topics:workflows:graphs:dynamic_namespaces:

Dynamic namespaces
^^^^^^^^^^^^^^^^^^

Some process classes leave a namespace open: ``ShellJob`` accepts any files under ``nodes`` and names its outputs after the files it retrieves.
A task fixes the names and node types inside such namespaces with ``inputs`` and ``outputs``, so its ports stay static and AiiDA checks every connection before launch:

.. code:: python

    from aiida.calculations.shell import ShellJob
    from aiida.orm import Code, SinglefileData

    cat = task(ShellJob, inputs={'nodes': {'text': SinglefileData}}, outputs={'stdout': SinglefileData})
    count_words = task(ShellJob, inputs={'nodes': {'text': SinglefileData}}, outputs={'stdout': SinglefileData})

    @graph
    def copy_and_count(
        text: SinglefileData, cat_code: Code, wc_code: Code, cat_arguments: list[str], wc_arguments: list[str]
    ) -> SinglefileData:
        copied = cat(code=cat_code, arguments=cat_arguments, nodes={'text': text})
        counted = count_words(code=wc_code, arguments=wc_arguments, nodes={'text': copied.stdout})
        return counted.stdout

Declarations only add names inside dynamic namespaces; names the class already declares are rejected.
A task that finishes without one of its declared outputs counts as failed.

.. _topics:workflows:graphs:structured_inputs:

Structured inputs
-----------------

A :ref:`PortModel <topics:processes:usage:port_models>` annotation declares a nested input namespace with defaults and help text:

.. code:: python

    from aiida.engine import PortModel

    class Nested(PortModel):
        count: int = 2

    class Settings(PortModel):
        nested: Nested
        label: str = 'test'

    @task
    def read_count(settings: Settings) -> int:
        return settings.nested.count

    @graph
    def total(settings: Settings) -> int:
        first = read_count(settings=settings)
        return add(x=first, y=settings.nested.count)

    run_get_node(total, settings={'nested': {}})

Avoid the parameter name ``inputs``: ``run``, ``run_get_node``, and ``submit`` use that keyword for the complete input dictionary.

The launch value can be a mapping or a model instance.
Tasks receive the namespace as an attribute-accessible mapping, so methods defined on the model are unavailable inside the task.
Graphs pass whole namespaces or single fields on to tasks, either by naming the whole output or by spreading it with ``**``; the original input nodes are kept.
Missing required inputs are reported together in one ``MissingRequiredInputsError``.
Default factories run once, when the graph is validated, and must return JSON values; each launch receives its own copy.

Pydantic models
^^^^^^^^^^^^^^^^^

A pydantic ``BaseModel`` declares the same typed port namespaces as a ``PortModel``: nested models, defaults, and ``Field(description=...)`` help text become ports, stored field by field.
Leaves support ``str``, ``int``, ``float``, ``bool``, and their optional forms.
Tasks receive attribute-accessible mappings, not model instances, so model methods are unavailable.
Port-level validation applies: aliases and decorated validators are rejected at declaration; check values inside the ``@task`` body.

.. code:: python

    import pydantic

    class FlatSettings(pydantic.BaseModel):
        count: int = 2
        label: str = pydantic.Field(default='test', description='A label.')

    @task
    def read_flat_count(config: FlatSettings) -> int:
        return config.count + len(config.label)

    @graph
    def total_flat(config: FlatSettings) -> int:
        return read_flat_count(config=config)

    run_get_node(total_flat, config={})

.. note::

    Only a subset of pydantic carries over to ports.
    Leaves must be JSON-native (``str``, ``int``, ``float``, ``bool``, and their optional forms); anything else fails with a ``TypeError`` when the graph is built.
    Decorated validators (``field_validator``, ``model_validator``), aliases, and frozen or excluded fields are likewise rejected at declaration with a ``TypeError``.
    Move value checks into the ``@task`` body instead.

.. _topics:workflows:graphs:spreading:

Spreading and forwarding
^^^^^^^^^^^^^^^^^^^^^^^^

``**`` spreads a namespace input or the result of a multi-output call across the ports of a call.
Each field must match an input of the called task or graph, and each port is given once:

.. code:: python

    class AddBundle(PortModel):
        x: int
        y: int

    @graph
    def spread(bundle: AddBundle) -> int:
        return add(**bundle)

To pass a subset of fields or replace one, wire the ports one by one, such as ``add(x=1, y=bundle.y)``.

``Forward`` declares a namespace input with the same inputs as a task or graph, so a graph passes a whole input contract on without restating its ports.
It is ``Annotated`` metadata, like ``PortField``; the marker declares the namespace, so the base type is ``Any``:

.. code:: python

    from typing import Annotated, Any

    from aiida.engine import Forward

    @graph
    def forwarded(bundle: Annotated[Any, Forward(multiply_add)]) -> int:
        result = multiply_add(**bundle)
        return add(x=result, y=1)

``exclude`` leaves out ports that the graph wires itself; it takes one port name or a tuple of them, with dots for nested ports, such as ``exclude=('structure', 'pw.parameters')``.
An alias reuses one declaration across graphs:

.. code:: python

    MultiplyAddInputs = Annotated[Any, Forward(multiply_add, exclude=('z',))]

    @graph
    def forwarded_z(bundle: MultiplyAddInputs) -> int:
        return multiply_add(**bundle, z=1)

.. _topics:workflows:graphs:outputs:

Outputs
-------

Task outputs are fixed by the return annotation:

* A single-value annotation, such as ``-> int`` or ``-> list[int]``, declares one output named ``result``.
* A ``TypedDict`` annotation with all keys required declares one output per key.
* A ``PortModel`` annotation declares a nested output namespace, stored field by field.
* ``-> None`` declares no outputs, for tasks run for their side effects.

.. code:: python

    from typing import TypedDict

    class Pair(TypedDict):
        sum: int
        product: int

    @task
    def arithmetic(x: int, y: int) -> Pair:
        return {'sum': x + y, 'product': x * y}

    @graph
    def statistics(x: int, y: int):
        pair = arithmetic(x=x, y=y)
        return {'total': pair.sum, 'product': pair.product}

A container holding data nodes stores as an owned container instead of JSON: ``list[orm.Int]`` and ``typing.List[orm.Int]`` store as ``orm.DataList``, while ``dict[str, orm.Int]`` and ``typing.Dict[str, orm.Int]`` store as ``orm.DataDict``.
The same spelling works on task inputs, task outputs, and graph ports, so one placement can pack the container and the next can consume it.
The task body still receives a plain Python ``list`` or ``dict`` holding the member nodes, while the provenance wire carries the owned container.
Annotating the port directly with ``orm.DataList`` or ``orm.DataDict`` keeps passing the node itself.
Plain ``list[int]`` and ``dict[str, int]`` still store as JSON ``List`` and ``Dict`` nodes.
Only a direct member annotation of one ``DataNode`` subclass is mapped.

.. code:: python

    from aiida.orm import Int

    @task
    def pack(x: int, y: int) -> list[Int]:
        return [Int(x), Int(y)]

    @task
    def total(values: list[Int]) -> int:
        return sum(member.value for member in values)

    @graph
    def summed(x: int, y: int) -> int:
        packed = pack(x=x, y=y)
        return total(values=packed)

A graph returning one value declares one output named ``result``, and a graph returning a ``dict`` declares one output per key.
A nested ``dict`` declares nested outputs, and returning a whole namespace regroups its existing leaves under one output without creating data.
A leaf without a node, such as a ``None`` value for a nullable field, stays out of the emitted outputs.

Use ``forward_outputs`` in the final return mapping to forward a static output namespace without listing every field:

.. code-block:: python

    from aiida.engine import forward_outputs, graph

    @graph
    def summarize(x: int, y: int):
        pair = arithmetic(x=x, y=y)
        return {'arithmetic': forward_outputs(pair, exclude=('product',))}

Exclusions must be a literal tuple of distinct immediate field names.
Excluding a namespace removes its entire subtree; at least one field must remain.
An empty tuple excludes nothing.
The compiler wires the remaining fields directly to their existing nodes and preserves absent optional fields and namespaces.
The selection also works in a return mapping wrapped in ``Ok``.

A ``TypeVar`` annotation, such as ``def scale(value: T, factor: T) -> T`` with ``T = TypeVar('T', int, float)``, accepts any of its constraints.
When all values wired to ``T`` share one type, the output takes that type at this call.

.. _topics:workflows:graphs:declared_failures:

Declared task failures
----------------------

A task that can fail declares it with a ``Result[Success, Errors]`` return annotation.
``Errors`` is an ``ExitCodeEnum`` subclass holding the ``ExitCode`` values the task may return.
The body returns ``Ok`` with the outputs, or ``Err`` with the declared member:

.. code:: python

    from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, PortModel, Result, catch_error, graph, task

    class DivisionErrors(ExitCodeEnum):
        ZERO_DENOMINATOR = ExitCode(410, 'The denominator is zero.')

    class InputErrors(ExitCodeEnum):
        NEGATIVE_NUMERATOR = ExitCode(411, 'Negative numerator: {value}')

    @task
    def divide_signed(numerator: float, denominator: float) -> Result[float, DivisionErrors | InputErrors]:
        if denominator == 0:
            return Err(DivisionErrors.ZERO_DENOMINATOR)
        if numerator < 0:
            return Err(InputErrors.NEGATIVE_NUMERATOR.exit_code.format(value=str(numerator)))
        return Ok(numerator / denominator)

    @task
    def recover_zero(error: DivisionErrors) -> float:
        return 0.0  # neutral fallback

    @task
    def recover_negative(numerator: float, error: InputErrors) -> float:
        return abs(numerator)  # fall back to the magnitude

    @graph
    def ratio_signed(numerator: float, denominator: float) -> float:
        value, error = catch_error(divide_signed(numerator=numerator, denominator=denominator))
        if error is None:
            selected = value
        elif error is DivisionErrors.ZERO_DENOMINATOR:
            selected = recover_zero(error=error)
        else:
            selected = recover_negative(numerator=numerator, error=error)
        return selected

A bare call such as ``value = divide_signed(...)`` binds only the success value and propagates declared failures, retaining the child's original status and formatted message.
Use ``value, error = catch_error(divide_signed(...))`` to handle a failure instead.
On success, ``error`` is ``None``; on declared failure, ``value`` is ``None`` and ``error`` is the declared member.
For a nullable success type, check ``error`` to distinguish a successful ``None`` from failure.
``catch_error`` also accepts a direct nested graph call if that graph can propagate declared failures.
A graph return annotation describes its successful value, not whether it can fail.

Standard Python type checkers see the bare call's success type but cannot infer the context-sensitive capture types.
The intrinsic's Python signature uses ``Any`` for the captured success arm and ``ExitCodeEnum | None`` for the captured error arm.
Use a checker suppression where needed; ``build()`` remains authoritative for graph wiring.
The success type may be structured: a ``PortModel``, a pydantic model, or a named tuple declares a ``value`` namespace, stored field by field, and consuming tasks take the model as their input type:

.. code:: python

    class Quotient(PortModel):
        ratio: float

    @task
    def divide_quotient(numerator: float, denominator: float) -> Result[Quotient, DivisionErrors]:
        if denominator == 0:
            return Err(DivisionErrors.ZERO_DENOMINATOR)
        return Ok(Quotient(ratio=numerator / denominator))

    @task
    def read_quotient(value: Quotient) -> float:
        return value.ratio

Only static namespaces are supported; dynamic outputs stay out of graph tasks.
Error inputs arrive as the enum member itself, typed by the annotation, so handlers match on members directly.
Branches test the arms with ``is None`` and ``is not None``, or match one declared member with ``is`` and ``is not``, such as ``if error is DivisionErrors.ZERO_DENOMINATOR``.
An unknown member or a member outside the captured invocation's error contract fails when the graph is built.
A branch nests inside an error arm, so each declared member routes to its own handler task with the dispatch visible in the body.

A captured declared failure sets the child's exit status but counts as completed, so downstream error handling can run.
An uncaught declared failure stops further scheduling within the affected invocation and does not release consumers of its success value.
Undeclared failures, exceptions, and outputs missing from a completed task keep the previous behavior: dependents never start and the graph exits with ``ERROR_TASK_FAILED``.
A task without ``Result`` keeps its behavior too: returning an ``ExitCode`` exits the child with that status.
``Err`` accepts a member or its ``ExitCode`` value, formatted to fill a message template; anything else fails the task itself, as do bare returns from a ``Result`` task.

Error enums need unique positive statuses with string messages; statuses must not clash with the engine exit codes.

Process classes cannot annotate their returns, so a ``CalcJob`` or ``WorkChain`` task declares its failures with ``errors``.
The enum maps the exit statuses the process may finish with onto declared members, and the call gains an ``error`` arm:

.. code:: python

    from aiida.calculations.shell import ShellJob
    from aiida.orm import Code, SinglefileData

    class ShellErrors(ExitCodeEnum):
        COMMAND_FAILED = ExitCode(400, 'The command failed.')

    fail = task(
        ShellJob,
        inputs={'nodes': {'text': SinglefileData}},
        outputs={'stdout': SinglefileData},
        errors=ShellErrors,
    )

    @task
    def recover_shell(error: ShellErrors) -> str:
        return f'recovered from {error.status}'

    @task
    def read_stdout(content: SinglefileData) -> str:
        return content.get_content()

    @graph
    def recover_failing(text: SinglefileData, code: Code, arguments: list[str]) -> str:
        ran = fail(code=code, arguments=arguments, nodes={'text': text})
        if ran.error is not None:
            selected = recover_shell(error=ran.error)
        else:
            selected = read_stdout(content=ran.stdout)
        return selected

A child finishing with a mapped status counts as completed; other statuses fail the task as before.
Every output the failed process stored stays available next to the synthesized ``error`` arm, so a retry can chain the failed run's ``remote_folder`` or read its parsed files.
Only declared arms the run did not store read as ``None`` downstream, like the missing arm of a ``Result`` task.
``errors`` takes one enum or a union of them, and a process class that already declares an ``error`` output cannot take it.

.. _topics:workflows:graphs:retries:

Retrying declared failures
^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``while`` loop retries a fallible task: its body uses ``catch_error`` on every iteration, and the condition reads the latest error arm.

.. code:: python

    from aiida.engine import RestartErrors, catch_error
    from aiida.orm import StructureData

    class StepErrors(ExitCodeEnum):
        UNSTABLE = ExitCode(410, 'Unstable step.')

    @task
    def run_step(structure: StructureData, attempt: int) -> Result[float, StepErrors]:
        if attempt < 2:
            return Err(StepErrors.UNSTABLE)
        return Ok(1.5)

    @task
    def ensure(value: float | None) -> None:
        if value is None:
            raise ValueError('the step never succeeded.')

    @graph
    def restartable(structure: StructureData, max_attempts: int, attempt: int = 0) -> float:
        value, error = catch_error(run_step(structure=structure, attempt=attempt))
        retry = error is not None and attempt < max_attempts
        while retry:
            attempt = attempt + 1
            value, error = catch_error(run_step(structure=structure, attempt=attempt))
            retry = error is not None and attempt < max_attempts
        checked = ensure(value=value)  # noqa: F841 - the guard validates without feeding the return
        return value

The counter and the retry flag are inline orchestration state, not tasks.
The counter seeds from its default graph input (``attempt: int = 0``); a scalar literal binding such as ``attempt = 0`` can also initialize ephemeral orchestration state.
The retry predicate combines error presence with the budget using short-circuiting ``and``.
Every ``@task`` runs as its own child process with its own provenance nodes, so inlining the counter and the condition avoids a process per increment or comparison.
The scientific step stays a task, so the returned value is still a stored task output.
There is no inline ``raise``, so ``ensure`` fails the graph when no attempt succeeded.
This guard costs one child process but creates no output nodes; returning the step output directly preserves its node identity.
Each iteration rebinds every unpacked name, so an arm the latest attempt left absent reads as ``None``.
``_`` discards an arm without carrying it into the next iteration.
``RestartErrors`` names the failures of the restart machinery itself, with the statuses ``BaseRestartWorkChain`` uses (301, 302, 401, 402), so a task that gives up after the last attempt can return ``Err(RestartErrors.UNHANDLED_FAILURE)``.

The same loop restarts tasks that run out of walltime: each retry dispatches
a fresh child process with the same inputs, and the scheduler places it anew.
Only the error member differs from the budget example above:

.. code:: python

    class StepErrors(ExitCodeEnum):
        UNSTABLE = ExitCode(409, 'Unstable step.')
        OUT_OF_WALLTIME = ExitCode(410, 'The step ran out of walltime.')

    @task
    def run_scf(structure: StructureData, attempt: int) -> Result[float, StepErrors]:
        if attempt < 2:
            return Err(StepErrors.OUT_OF_WALLTIME)
        return Ok(1.5)

    @graph
    def restart_on_walltime(structure: StructureData, max_attempts: int, attempt: int = 0) -> float:
        value, error = catch_error(run_scf(structure=structure, attempt=attempt))
        retry = error is StepErrors.OUT_OF_WALLTIME and attempt < max_attempts
        while retry:
            attempt = attempt + 1
            value, error = catch_error(run_scf(structure=structure, attempt=attempt))
            retry = error is StepErrors.OUT_OF_WALLTIME and attempt < max_attempts
        checked = ensure(value=value)
        return value

Failures and restarts
^^^^^^^^^^^^^^^^^^^^^

Declared failures keep the graph alive, as above.
Anything else stops it: tasks that depend on a failed task never start; independent tasks still run, and the graph then exits with ``ERROR_TASK_FAILED``.
The graph checkpoint records dispatched and finished tasks with their scope hierarchy, so a restarted graph reattaches pending children and reuses finished work instead of resubmitting it.
Caching applies to tasks as to any other process.

.. _topics:workflows:graphs:ordering:

Explicit ordering
-----------------

The reserved ``after`` argument makes a task wait for another task without using its output:

.. code:: python

    @task
    def prepare(x: int) -> None:
        ...

    @graph
    def ordered(x: int) -> int:
        prepared = prepare(x=x)
        return add(x=x, y=1, after=prepared)

``after=(first, second)`` waits for both.
Task functions cannot have a parameter named ``after``.

.. _topics:workflows:graphs:partial:

Partial input bindings
----------------------

``partial`` binds some inputs of a task or graph without running anything, so one binding serves every use that shares those inputs.
It needs no import: the bare ``partial`` name is reserved in graph bodies and always binds.
Each use merges the fixed values with its own arguments into one ordinary placement, keeping the target's placement naming (including ``.alias(...)``), contracts, and type checking:

.. code:: python

    @graph
    def calibrated(x: int, y: int, z: int) -> int:
        configured = partial(add, y=y)
        first = configured(x=x)
        second = configured.alias('second_add')(x=z)
        return add.alias('total_add')(x=first, y=second)

A use takes the remaining inputs by keyword or, positionally, in the declared order of the inputs the binding leaves open: ``configured(item)`` and ``configured(x=item)`` both wire ``x``.
Bindings compose (``partial(configured, more=wire)``), nest inline (``partial(add, y=y)(x=x)``), and work in branch arms and loop bodies.
Fixed values capture the declaration-time references, so a later rebinding of the same name cannot change them.
Fixed inputs bind by keyword only; a positional fixed input, a duplicate or unknown fixed input, a missing required input at the call, or an illegal target (anything that is not a task or graph) fails when the graph is built.
A namespaced input merges field by field: fixing ``config={'first': a}`` and calling with ``config={'second': b}`` combines the disjoint leaves, while repeating a leaf still fails.
A use-site alias applies generically, including to inline bindings: ``partial(add, y=y).alias('named')(x=x)`` and ``par_map(partial(add, y=y).alias('named'), values)`` place under ``named``.
A graph partial used on its own inlines exactly like the graph.

Mapping over a partial is one consumer of the same mechanism: ``par_map`` over a partial binds every input but one, and each element wires into the single remaining input:

.. code:: python

    from aiida import orm
    from aiida.engine import graph, par_map

    # `add` is the intro task.
    @graph
    def calibrated_all(values: orm.DataList, y: int) -> orm.DataList:
        configured = partial(add, y=y)
        return par_map(configured, values)

The mapped target keeps its usual map contract of exactly one leaf output, and the map keeps its usual collection, ordering, and collector behavior; shared fixed inputs travel as ordinary wires, so every item waits for the fixed upstream outputs.

.. _topics:workflows:graphs:maps:

Parallel maps over containers
-----------------------------

``par_map`` dispatches a unary task or graph for every element of an ``orm.DataList`` or every value of an ``orm.DataDict``.
All items are dispatched before waiting for their results.
The result has the same container kind, preserving list order or dictionary keys and insertion order.

.. code:: python

    from aiida import orm
    from aiida.engine import graph, par_map, run, task

    @task
    def increment(value: int) -> int:
        return value + 1

    @graph
    def increment_all(values: orm.DataList) -> orm.DataList:
        mapped = par_map(increment, values)
        return mapped

    result = run(increment_all, values=orm.DataList([orm.Int(1), orm.Int(2)]))
    assert [item.value for item in result['result']] == [2, 3]

The mapped callable can also be a multi-step graph:

.. code:: python

    @graph
    def increment_twice(value: int) -> int:
        first = increment(value=value)
        return increment.alias('increment_2')(value=first)

    @graph
    def apply_graph(values: orm.DataList) -> orm.DataList:
        return par_map(increment_twice, values)

Each list element then runs as its own scope of the same graph process, including all of that graph's tasks dispatched with hierarchical call labels.
Graphs containing ``par_map`` can themselves be mapped over lists of lists.
``par_map`` also works inside ``if`` branches and ``while`` bodies.

The callable must declare exactly one input and one leaf output.
The collection must be a wire annotated as ``DataList`` or ``DataDict``; plain Python lists and dictionaries are not owned containers.
A task can produce the collection before it is mapped, and downstream tasks can consume the mapped result.
Element types are checked when each child receives its input.
Mapped ``CalcJob`` tasks and per-item metadata are not supported yet.

Empty collections produce empty containers without dispatching any item tasks.
A collector calculation creates the result container from the child outputs; the graph only returns it, preserving calculation/workflow provenance rules.
If any item fails or omits its declared output, the graph fails with ``ERROR_TASK_FAILED`` and does not run the collector.
Map progress is checkpointed, so restarting does not resubmit completed items.
Like task calls, ``par_map`` accepts ``after=placement`` for explicit ordering.

Provenance
----------

AiiDA records the graph run, the task runs, and their data:

* The graph run is a single process node: nested graphs, loop iterations, branch arms, and map elements never create intermediate process nodes.
* Each task run is a child process node, with a call link named after its placement in the graph.
  Tasks inside nested scopes carry hierarchical labels, such as ``multiply_add__multiply`` or ``loop_1_iteration_0__subtract``, that preserve their scope and iteration identity.
* Each annotated task input and output is a data node linked to the task node.

AiiDA stores plain Python inputs and outputs as nodes automatically; passing an existing node reuses it.
This conversion uses :ref:`to_aiida_type <topics:data_types:core:conversion>` and covers types with a registered conversion, such as ``int``, ``float``, ``str``, ``bool``, ``list``, and ``dict``.
For other types, annotate the port with a ``Data`` subclass or register a conversion.
For a ``PortModel`` input, each field is converted and stored as its own node.
Literal values in the graph body, such as the ``1`` in ``add(x=x, y=1)``, are stored only when their task runs, so an ``if`` arm that is not taken creates no nodes.

Task functions receive the types their annotations declare: Python values for Python annotations, nodes for ORM annotations.
Values a task computes but does not return leave no trace in the provenance graph.

.. _topics:workflows:graphs:gallery:

Example gallery
---------------

Complete, runnable graphs. Each links to the section that explains it.

Multiply and add, the smallest complete graph:

.. code:: python

    @graph
    def multiply_add(x: int, y: int, z: int) -> int:
        product = multiply(x=x, y=y)
        return add(x=product, y=z)

They build on the ``add`` and ``multiply`` tasks from the intro, plus these shared definitions:

.. code:: python

    from aiida import orm
    from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, Result

    class StepErrors(ExitCodeEnum):
        UNSTABLE = ExitCode(410, 'Unstable step.')

    @task
    def run_step(x: int, attempt: int) -> Result[int, StepErrors]:
        if attempt < 1:
            return Err(StepErrors.UNSTABLE)
        return Ok(x + 1)

    @task
    def ensure(value: int | None) -> None:
        if value is None:
            raise ValueError('the step never succeeded.')

    @task
    def expand_cell(structure: orm.StructureData) -> orm.StructureData:
        return structure

Branch on a flag
^^^^^^^^^^^^^^^^

.. code:: python

    @graph
    def choose(x: int, flag: bool) -> int:
        if flag:
            chosen = add(x=x, y=1)
        else:
            chosen = add(x=x, y=2)
        return chosen

See :ref:`topics:workflows:graphs:control_flow`.

Retry a declared failure with a budget
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    @graph
    def restartable(x: int, max_retries: int, attempt: int = 0) -> int:
        value, error = catch_error(run_step(x=x, attempt=attempt))
        while error is not None and attempt < max_retries:
            attempt = attempt + 1
            value, error = catch_error(run_step(x=x, attempt=attempt))
        checked = ensure(value=value)
        return value

See :ref:`topics:workflows:graphs:retries`.

Fan out over a container, then reduce inside one task
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(``for`` loops live in ``@task`` bodies, never in ``@graph`` bodies)

.. code:: python

    from aiida import orm
    from aiida.engine import par_map

    @task
    def mean_cell_volume(structures: orm.DataList) -> float:
        if not structures:
            raise ValueError('empty structure list')
        total = 0.0
        for structure in structures:
            total += structure.get_cell_volume()
        return total / len(structures)

    @graph
    def mean_expanded_volume(structures: orm.DataList) -> float:
        expanded = par_map(expand_cell, structures)
        return mean_cell_volume(structures=expanded)

See :ref:`topics:workflows:graphs:maps`.

Nest graphs as subgraphs
^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    @graph
    def outer(x: int, y: int, z: int) -> int:
        inner = multiply_add(x=x, y=y, z=z)
        return add(x=inner, y=x)

The nested graph runs as a scope of the same graph process, not as a child workflow. See :ref:`topics:workflows:graphs:control_flow`.

Handle a declared error without retrying
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, Result, catch_error

    class DivisionErrors(ExitCodeEnum):
        ZERO_DENOMINATOR = ExitCode(410, 'The denominator is zero.')

    @task
    def divide(numerator: float, denominator: float) -> Result[float, DivisionErrors]:
        if denominator == 0:
            return Err(DivisionErrors.ZERO_DENOMINATOR)
        return Ok(numerator / denominator)

    @task
    def recover_zero(error: DivisionErrors) -> float:
        return 0.0

    @graph
    def ratio_or_zero(numerator: float, denominator: float) -> float:
        value, error = catch_error(divide(numerator=numerator, denominator=denominator))
        if error is None:
            selected = value
        else:
            selected = recover_zero(error=error)
        return selected

See :ref:`topics:workflows:graphs:declared_failures`.

Run a ``CalcJob``
^^^^^^^^^^^^^^^^^

The executable arrives through ``runtime_config``, not the graph inputs.

.. code:: python

    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
    from aiida.orm import Code

    add_calc = task(ArithmeticAddCalculation)

    @graph
    def add_single(x: int, y: int) -> int | float:
        total = add_calc(x=x, y=y)
        return total.sum

Launch with ``runtime_config={'add_calc': {'code': code, 'metadata': {...}}}``.
See :ref:`topics:workflows:graphs:runtime_config`.

Run a ``WorkChain`` and combine it with a ``CalcJob`` in one graph
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    from aiida.engine import WorkChain
    from aiida.orm import Int

    from aiida.engine import calcfunction

    @calcfunction
    def store_sum(x: Int, y: Int) -> Int:
        return Int(x.value + y.value)

    class AddWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input('x', valid_type=Int)
            spec.input('y', valid_type=Int)
            spec.output('result', valid_type=Int)
            spec.outline(cls.add_numbers)

        def add_numbers(self):
            self.out('result', store_sum(self.inputs.x, self.inputs.y))

    add_chain = task(AddWorkChain)

    @graph
    def mixed(x: int, y: int, z: int) -> int | float:
        stepped = add_chain(x=x, y=y)
        total = add_calc(x=stepped.result, y=z)
        return total.sum

Add chains compute through a calculation, so their outputs are stored nodes.

Legacy processes keep their outline and children; the graph only connects them. See :ref:`topics:workflows:graphs:task_kinds`.

Submit a ``WorkChain`` on its own
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    from aiida.engine import WorkChain
    from aiida.orm import Int

    from aiida.engine import calcfunction

    @calcfunction
    def store_sum(x: Int, y: Int) -> Int:
        return Int(x.value + y.value)

    class AddWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input('x', valid_type=Int)
            spec.input('y', valid_type=Int)
            spec.output('result', valid_type=Int)
            spec.outline(cls.add_numbers)

        def add_numbers(self):
            self.out('result', store_sum(self.inputs.x, self.inputs.y))

    add_chain = task(AddWorkChain)

    @graph
    def add_twice(x: int, y: int) -> int:
        first = add_chain.alias('first')(x=x, y=y)
        return add_chain.alias('second')(x=first.result, y=y)

The work chain keeps its outline and children.
Each placement runs as a child workflow process under the graph.
See :ref:`topics:workflows:graphs:task_kinds`.

Pick a value with a conditional expression instead of a branch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    @graph
    def choose_scaled(value: int, flag: bool) -> int:
        chosen = (value + 1) if flag else (value - 1)
        return add(x=chosen, y=0)

Only the taken side runs. See :ref:`topics:workflows:graphs:control_flow`.

Order placements without passing values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    @task
    def prepare(x: int) -> None:
        ...

    @graph
    def ordered(x: int) -> int:
        prepared = prepare(x=x)
        return add(x=x, y=1, after=prepared)

``after=(first, second)`` waits for both. See :ref:`topics:workflows:graphs:ordering`.

Pass a structured input bundle instead of flat arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    from aiida.engine import PortModel

    class Nested(PortModel):
        count: int = 2

    class Settings(PortModel):
        nested: Nested
        label: str = 'test'

    @task
    def read_count(settings: Settings) -> int:
        return settings.nested.count

    @graph
    def total(settings: Settings) -> int:
        first = read_count(settings=settings)
        return add(x=first, y=settings.nested.count)

Each field becomes its own stored node. See :ref:`topics:workflows:graphs:structured_inputs`.

Bind shared inputs once with ``partial``:

.. code:: python

    @graph
    def add_shifted(x: int, y: int, z: int) -> int:
        add_y = partial(add, y=y)
        first = add_y.alias('first')(x=x)
        return add_y.alias('second')(x=first)

``partial`` needs no import and binds nothing by itself; each call site places independently. See :ref:`topics:workflows:graphs:partial`.


.. _topics:workflows:graphs:limitations:

Known limitations
-----------------

Under development
^^^^^^^^^^^^^^^^^

These are gaps in the current implementation, expected to be closed with further development:

* **Coarse error handling:** an undeclared task failure fails the graph, see `Failures and restarts`_. Declared failures branch and retry in the graph, see :ref:`topics:workflows:graphs:retries`; reusable error handlers and partial reruns are not yet available.
* **Stored provenance only:** graphs and their tasks always store their nodes; unstored runs and unstored intermediate nodes are not supported.
* **No dry runs:** graph metadata rejects ``dry_run``.
* **Monitor wiring:** dynamic ``CalcJob`` monitor mappings can be supplied through ``runtime_config``; graph wiring still needs a fixed namespace declaration.
* **Local function tasks:** a function task runs in the interpreter that runs the graph, on a daemon worker when submitted. Running it on a remote computer is not yet supported.
* **Serial loops:** a ``while`` runs one iteration at a time. Use ``par_map`` to run independent items of an owned container in parallel.
* **No per-iteration outputs:** a graph output holds one node, so a loop cannot return one result per iteration, such as the trajectory of each relaxation step. A task can copy the values into one list node, without links to the original nodes. Owned ``DataList``/``DataDict`` containers hold the original nodes in one output instead; use ``par_map`` to build one from per-item tasks.
* **No value validators:** port types are checked, and ``PortModel`` fields reject pydantic validators; check values inside a task.
* **Source-only authoring:** graphs are written as Python source. A graphical editor is planned.

Design constraints
^^^^^^^^^^^^^^^^^^

These follow from how graphs work and are expected to stay:

* **Static ports:** every task and graph input and output is declared statically; a dynamic namespace is usable only after a task declares its contents, see :ref:`topics:workflows:graphs:dynamic_namespaces`. This static shape is what allows AiiDA to check the whole graph before launch.
* **Whole-port type variables:** ports hold node types, and a ``List`` or ``Dict`` node records no element types. A ``TypeVar`` therefore annotates a whole port, such as ``a: T``; one inside another annotation, such as ``list[T]``, is rejected.
