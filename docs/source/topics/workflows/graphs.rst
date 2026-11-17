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

.. _topics:workflows:graphs:recipe:

Authoring recipe
----------------

The following workflow moves a value toward a target, stopping when it reaches the target or uses its step budget.
Copy these definitions into a Python module:

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

    assert converge.build() is None

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

The stored workflow node keeps the launch inputs directly under ``root.inputs``.
Its output is the existing report node, not a copy:

.. code:: python

    summary = next(child for child in root.called if child.process_label == 'summarize')
    assert outputs['result'].uuid == summary.outputs.result.uuid

Also check the stopping conditions: exhausting the budget, starting at the target, and allowing no steps.
A descending case exercises the other branch of ``step_toward``:

.. code:: python

    for initial, target, budget, value, attempts, status in [
        (0, 5, 2, 2, 2, 'exhausted'),
        (4, 4, 5, 4, 0, 'converged'),
        (0, 3, 0, 0, 0, 'exhausted'),
        (2, -1, 10, -1, 3, 'converged'),
    ]:
        outputs, root = run_get_node(converge, initial=initial, target=target, max_steps=budget)
        assert root.is_finished_ok
        assert outputs['result'].get_dict() == {
            'value': value, 'target': target, 'attempts': attempts, 'status': status
        }

Graph language
--------------

AiiDA reads the source of a ``@graph`` function and compiles it for the engine; the compiled representation stays an implementation detail user code never touches.

.. important::

   **A graph body is never executed as Python.**
   It uses a very small subset of Python syntax; arbitrary Python code belongs in a ``@task``.

The graph body supports:

* ``name = task(...)`` assignments, with keyword or positional arguments; positional arguments follow the declared input order. Calling another graph works the same way.
* Graph inputs and names bound on an earlier line, such as ``product`` in ``add(x=product, y=z)``, as arguments.
* Literal numbers, strings, booleans, and ``None`` as arguments, such as ``y=1``.
* Scalar literals bound to names, such as ``attempts = 0`` or ``mode = 'square'``, see :ref:`topics:workflows:graphs:inline`.
* ``if``, with or without ``elif`` and ``else``, and ``while``, as well as conditional expressions ``x if condition else y``, see :ref:`topics:workflows:graphs:control_flow`.
* Inline expressions for orchestration state: numeric arithmetic ``+ - * // %``, comparisons ``< <= > >= == !=``, and unary ``+ - not``, such as ``iterations - 1`` or ``iterations > 0``, see :ref:`topics:workflows:graphs:inline`.
* One final ``return`` of a name, a field, or a call, or of a ``dict`` of those, possibly nested, with literal string keys; a graph with no outputs ends with an explicit ``return {}``.
* ``.key`` or ``['key']`` to select an output of a multi-output call or a field of a namespace input; ``.result`` on a single-output call is optional.
* ``a, b = task(...)`` to bind every output of a multi-output call, in declaration order, outside branches; loop bodies rebind unpacked names the same way.
* Calls through an imported module, such as ``my_module.add(...)``.
* ``dict`` literals with string keys as arguments: for namespace ports, such as ``nodes={'text': text}``, and for ``dict`` ports when every value is a literal.
* ``**bundle`` to spread a namespace-typed name across the ports of a call, see :ref:`topics:workflows:graphs:spreading`.
* ``after=first`` or ``after=(first, second)`` to wait for earlier calls without passing their values.
* A docstring as the first statement.

Every call is assigned to a name, including calls to tasks without outputs; ``return`` and the tests of ``if`` and ``while`` also take inline expressions and calls directly.
Each name is bound once; only ``if`` arms and ``while`` bodies rebind names bound before them.
Any other construct raises a ``GraphLanguageError`` naming its source line when the graph is validated with ``build()``.
For example, an inline comparison in an ``if`` condition just runs:

.. code:: python

    @graph
    def choose_by_sign(x: int) -> int:
        if x > 0:
            chosen = add(x=x, y=1)
        else:
            chosen = add(x=x, y=2)
        return chosen

.. _topics:workflows:graphs:inline:

Inline operations
^^^^^^^^^^^^^^^^^^

Arithmetic, comparisons, and unary operators compute orchestration state inline, without a task:
``+ - * // %``, ``< <= > >= == !=``, and unary ``+ - not``. Operands are graph inputs, names bound
on an earlier line, or literals. A ``while`` tests an inline comparison directly and steps its
counter with inline arithmetic:

.. code:: python

    @graph
    def count_down(n: int) -> None:
        while n > 0:
            n = n - 1
        return {}

Scalar literals bind the same way, without a task, such as ``attempts = 0``, ``running = False``, or ``mode = 'square'``.
A bound name wires its value into task arguments, branch arms, and loop state exactly like a computed inline result.
Only finite numbers, strings, booleans, and ``None`` bind; anything else -- collections, formatting, indexing -- still belongs in a task or a graph input.

Inline results are ephemeral orchestration state, not scientific data:

* **No provenance:** inline values never become data nodes and never carry links. Only task outputs
  are stored.
* **Checkpointed, not stored:** the scheduler keeps inline values in its scope state, so restarts
  resume counters and conditions, but the provenance graph shows only the tasks that ran.
* **Root graphs never return a newly computed scalar:** returning ``n`` above would publish a value
  with no creator, breaking the rule that workflows return existing data while only tasks create new
data. A root graph returns task outputs, graph inputs, or collector-built containers -- or nothing,
declared explicitly with ``return {}``. Use an explicit task
for a scientific result computed from inline state.
Returning a bound literal directly fails when the graph is built, for the same reason.
* **Nested helpers may return control state:** a subgraph can return an inline value for its caller to
consume as orchestration state, since the caller scope -- not the provenance -- receives it.
* **Explicit tasks are never inlined:** a ``@task`` function always runs as its own child process,
even when its body is a single expression. Inlining never invents a calculation absent from the source.
* **Cheap by construction:** inline expressions run inside the graph process, so keep them to the
supported operators. Anything else -- formatting, indexing, comprehensions, nested calls -- belongs
in a task and still raises ``GraphLanguageError``. Division by zero and non-finite results fail the run.

Loop iterations run one at a time and each iteration completes its whole scope before the next
begins, so placements without a data dependency still run sequentially. For example, stepping an
inline counter after a calculation needs no ``after`` edge: the next iteration starts only after the
calculation scope completes.

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

``run_get_node`` blocks until the graph finishes in the current interpreter.
``submit`` returns the process node immediately and the daemon runs the graph in the background.
Calling ``multiply_add(x=2, y=3, z=4)`` directly raises a :py:class:`~aiida.common.exceptions.GraphError`, because the graph body is never executed as Python.

Graph inputs are the function parameters; an input omitted at launch takes its literal default.
Graphs and tasks take no ``*args`` or ``**kwargs``, because every input needs its own declared port.
Graph outputs can be task outputs or graph inputs; a graph with no outputs ends with an explicit ``return {}``. A root graph never returns a newly computed inline scalar -- use an explicit task for a scientific result -- while a nested graph may return inline control state for its caller; see :ref:`topics:workflows:graphs:inline`.
A graph is a workflow, so it returns existing data nodes; only tasks create new data (see :ref:`topics:provenance:concepts`).

Tasks can be run independently: ``run_get_node(add, x=1, y=2)`` launches a single task.
Calling ``add(x=1, y=2)`` directly raises a :py:class:`~aiida.common.exceptions.GraphError`, as for graphs.

.. _topics:workflows:graphs:where_to_define:

Where to define graphs
^^^^^^^^^^^^^^^^^^^^^^

Graphs and tasks can be defined in a module, a script, or a notebook.
Each submission carries the graph structure and a pickled copy of every task, so the daemon needs no access to the files that define them.
These copies include helpers defined in the same file as the task.
Helpers imported from other files are referenced by name, so the daemon imports them; those files must be installed or on the daemon's ``PYTHONPATH``.

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

Explicit placement names
^^^^^^^^^^^^^^^^^^^^^^^^

A task or graph called through ``.alias('scf')`` names its placement explicitly instead of reusing the task name:

.. code:: python

    @graph
    def two_steps(x: int, y: int) -> int:
        first = add.alias('scf')(x=x, y=y)
        return add.alias('nscf')(x=first, y=y)

The constructor works for function tasks, ``CalcJob`` and ``WorkChain`` tasks, nested graphs, generic tasks, dotted and module call targets such as ``tasks.add.alias('scf')``, and the callable mapped with ``par_map``.
The alias is local to the call: it never mutates the task handle, so a later plain ``add(...)`` still places under its own name.
It accepts only a non-empty string literal following the link-label contract; a variable or an invalid name fails when the graph is built.
The compiled template, the provenance call labels, and the ``task_metadata`` entries below all carry the alias.
This is unrelated to the module-level ``Forward`` input alias under :ref:`spreading <topics:workflows:graphs:spreading>`, which reuses an input declaration across graphs.

Calculation job options
^^^^^^^^^^^^^^^^^^^^^^^

Calls to a ``CalcJob`` task inside a graph pass all inputs except ``metadata``:

.. code:: python

    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
    from aiida.orm import Code

    add_calc = task(ArithmeticAddCalculation)

    @graph
    def multiply_add_calc(x: int, y: int, z: int, code: Code) -> int | float:
        product = multiply(x=x, y=y)
        total = add_calc(x=product, y=z, code=code)
        return total.sum

Scheduler options are given at launch under ``task_metadata``, keyed by placement name:

.. code:: python

    run_get_node(multiply_add_calc, x=2, y=3, z=4, code=code, task_metadata={'add_calc': {'options': {...}}})

Every ``CalcJob`` placement needs an entry; a missing one fails the launch with a ``GraphValidationError`` naming the placement.
Nested graphs receive the same ``task_metadata``, keyed by their inner placement names, so give placements with different options distinct names.
Standard ``metadata`` such as ``label`` applies to the graph process itself.

Static optional inputs, such as a restart folder, need no declaration: wire `None`
and the input stays out of the launch; wire a node and it arrives. Unwired
optional inputs were already left out; `None` now means the same.

.. _topics:workflows:graphs:dynamic_namespaces:

Dynamic namespaces
^^^^^^^^^^^^^^^^^^

Some process classes leave a namespace open: ``ShellJob`` accepts any files under ``nodes`` and names its outputs after the files it retrieves.
A task fixes the names and node types inside such namespaces with ``inputs`` and ``outputs``, so its ports stay static and AiiDA checks every connection before launch:

.. code:: python

    from aiida.calculations.shell import ShellJob
    from aiida.orm import SinglefileData

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

A graph returning one value declares one output named ``result``, and a graph returning a ``dict`` declares one output per key.
A nested ``dict`` declares nested outputs, and returning a whole namespace regroups its existing leaves under one output without creating data.
A leaf without a node, such as a ``None`` value for a nullable field, stays out of the emitted outputs.

A ``TypeVar`` annotation, such as ``def scale(value: T, factor: T) -> T`` with ``T = TypeVar('T', int, float)``, accepts any of its constraints.
When all values wired to ``T`` share one type, the output takes that type at this call.

.. _topics:workflows:graphs:declared_failures:

Declared task failures
----------------------

A task that can fail declares it with a ``Result[Success, Errors]`` return annotation.
``Errors`` is an ``ExitCodeEnum`` subclass holding the ``ExitCode`` values the task may return.
The body returns ``Ok`` with the outputs, or ``Err`` with the declared member:

.. code:: python

    from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, PortModel, Result, graph, task

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
        value, error = divide_signed(numerator=numerator, denominator=denominator)
        if error is None:
            selected = value
        elif error is DivisionErrors.ZERO_DENOMINATOR:
            selected = recover_zero(error=error)
        else:
            selected = recover_negative(numerator=numerator, error=error)
        return selected

The call unpacks into ``(value, error)``; exactly one arm is present.
The success arm passes the value through, and each declared member routes to its own handler task.
Only the present arm creates data nodes; the absent arm reaches downstream inputs as ``None``.
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
An unknown compared name fails when the graph is built.
A branch nests inside an error arm, so each declared member routes to its own handler task with the dispatch visible in the body.

A declared failure sets the child's exit status but counts as completed, so dependents still run; its absent success arms read as ``None`` downstream.
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

A ``while`` loop retries a fallible task: its body unpacks the ``Result`` on every iteration, and the condition reads the latest error arm.

.. code:: python

    from aiida.engine import RestartErrors
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
        value, error = run_step(structure=structure, attempt=attempt)
        retry = error is not None and attempt < max_attempts
        while retry:
            attempt = attempt + 1
            value, error = run_step(structure=structure, attempt=attempt)
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
Presence and member tests (``is None``, ``is not None``, ``is`` and ``is not`` against a declared error
member, optionally under ``not``) lower to ephemeral boolean control values wherever a boolean reads:
they work in an ``if`` or ``while`` test, on either side of ``and``/``or``, as named wires such as
``present = value is not None``, and inside selections. Only these supported identity forms read as
booleans; arbitrary ``x is y`` identities never run and fail when the graph is built.
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

Each arm holds one statement: an assignment of a call, an assignment of a name bound earlier, such as ``chosen = first``, which runs no task, an assignment of one field of those, such as ``chosen = pair.sum``, an assignment of a whole namespace, such as ``chosen = pair``, an assignment of an inline expression, such as ``n = n - 1``, a ``while`` loop that rebinds one name bound before the ``if``, or another ``if``, such as an ``elif``, whose arms follow the same rules.
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
A tested name must be rebound in the body; a tested call runs again after every iteration. An inline test re-evaluates from the rebound names.
Names the body assigns without an enclosing binding are iteration-local, such as ``step`` below: declared on their first write, fresh every pass, never carried across iterations or visible after the loop.
Reading one before its write, assigning it on only one branch path, or reading it after the loop fails when the graph is built:

.. code:: python

    @task
    def trial(x: int) -> int:
        return x - 1

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
Each iteration runs as a numbered scope of the same graph process, with hierarchical call labels such as
``loop_1_iteration_0__add`` that preserve the iteration identity.
A loop that never runs leaves its names at their values from before the loop, as in Python.
A loop still running after 1000 iterations fails the graph process.

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
        return increment(value=first)

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
* Each task run is a child process node, with a call link named after its placement in the graph. Tasks inside nested scopes carry hierarchical labels, such as ``multiply_add__multiply`` or ``loop_1_iteration_0__subtract``, that preserve their scope and iteration identity.
* Each annotated task input and output is a data node linked to the task node.

AiiDA stores plain Python inputs and outputs as nodes automatically; passing an existing node reuses it.
This conversion uses :ref:`to_aiida_type <topics:data_types:core:conversion>` and covers types with a registered conversion, such as ``int``, ``float``, ``str``, ``bool``, ``list``, and ``dict``.
For other types, annotate the port with a ``Data`` subclass or register a conversion.
For a ``PortModel`` input, each field is converted and stored as its own node.
Literal values in the graph body, such as the ``1`` in ``add(x=x, y=1)``, are stored only when their task runs, so an ``if`` arm that is not taken creates no nodes.

Task functions receive the types their annotations declare: Python values for Python annotations, nodes for ORM annotations.
Values a task computes but does not return leave no trace in the provenance graph.

.. _topics:workflows:graphs:inspecting:

Validating graphs and inspecting runs
--------------------------------------

Call ``assert workflow.build() is None`` while developing a graph, or from a test, to catch unsupported syntax, bad wiring, and static contract mismatches without launching anything.
``build()`` only validates the declaration; the representation it compiles is an implementation detail user code never touches.
Then run a representative case and check its outputs before trying boundary cases, as shown in :ref:`topics:workflows:graphs:recipe`; runtime failures are not caught by ``build()``.
Inspect execution results through the launch outputs and the stored graph node: ``outputs['result']`` reads what tasks produced, while ``root.inputs.initial`` reads the flat workflow argument the run was launched with.

Failures and restarts
---------------------

Tasks that depend on a failed task never start; independent tasks still run, and the graph then exits with ``ERROR_TASK_FAILED``.
A declared ``Result`` failure is not a failure in this sense: the child exits with the declared status, the graph branches on it, and the graph itself can exit cleanly; see :ref:`topics:workflows:graphs:declared_failures`.
The graph checkpoint records dispatched and finished tasks with their scope hierarchy, so a restarted graph reattaches pending children and reuses finished work instead of resubmitting it.
Caching applies to tasks as to any other process.

Known limitations
-----------------

Under development
^^^^^^^^^^^^^^^^^

These are gaps in the current implementation, expected to be closed with further development:

* **Coarse error handling:** an undeclared task failure fails the graph, see `Failures and restarts`_. Declared failures branch and retry in the graph, see :ref:`topics:workflows:graphs:retries`; reusable error handlers and partial reruns are not yet available.
* **Stored provenance only:** graphs and their tasks always store their nodes; unstored runs and unstored intermediate nodes are not supported.
* **No dry runs:** graph metadata rejects ``dry_run``.
* **No monitors yet:** ``CalcJob`` monitor mappings cannot be wired yet, since dictionary syntax only fills fixed namespaces.
* **Local function tasks:** a function task runs in the interpreter that runs the graph, on a daemon worker when submitted. Running it on a remote computer is not yet supported.
* **Serial loops:** a ``while`` runs one iteration at a time. Use ``par_map`` to run independent items of an owned container in parallel.
* **No per-iteration outputs:** a graph output holds one node, so a loop cannot return one result per iteration, such as the trajectory of each relaxation step. A task can copy the values into one list node, without links to the original nodes. Container data types, in development, will hold the original nodes in one output.
* **No value validators:** port types are checked, and ``PortModel`` fields reject pydantic validators; check values inside a task.
* **Source-only authoring:** graphs are written as Python source. A graphical editor is planned.

Design constraints
^^^^^^^^^^^^^^^^^^

These follow from how graphs work and are expected to stay:

* **Static ports:** every task and graph input and output is declared statically; a dynamic namespace is usable only after a task declares its contents, see :ref:`topics:workflows:graphs:dynamic_namespaces`. This static shape is what allows AiiDA to check the whole graph before launch.
* **Whole-port type variables:** ports hold node types, and a ``List`` or ``Dict`` node records no element types. A ``TypeVar`` therefore annotates a whole port, such as ``a: T``; one inside another annotation, such as ``list[T]``, is rejected.
* **Untyped adapted spreads:** a pydantic model or named tuple input is converted to a ``PortModel`` at declaration, but type checkers read the original class, so mypy reports ``Argument after ** must be a mapping`` for ``**bundle``. The graph runs regardless; declare a ``PortModel`` for a type-checked spread.
