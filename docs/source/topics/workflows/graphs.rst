.. _topics:workflows:graphs:

Graphs of tasks
===============

A graph declares dependencies between tasks. AiiDA parses the graph's Python source without executing its body, then schedules each task as a child process when its dependencies have finished.
Save declarations in an importable Python module, installed wherever the daemon runs. Definitions in notebooks, ``__main__``, and nested functions are not supported.

Declaring and launching
----------------------

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
    declaration = pipeline.build()

Calling a graph directly is not supported. ``build()`` returns a ``GraphSpec`` without running tasks or the graph body.
Graph inputs are the function parameters, and graph outputs reference task outputs or input leaves.
Graph declarations currently support ordinary positional-or-keyword parameters without parameter defaults; defaults can be declared on ``PortModel`` input fields.
Calls inside graphs must use named arguments. Arbitrary Python code, imports, comprehensions, and fan-out loops are rejected with a source location.

Task functions receive the runtime types their annotations declare: Python values for Python annotations and nodes for ORM annotations.
Their leaf outputs are converted to data nodes. Graphs return these existing nodes rather than creating new data themselves.
Every task is recorded with its own process node and a call link named after its placement.
Task functions can also be called or passed to ``run`` and ``submit`` independently.

Static named outputs
--------------------

Task outputs must be statically declared. A scalar return annotation declares a single ``result`` output.
Explicit output names declare multiple leaf outputs, returned as a tuple in the same order:

.. code:: python

    @task(outputs=('sum', 'product'))
    def arithmetic(x: int, y: int) -> tuple[int, int]:
        return x + y, x * y

    @graph
    def statistics(x: int, y: int):
        pair = arithmetic(x=x, y=y)
        return {'total': pair.sum, 'product': pair.product}

The return mapping declares named leaf outputs; it is not an output namespace.
Dynamic ports, nested output namespaces, ``PortModel`` task/graph returns, and runtime-keyed output collections are not supported.
A task annotated ``-> None`` has no outputs and can run for its side effects.

Structured inputs
-----------------

``PortModel`` declares fixed input namespaces, with nested fields, help text, defaults, and nullable values:

.. code:: python

    from aiida.engine import PortModel

    class Settings(PortModel):
        count: int = 2
        nullable: int | None

    class Configuration(PortModel):
        settings: Settings
        label: str = 'test'

    @task
    def read_config(config: Configuration) -> int:
        return config.settings.count

    @graph
    def configured(config: Configuration) -> int:
        first = read_config(config=config)
        return add(x=first, y=config.settings.count)

Launch with a mapping or model instance, for example ``run_get_node(configured, config={'settings': {'nullable': None}})``.
Models declare namespaces; tasks receive attribute-accessible namespace mappings, not reconstructed model instances.
A nullable field still requires its key unless it has a default. Missing required graph inputs are reported together by ``MissingRequiredInputsError``.
Whole namespaces and selected fields are wired without flattening ordinary dictionary-valued leaves or replacing original input-node identities.

Subgraphs, branches, and loops
-----------------------------

Calling another declared graph inside a graph places it as a subgraph. It runs as a child graph process:

.. code:: python

    @graph
    def outer(x: int, y: int) -> int:
        inner = pipeline(x=x, y=y)
        return add(x=inner, y=x)

An ``if`` must have one assignment to the same new name on each side. Both sides must produce compatible leaf outputs:

.. code:: python

    @graph
    def choose(x: int, flag: bool) -> int:
        if flag:
            chosen = add(x=x, y=1)
        else:
            chosen = add(x=x, y=2)
        return chosen

A ``while`` condition must be a bound name. Its body consists of task assignments, rebinding existing loop state, and must update the condition:

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

Loop iterations are child graph runs. A false initial condition skips the loop; downstream tasks depending on it are skipped too.
Outputs sourced from skipped tasks are not returned, so callers should ensure a loop runs when its final state is required.
The default limit is 1000 iterations; exceeding it with the condition still true fails the graph.

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

``after=(first, second)`` waits for both placements. ``after`` cannot be a task-function parameter.
Ordering dependencies are part of the serialized graph, checked for cycles, and preserved across checkpoints.

Persistence and failures
------------------------

Specifications store importable executor names and reject unsupported format versions or task kinds.
The graph checkpoint records dispatched/completed tasks and loop iterations so completed work is not dispatched again on resume.
A failed task prevents dependent tasks from starting and ends the graph with ``ERROR_TASK_FAILED``.
Normal AiiDA task caching remains available; graphs do not introduce recovery handlers, retry policies, monitors, or partial-rerun APIs.
