.. _topics:workflows:graphs:

Graphs of tasks
===============

Workflows can be built from two decorators applied to plain Python functions.
``@task`` marks a step that will run on the daemon workers.
``@graph`` marks a workflow function that combines tasks and other graphs.

Task bodies
-----------

Inside ``@task`` bodies you can write anything that Python supports.
Only the task itself and its annotated inputs and outputs end up in the database and the provenance graph: one process node per task, one data node per declared output and input.
Plain values become stored nodes at the boundary: inputs once when the workflow launches, outputs when each task finishes; passing a node reuses it instead.
Anything that is not an annotated input or output never happened as far as AiiDA is concerned.

Graph bodies
------------

``@graph`` decorated workflows are plain Python functions using a tiny embedded language, a subset of Python: assignments, calls, and returns, plus ``if`` and ``while`` over task results.
AiiDA walks their source and lowers the supported constructs into an intermediate representation, a static JSON-serializable DAG of tasks, dependencies, and typed ports, rejecting everything else with a source location.
This allows the workflow to be validated upfront.
When submitted, the workflow source is parsed into an intermediate representation, which the engine runs instead of the Python body.
An ``if`` becomes a branch holding both sides in the spec, dispatching exactly one as a child graph process at runtime.
A ``while`` becomes a loop dispatching numbered child runs that thread state between iterations.
The plan language is:

* ``name = task(...)`` assignments; graphs call other graphs the same way
* ``if`` and ``else`` each storing their outcome under the same name
* ``while`` over a named check with no ``else``, updating the check inside the body
* ``(a, b) = task(...)`` only for tasks with several outputs, one name per output
* arguments by name like ``x=1`` or by position; no ``*args``, no ``**kwargs``
* literal defaults like ``def f(value=3)``
* ``.result`` only on single-output tasks; ``.key`` or ``['key']`` only on grouped outputs
* one ``return`` at the end, of a task output, a graph input, or a flat mapping of those
* ``after=...`` for ordering without passing values

Anything else the Python language supports is rejected with an actionable error message; moving the offending code into a ``@task`` body is usually the fix.
Body code would execute blockingly in the interpreter, while tasks execute non-blockingly on the daemon workers.

A graph declares dependencies between tasks. Each task is scheduled as a child process when its dependencies have finished.
Save declarations in an importable Python module, installed wherever the daemon runs.
Notebook, ``__main__``, and nested function declarations are not yet supported.

Declaring and launching
-----------------------

For example, save this as ``my_workflow.py``:

.. code:: python

    from aiida.engine import graph, task

    @task
    def add(x: int, y: int) -> int:
        return x + y

    @graph
    def pipeline(x: int, y: int) -> int:
        first = add(x=x, y=y)
        return add(x=first, y=y)

Launch it from another module or an interactive interpreter with a loaded AiiDA profile:

.. code:: python

    from aiida.engine import run_get_node, submit
    from my_workflow import pipeline

    outputs, node = run_get_node(pipeline, x=2, y=3)
    assert outputs['result'].value == 8
    submitted = submit(pipeline, x=2, y=3)

Calling a graph directly is not supported.
Launch it with ``run`` or ``submit``; graph lowering is internal to the engine.
Graph inputs are the function parameters, with literal defaults filled when absent, and graph outputs reference task outputs or input leaves.
Several names can share one placement.

Task functions receive the runtime types their annotations declare: Python values for Python annotations and nodes for ORM annotations.
Their leaf outputs are converted to data nodes.
Graphs return these existing nodes rather than creating new data themselves.
Every task is recorded with its own process node and a call link named after its placement.
Task functions can also be called or passed to ``run`` and ``submit`` independently.

Structured inputs
-----------------

``PortModel`` declares fixed input namespaces, with nested fields, help text, defaults, and nullable values:

.. code:: python

    from aiida.engine import PortModel

    class Nested(PortModel):
        count: int = 2

    class Inputs(PortModel):
        nested: Nested
        label: str = 'test'

    @task
    def read_count(inputs: Inputs) -> int:
        return inputs.nested.count

    @graph
    def total(inputs: Inputs) -> int:
        first = read_count(inputs=inputs)
        return add(x=first, y=inputs.nested.count)

Launch with a mapping or model instance, for example ``run_get_node(total, inputs={'nested': {}})``.
Models declare namespaces; tasks receive attribute-accessible namespace mappings, not reconstructed model instances.
Missing required graph inputs are reported together by ``MissingRequiredInputsError``.
Model default factories evaluate on every launch; results must be finite JSON values, so launches never share mutable defaults.
Whole namespaces and selected fields are wired without flattening ordinary dictionary-valued leaves or replacing original input-node identities.

Static named outputs
--------------------

Task outputs must be statically declared.
A scalar return annotation declares a single ``result`` output.
A total ``TypedDict`` return annotation declares one leaf output per key, returned as a mapping:

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

The return mapping declares named leaf outputs; it is not an output namespace.
``PortModel`` task/graph returns are not yet supported.
Dynamic ports, nested output namespaces, and runtime-keyed output collections are not supported.
A task annotated ``-> None`` has no outputs and can run for its side effects.

Subgraphs, branches, and loops
------------------------------

Calling another declared graph inside a graph places it as a subgraph.
It runs as a child graph process:

.. code:: python

    @graph
    def outer(x: int, y: int) -> int:
        inner = pipeline(x=x, y=y)
        return add(x=inner, y=x)

An ``if`` becomes a branch holding both sides in the spec, dispatching exactly one as a child graph process at runtime.
Its condition may be a bound name or a direct task call, which lowers like the bound form.
Each side must assign one new name shared by both, with compatible leaf outputs:

.. code:: python

    @graph
    def choose(x: int, flag: bool) -> int:
        if flag:
            chosen = add(x=x, y=1)
        else:
            chosen = add(x=x, y=2)
        return chosen

A ``while`` condition may be a bound name or a direct task call, re-evaluated every iteration.
Its body consists of task assignments, rebinding existing loop state, and must update the condition:

.. code:: python

    @task
    def subtract(x: int) -> int:
        return x - 1

    @task
    def positive(x: int) -> bool:
        return x > 0

    @graph
    def count(x: int, keep_going: bool) -> int:
        while keep_going:
            x = subtract(x=x)
            keep_going = positive(x=x)
        return x

Loop iterations are child graph processes.
A loop that is never entered returns its initial state, like the equivalent Python loop.
The default limit is 1000 iterations; exceeding it with the condition still true raises an error, failing the graph process.

Explicit ordering
-----------------

Use the reserved ``after`` call argument when a task must wait for another without consuming its output:

.. code:: python

    @task
    def prepare(x: int) -> None:
        # Perform a provenance-aware side effect.
        pass

    @graph
    def ordered(x: int) -> int:
        prepared = prepare(x=x)
        result = add(x=x, y=1, after=prepared)
        return result

``after=(first, second)`` waits for both placements.
``after`` cannot be a task-function parameter.
Ordering dependencies are part of the serialized graph, checked for cycles, and preserved across checkpoints.

Persistence and failures
------------------------

Specifications store importable executor names and reject unsupported format versions or task kinds.
The graph checkpoint records dispatched and completed tasks, loop iterations, and passed-through initial loop state, so completed work is not dispatched again on resume.
A failed task prevents dependent tasks from starting and ends the graph with ``ERROR_TASK_FAILED``.
Normal AiiDA task caching remains available.
Graphs do not yet introduce recovery handlers, retry policies, monitors, or partial-rerun APIs, but are all planned to be supported.
