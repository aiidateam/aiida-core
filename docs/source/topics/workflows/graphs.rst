.. _topics:workflows:graphs:

Graphs
======

.. versionadded:: 3.0

Besides work chains and work functions, workflows can also be written as graphs: plain Python functions that connect individual steps, called tasks.
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

For workflows that pass data from step to step, graphs have these advantages over work chains:

* **Less boilerplate:** inputs and outputs come from function signatures, so no ``define`` method, ``spec`` or outline is needed.
* **No subclassing:** graphs are plain decorated functions; work chains require subclassing ``WorkChain``.
* **Inspectable before launch:** the graph structure is a plain object that can be checked, drawn, and processed by tools, see :ref:`topics:workflows:graphs:inspecting`.
* **Early errors:** AiiDA checks the whole graph before any task runs, and each error names its source line. A work chain only fails at runtime, when it reaches the faulty step.
* **Fast iteration:** edit the source and resubmit. Each submission carries its own copy of the graph structure and the task bodies, so the daemon needs no restart.
* **Recorded structure:** the graph structure is stored as an input of the graph process, so the provenance shows what was planned as well as what ran.

Graph language
--------------

AiiDA reads the source of a ``@graph`` function and builds an intermediate representation from it: a JSON-serializable graph of tasks, their typed ports, and the dependencies between them.
The engine executes this intermediate representation.

.. important::

   **A graph body is never executed as Python.**
   It uses a very small subset of Python syntax; arbitrary Python code belongs in a ``@task``.

The graph body supports:

* ``name = task(...)`` assignments, with keyword or positional arguments; positional arguments follow the declared input order. Calling another graph works the same way.
* Graph inputs and names bound on an earlier line, such as ``product`` in ``add(x=product, y=z)``, as arguments.
* Literal numbers, strings, booleans, and ``None`` as arguments, such as ``y=1``.
* ``if``, with or without ``else`` but without ``elif``, and ``while``, see :ref:`topics:workflows:graphs:control_flow`.
* One final ``return`` of a name, a field, or a call, or of a flat ``dict`` of those with literal string keys.
* ``.key`` or ``['key']`` to select an output of a multi-output call or a field of a namespace input; ``.result`` on a single-output call is optional.
* ``a, b = task(...)`` to bind every output of a multi-output call, in declaration order, outside branches and loops.
* Calls through an imported module, such as ``my_module.add(...)``.
* ``dict`` literals with string keys as arguments: for namespace ports, such as ``nodes={'text': text}``, and for ``dict`` ports when every value is a literal.
* ``**bundle`` to spread a namespace-typed name across the ports of a call, see :ref:`topics:workflows:graphs:spreading`.
* ``after=first`` or ``after=(first, second)`` to wait for earlier calls without passing their values.
* A docstring as the first statement.

Every call is assigned to a name, including calls to tasks without outputs; only ``return`` and the test of an ``if`` or ``while`` take a call directly.
Each name is bound once; only ``if`` arms and ``while`` bodies rebind names bound before them.
Any other construct raises a ``GraphLanguageError`` naming its source line when the intermediate representation is built.
For example, an inline comparison in an ``if`` condition:

.. code:: python

    @graph
    def choose_by_sign(x: int) -> int:
        if x > 0:
            chosen = add(x=x, y=1)
        else:
            chosen = add(x=x, y=2)
        return chosen

fails with:

.. code:: text

    GraphLanguageError my_module.py:3:8: my_module:choose_by_sign: operators compute a new value, which only a task can create and record; put this check in a task and use its result instead
        if x > 0:
           ^

Computations such as ``x > 0`` belong in tasks for three reasons:

* **Provenance:** every data node in AiiDA is created by a calculation that records its inputs (see :ref:`topics:provenance:concepts`). The ``Bool`` result of ``x > 0`` computed inline would have no creator.
* **Explicit tasks:** every calculation in the provenance graph is a call written in the graph body. Compiling ``x > 0`` into an implicit task would record a calculation absent from the source.
* **Non-blocking execution:** tasks run as separate processes, on daemon workers when submitted. Inline code would run inside the graph process and could block it, and AiiDA cannot tell in advance how expensive an expression is.

Instead, a task returning the check creates the node, and the ``if`` branches on it:

.. code:: python

    @task
    def is_positive(x: int) -> bool:
        return x > 0

    @graph
    def choose_by_sign(x: int) -> int:
        positive = is_positive(x=x)
        if positive:
            chosen = add(x=x, y=1)
        else:
            chosen = add(x=x, y=2)
        return chosen

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
Graph outputs can be task outputs or graph inputs.
A graph is a workflow, so it returns existing data nodes; only tasks create new data (see :ref:`topics:provenance:concepts`).

Tasks can be run independently: ``run_get_node(add, x=1, y=2)`` launches a single task.

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
Graphs pass whole namespaces or single fields on to tasks; the original input nodes are kept.
Missing required inputs are reported together in one ``MissingRequiredInputsError``.
Default factories run once, when the intermediate representation is built, and must return JSON values; each launch receives its own copy.

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
An output whose source holds no node, such as an optional input left at ``None``, stays out of the emitted outputs.

A ``TypeVar`` annotation, such as ``def scale(value: T, factor: T) -> T`` with ``T = TypeVar('T', int, float)``, accepts any of its constraints.
When all values wired to ``T`` share one type, the output takes that type at this call.

.. _topics:workflows:graphs:control_flow:

Subgraphs, branches, and loops
------------------------------

Calling a graph inside another graph places it as a subgraph, which runs as a child graph process:

.. code:: python

    @graph
    def outer(x: int, y: int, z: int) -> int:
        inner = multiply_add(x=x, y=y, z=z)
        return add(x=inner, y=x)

An ``if`` tests a bound name, a field, or a task call.
The intermediate representation holds both arms; at runtime, only the selected arm runs, as a child graph process.
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

Each arm holds one statement: an assignment of a call, an assignment of a name bound earlier, such as ``chosen = first``, which runs no task, or a ``while`` loop that rebinds one name bound before the ``if``.
The branch reserves the name ``condition`` for its test, so the arms cannot read a value of that name.

A ``while`` tests a bound name or a task call before every iteration.
The body rebinds names bound before the loop, with task calls, ``if`` branches, or nested ``while`` loops.
A tested name must be rebound in the body; a tested call runs again after every iteration:

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

``while`` takes no ``else``.
Each iteration runs as a numbered child graph process.
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

Provenance
----------

AiiDA records the graph run, the task runs, and their data:

* The graph run is a process node.
* Each task run is a child process node, with a call link named after its placement in the graph.
* Each annotated task input and output is a data node linked to the task node.

AiiDA stores plain Python inputs and outputs as nodes automatically; passing an existing node reuses it.
This conversion uses :ref:`to_aiida_type <topics:data_types:core:conversion>` and covers types with a registered conversion, such as ``int``, ``float``, ``str``, ``bool``, ``list``, and ``dict``.
For other types, annotate the port with a ``Data`` subclass or register a conversion.
For a ``PortModel`` input, each field is converted and stored as its own node.
Literal values in the graph body, such as the ``1`` in ``add(x=x, y=1)``, are stored only when their task runs, so an ``if`` arm that is not taken creates no nodes.

Task functions receive the types their annotations declare: Python values for Python annotations, nodes for ORM annotations.
Values a task computes but does not return leave no trace in the provenance graph.

.. _topics:workflows:graphs:inspecting:

Inspecting the intermediate representation
------------------------------------------

``multiply_add.build()`` returns the intermediate representation without running any task.
Errors in the graph source surface here, before launch.

``to_dict()`` returns it as a JSON-serializable ``dict``, and ``GraphIR.from_dict`` reads it back.
The ``payload`` of each task holds its pickled copy, see :ref:`topics:workflows:graphs:where_to_define`.

.. dropdown:: JSON for ``multiply_add``, abridged

    .. code:: json

        {
          "identifier": "my_module:multiply_add",
          "tasks": [
            {
              "name": "multiply",
              "kind": "process",
              "spec": {"identifier": "multiply", "executor": {"module": "my_module", "name": "multiply", "payload": "..."}}
            },
            {
              "name": "add",
              "kind": "process",
              "spec": {"identifier": "add", "executor": {"module": "my_module", "name": "add", "payload": "..."}}
            }
          ],
          "dependencies": [{"source": "multiply", "target": "add", "source_port": "result", "target_port": "x"}],
          "inputs": {"x": [["multiply", "x"]], "y": [["multiply", "y"]], "z": [["add", "y"]]},
          "outputs": {"result": {"task": "add", "port": "result"}}
        }

:py:func:`~aiida.engine.processes.graphs.viz.to_mermaid` returns Mermaid flowchart source, which any Mermaid renderer draws, such as `mermaid.live <https://mermaid.live>`_.

.. dropdown:: Mermaid source for ``multiply_add``

    .. code:: text

        flowchart TD
            in__x{{x}}
            in__x -->|x| multiply
            in__y{{y}}
            in__y -->|y| multiply
            in__z{{z}}
            in__z -->|y| add
            multiply["multiply"]
            add["add"]
            multiply -->|result -> x| add
            out__result[/result/]
            add -->|result| out__result

Failures and restarts
---------------------

Tasks that depend on a failed task never start; independent tasks still run, and the graph then exits with ``ERROR_TASK_FAILED``.
The graph checkpoint records dispatched and finished tasks and loop iterations, so a restarted graph does not run finished work again.
Caching applies to tasks as to any other process.

Known limitations
-----------------

Under development
^^^^^^^^^^^^^^^^^

These are gaps in the current implementation, expected to be closed with further development:

* **Coarse error handling:** any failed task fails the graph, see `Failures and restarts`_. Error handlers, retries, partial reruns, and custom exit codes are not yet available.
* **Stored provenance only:** graphs and their tasks always store their nodes; unstored runs and unstored intermediate nodes are not supported.
* **No dry runs:** graph metadata rejects ``dry_run``.
* **No monitors yet:** ``CalcJob`` monitor mappings cannot be wired yet, since dictionary syntax only fills fixed namespaces.
* **Local function tasks:** a function task runs in the interpreter that runs the graph, on a daemon worker when submitted. Running it on a remote computer is not yet supported.
* **Serial loops:** a ``while`` runs one iteration at a time. Running a task over each item of a collection in parallel requires container data types, which are in development.
* **No per-iteration outputs:** a graph output holds one node, so a loop cannot return one result per iteration, such as the trajectory of each relaxation step. A task can copy the values into one list node, without links to the original nodes. Container data types, in development, will hold the original nodes in one output.
* **Flat task outputs:** function tasks cannot return nested output namespaces or ``PortModel`` annotations.
* **No value validators:** port types are checked, and ``PortModel`` fields reject pydantic validators; check values inside a task.
* **Source-only authoring:** graphs are written as Python source. A graphical editor is planned.

Design constraints
^^^^^^^^^^^^^^^^^^

These follow from how graphs work and are expected to stay:

* **Static ports:** every task and graph input and output is declared statically; a dynamic namespace is usable only after a task declares its contents, see :ref:`topics:workflows:graphs:dynamic_namespaces`. This static shape is what allows AiiDA to check the whole graph before launch.
* **Whole-port type variables:** ports hold node types, and a ``List`` or ``Dict`` node records no element types. A ``TypeVar`` therefore annotates a whole port, such as ``a: T``; one inside another annotation, such as ``list[T]``, is rejected.
* **Untyped adapted spreads:** a pydantic model or named tuple input is converted to a ``PortModel`` at declaration, but type checkers read the original class, so mypy reports ``Argument after ** must be a mapping`` for ``**bundle``. The graph runs regardless; declare a ``PortModel`` for a type-checked spread.
