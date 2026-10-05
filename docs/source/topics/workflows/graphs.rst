.. _topics:workflows:graphs:

======
Graphs
======

A graph is a third way of writing a workflow, beside :ref:`work functions <topics:workflows:usage:workfunctions>` and :ref:`work chains <topics:workflows:usage:workchains>`.
Where a work chain is a class whose outline says what to do step by step, a graph is a *declaration*: it records which tasks to run and which output of one feeds which input of another, and the engine works out what can run when.

That difference is what a graph is for.
The declaration is a value rather than code, so it is stored with the run, can be read before anything has started, and is the same for every run of the same workflow.
Every task in it is a process of its own, so each one has its own node, its own entry in the provenance graph, and is paused, played and killed the way any other process is.

.. _topics:workflows:graphs:tasks:

Tasks
=====

A task is an ordinary Python function, marked with :func:`~aiida.engine.task_source`.
The top-level ``aiida.engine.task`` decorator also selects the source flavour.
It takes and returns plain Python values, and the engine stores them as nodes on the way in and on the way out:

.. include:: include/snippets/graphs/task.py
    :code: python

The return annotation declares the output type.
A scalar result is stored on the ``result`` output port.
An ordinary dictionary is stored as one ``Dict`` node, even without a return annotation; its keys never become output ports.
A ``PortModel`` return annotation declares named and nested outputs, which the task must populate by returning model instances rather than dictionaries.

A node holding one plain value arrives as that value, so the function is written the way it would be written without a graph around it.
Anything else arrives as the node it is, since a :class:`~aiida.orm.nodes.data.structure.StructureData` or a :class:`~aiida.orm.nodes.data.folder.FolderData` is not a value there is a plain Python spelling of.

A task can be launched on its own, with :func:`~aiida.engine.launch.run` or :func:`~aiida.engine.launch.submit`, exactly as a calculation function can.

.. _topics:workflows:graphs:tasks:structured:

Saying what a task takes and produces
-------------------------------------

A :class:`~aiida.engine.PortModel` declares a namespace using annotated fields and defaults.
Its fields become ordinary AiiDA ports, and nested models become nested namespaces.
Use :class:`~aiida.engine.PortField` inside ``Annotated`` to attach configuration help.
A field without a default is required; a field with a default can be omitted.

.. include:: include/snippets/graphs/structured.py
    :code: python

``PortModel`` is declaration syntax, not a runtime validation model.
Inside the task, ``given`` is an :class:`~aiida.common.extendeddicts.AttributesFrozendict`, supporting both ``given.steps`` and ``given['steps']``.
This is the same namespace-value representation used by WorkChain inputs, except tasks unwrap scalar nodes when their annotations request Python values.
An annotation naming an ORM node type preserves the node itself.
The engine does not reconstruct a ``PortModel`` instance or run its constructor during validation or task execution.

Supply mappings or model instances as inputs at launch; input namespaces are stored as individually linked data-node leaves, not as container nodes.
For task output namespaces, return a ``PortModel`` instance, including model instances for nested namespaces.
A dictionary-valued field remains one ``Dict`` node rather than a namespace.
To produce a keyed collection with runtime-defined names, annotate an output field as ``Many[T]``:

.. code-block:: python

    from aiida import orm
    from aiida.engine import Many, PortModel, task

    class Prepared(PortModel):
        values: Many[orm.Int]

    @task
    def prepare_values() -> Prepared:
        return Prepared(values={'a': orm.Int(1), 'b': orm.Int(2)})

``values`` declares a dynamic namespace with leaves of type ``T``.
Return a mapping for this field; each leaf has its own output link, and keys must be valid AiiDA port names.
The namespace can be wired as a whole to a task input namespace, including when the mapping is empty.
Tasks retain calculation-function provenance rules: returning already stored nodes is not allowed.
Use a workflow to return existing nodes rather than copying them or bypassing provenance validation.

Opaque objects should be declared as ORM nodes such as :class:`~aiida.orm.Dict` or :class:`~aiida.orm.JsonableData`.
Arbitrary dataclasses, ``TypedDict``, ``NamedTuple`` and Pydantic models do not declare namespaces.

Source graph bodies can pass a namespace as a whole, as in ``relax(given=given)``, or populate a declared input namespace with a dictionary of literals and references, as in ``relax(given={'structure': produced.structure})``.
Dictionary-valued ports are leaves: a literal dictionary replaces the whole value, and symbolic references must supply the whole port rather than its individual dictionary entries.
Selecting ``given.structure`` or ``given['structure']`` from a graph input inside the body is not supported; select such fields inside registered tasks instead.

A function that carries no annotations, because it came from somewhere else, is described where it is placed:

.. code-block:: python

    from aiida.engine import task_execution

    relax = task_execution(their_relax, inputs=RelaxInputs, outputs=RelaxOutputs)

This explicit execution-flavour adapter names top-level ports for an unannotated function.
The source flavour instead reads the task function's annotations.

.. _topics:workflows:graphs:tasks:processes:

Placing a calculation or a work chain
-------------------------------------

Use :func:`~aiida.engine.task_from_calcjob` or :func:`~aiida.engine.task_from_workchain` to place an existing process class as a task in either a source or an execution graph.
These helpers use the process's existing inputs and outputs, including nested namespaces, defaults and requiredness, without capturing its source or executing its implementation while building the graph.
For example, ``relax = task_from_workchain(RelaxWorkChain)`` creates a handle that can be called inside either graph flavour, including through a local or imported alias.
When the graph runs, the original process runs as its child with normal provenance.
The existing ``task_execution(ProcessClass)`` adapter remains supported.
The following example uses the explicit registration helper with execution-flavour decorators:

.. include:: include/snippets/graphs/process_class.py
    :code: python

This is how a graph meets the rest of AiiDA: a ``CalcJob``, a ``WorkChain``, a :class:`~aiida.calculations.shell.ShellJob` and a task written as a function are all tasks, and nothing about them has to be rewritten to be placed in one.

Prepared process builders
-------------------------

Use :func:`~aiida.engine.task_from_builder` when an upstream plugin has already prepared a ``ProcessBuilder``.
Call ``get_builder_from_protocol`` in ordinary Python, with concrete arguments, before graph launch.
Preparation is not a calculation task: selected stored pseudos become ordinary inputs of the child process, not outputs of a preparation calculation.
The adapter snapshots containers without cloning ORM nodes and preserves the upstream process ports.
An incomplete builder is allowed; placement or graph launch can supply missing required inputs.

For a source graph, register ordinary process handles at module scope, then bind prepared handles by their placement names using :meth:`~aiida.engine.processes.graphs.interface.GraphHandle.bind_tasks`:

.. code-block:: python

    from aiida.engine import graph_source, submit, task_from_builder, task_from_workchain
    from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain

    pw = task_from_workchain(PwBaseWorkChain)

    @graph_source
    def scf_nscf():
        scf = pw()
        nscf = pw(pw={'parent_folder': scf.remote_folder})
        return nscf.remote_folder

    # Outside the graph body, with concrete code and structure:
    scf_builder = PwBaseWorkChain.get_builder_from_protocol(
        code=code, structure=structure, overrides=scf_overrides,
    )
    nscf_builder = PwBaseWorkChain.get_builder_from_protocol(
        code=code, structure=structure, overrides=nscf_overrides,
    )
    scf_builder.clean_workdir = False
    nscf_builder.clean_workdir = False
    launch = scf_nscf.bind_tasks(
        pw=task_from_builder(scf_builder),
        pw_2=task_from_builder(nscf_builder),
    )
    node = submit(launch)

Binding keys are declaration placement names (``pw``, then ``pw_2`` for repeated calls), not assignment-variable names.
The returned graph handle is independent; neither the original graph nor a shared registered task is mutated.
Execution graphs can also place a prepared handle directly, including a handle captured by a local graph function.

Explicit placement leaves replace bound leaves; unrelated leaves in the same namespace remain.
Replacing ``pw.parameters`` replaces that whole port rather than merging namelists.
Optional omissions, upstream defaults, labels and scheduler options retain their upstream semantics.
Metadata is checkpointed separately and does not become database input links.
Final validation combines prepared values, launch values and checked task-output references; missing required ports retain structural error records and port help.

The declaration contains private boundary routes, never builders or bound node identities.
Carry the full mapping returned by ``launch.get_launch_inputs()`` alongside a round-tripped declaration when submitting ``GraphProcess`` directly; the mapping contains the scientific inputs and separate non-database bindings needed by a fresh worker.
Preparation itself has no process node, and protocol choice is not automatically recorded as a graph input.

Replacing a prepared input does not rerun the protocol builder.
In particular, changing a structure can invalidate selected pseudos, cutoffs or other derived choices; prepare again when those dependencies change.
A structure produced by an upstream task cannot be inspected by submission-time protocol preparation: use a workflow that prepares and launches the process at runtime instead.
For remote-folder chains, disable upstream work-directory cleanup explicitly; the adapter never changes ``clean_workdir`` itself.

.. _topics:workflows:graphs:writing:

Writing a graph
===============

A source graph is written as a function marked with :func:`~aiida.engine.graph_source`.
The top-level ``aiida.engine.graph`` decorator also selects this flavour.
Its source is parsed without executing the graph body.
Calling a registered task records a dependency rather than running that task:

.. include:: include/snippets/graphs/graph.py
    :code: python

The parameters of the function are the inputs of the graph, and what it returns are its outputs.
Named and nested graph outputs must be declared by a ``PortModel`` return annotation.
Return a model instance containing task-output or graph-input references, or forward an already-declared namespace with the same fields.
Raw dictionary returns are rejected, including when the graph has a ``PortModel`` annotation: dictionary shape never declares a graph namespace.
A scalar return remains a single output; a task annotated with ``dict`` produces one dictionary-valued output, not one output per key.
For example:

.. code-block:: python

    from aiida.engine import PortModel, graph_source

    class Results(PortModel):
        total: int

    @graph_source
    def named_sum(x: int, y: int) -> Results:
        result = add(x=x, y=y)
        return Results(total=result)

Only the supported source syntax described below is accepted; ordinary Python expressions are not executed while building the graph.
Independent task calls are not forced to execute in source order.
:meth:`~aiida.engine.processes.graphs.spec.GraphSpec.unread` reports tasks whose outputs are not consumed.

Building a restricted graph from source
---------------------------------------

For graphs with only single-output tasks and straightforward data dependencies,
:func:`~aiida.engine.processes.graphs.build_source.build_from_source` builds a :class:`~aiida.engine.processes.graphs.spec.GraphSpec`
from the source code without executing the graph function:

.. code-block:: python

    from aiida.engine import graph_source, task_source

    @task_source
    def add(x: int, y: int) -> int:
        return x + y

    @graph_source
    def add_twice(x: int, y: int) -> int:
        first = add(x=x, y=y)
        return add(x=first, y=y)

    declaration = add_twice.build()

Use the explicit ``graph_source`` and ``task_source`` names to make the authoring flavour clear.
``graph_execution`` and ``task_execution`` provide a separate execution-tracing flavour.
They capture source when a module is imported; definitions must be at module scope. The parser reads a graph's assignments and calls in source
order, resolving only tasks and graphs registered in the same module. Task
bodies are not parsed. It accepts single-name assignments to registered calls,
keyword arguments that are graph inputs, task outputs or scalar literals, and a
final return of an input or a single output. Restricted control flow is also
supported: ``if``/``else`` must assign a new name in both arms, ``while`` must
update an existing condition name with a task call (and can update other
existing state names), and ``for item in collection`` must assign one task call
per item to a new name. A ``for`` result is a collection of outputs, not a
single value. Conditions and collections must be graph inputs or task outputs;
comparisons and arithmetic belong in registered tasks. These forms lower to
branch, loop and map tasks, respectively, rather than executing Python control
flow at parse time. Other forms, including ``break``, ``continue`` and loop
``else`` blocks, are rejected with :class:`~aiida.engine.processes.graphs.build_source.UnsupportedSyntax`,
pointing at the offending source.
The result is a declaration, not a launched process.

Source graphs currently accept only ordinary positional-or-keyword parameters without defaults.
Positional-only parameters, keyword-only parameters, ``*args``, ``**kwargs`` and graph parameter defaults are rejected when building the declaration.
Defaults inside a ``PortModel`` are supported, so group defaulted configuration fields in a required namespace parameter.
An annotation allowing ``None`` does not itself make an input omittable.
Use an explicit mapping input for extra options; ``task(**symbolic_mapping)`` is not supported.
Conditions and topology must use the supported graph control flow or registered tasks, not build-time decisions based on launch values.

.. _topics:workflows:graphs:launch:

Launching and inspecting declarations
-------------------------------------

A graph handle and its :class:`~aiida.engine.processes.graphs.spec.GraphSpec` hold declarations, not bound run values.
Keep a declaration and an input mapping side by side when carrying a workflow between application layers.
:meth:`~aiida.engine.processes.graphs.process.GraphProcess.launch_inputs` prepares the values for launch; :meth:`~aiida.engine.processes.graphs.interface.GraphHandle.get_launch_inputs` also binds them to the graph signature.

.. include:: include/snippets/graphs/launch.py
    :code: python

For daemon submission, use the same inputs with :func:`~aiida.engine.launch.submit`:

.. code-block:: python

    from aiida.engine import GraphProcess, submit

    node = submit(GraphProcess, **launch_inputs, metadata={'label': 'example'})

Task definitions must be importable by the daemon worker.
Validation applies at handle launch, direct ``GraphProcess.launch_inputs`` and raw ``GraphProcess`` construction before graph provenance is stored.
Missing required inputs raise :class:`~aiida.common.exceptions.MissingRequiredInputsError`.
Its ``missing`` tuple contains immutable :class:`~aiida.common.exceptions.MissingInput` records in deterministic path order, each with ``identifier``, graph-relative ``socket_path``, ``help`` and ``required``.
A missing required namespace reports its missing leaves; an absent optional namespace does not require its children.
Wrong types, shapes and unknown inputs remain separate validation errors.
Consumers can translate the structured records into application-specific advice without parsing error messages.
On Python versions supporting exception notes, they can attach advice using ``error.add_note(...)``.

:meth:`~aiida.engine.processes.graphs.spec.GraphSpec.to_dict` and :meth:`~aiida.engine.processes.graphs.spec.GraphSpec.from_dict` preserve the versioned declaration, including boundary help, defaults and requiredness.
Snapshots contain declaration structure and importable executor/type references, not bound input values or run-state node identities.
Use ``declaration.task_names`` for the task list.
The current schema version is ``1.0``; unknown versions are rejected.
Serialization is versioned, not a promise that snapshot formatting never changes across releases.

Execution-flavour examples
==========================

The remaining examples use explicit execution-flavour decorators and controls.
They are not source-parser syntax and should not be copied into a ``graph_source`` body.

.. _topics:workflows:graphs:each:

Running a task once per item
============================

:func:`~aiida.engine.processes.graphs.build_execution.each` runs a task once for every item of a collection, whether or not the length of that collection is known before the graph runs:

.. include:: include/snippets/graphs/each.py
    :code: python

Each run is a process of its own, named after the item it was for.
What they produced arrives together at whatever takes it, which is what :class:`~aiida.engine.processes.functions.Many` declares: a parameter that takes many values at once, keyed by name.

``each`` is also written as a block, with ``with each(values) as item:``, which runs everything inside it once per item rather than only one task.

.. _topics:workflows:graphs:branches:

Choosing between two graphs
===========================

:func:`~aiida.engine.processes.graphs.build_execution.branch` runs one of two graphs, and each side is written where it is used:

.. include:: include/snippets/graphs/branch.py
    :code: python

Both sides have to return the same outputs, since what comes after the branch takes them without knowing which side ran.
A task on the side that was not taken never runs, and neither does anything that waited for one of its outputs.

Where the choice is between two values that already exist, :func:`~aiida.engine.processes.graphs.build_execution.select` is the cheap version: it costs one task rather than a process for each side, and returns the node it was handed rather than a copy of it.

.. _topics:workflows:graphs:loops:

Going round until a condition turns
===================================

:func:`~aiida.engine.processes.graphs.build_execution.loop` runs a graph again and again, each run starting from what the one before it produced:

.. include:: include/snippets/graphs/loop.py
    :code: python

The state the loop carries is what the body returns, and one of those values decides whether to go round again.
That is what lets a loop be written without an edge pointing backwards, which a graph has no way to record.
``max_iterations`` bounds it, so a condition that never turns stops rather than running forever.

.. _topics:workflows:graphs:subgraphs:

Grouping tasks
==============

:func:`~aiida.engine.processes.graphs.build_execution.subgraph` groups what is written inside it into a graph of its own, run as one task:

.. include:: include/snippets/graphs/subgraph.py
    :code: python

The graph around it waits on the whole group and takes what the group returns, rather than on each of the tasks inside it.
That is what makes the group a contract: what it takes and produces is declared, and how it does it is its own business.

.. _topics:workflows:graphs:handlers:

Recovering from a run that failed
=================================

A task can say how to recover from a run that failed, with :func:`~aiida.engine.processes.graphs.build_execution.handler`:

.. include:: include/snippets/graphs/handlers.py
    :code: python

A handler is given the node of the run that failed and the inputs the next run will be launched with, and changes those inputs to fix what went wrong.
Returning a :class:`~aiida.engine.processes.workchains.utils.ProcessHandlerReport` says the failure was handled, and ``do_break`` stops the handlers below it from being called for that run.

Such a task is run by a :class:`~aiida.engine.processes.workchains.restart.BaseRestartWorkChain` generated for it, which is what retries it and calls the handlers, so a task also takes that work chain's own inputs: ``max_iterations``, ``handler_overrides``, ``on_unhandled_failure`` and ``pause_on_max_iterations``.

Where the handling grows past what a few functions say, a work chain written by hand is still the thing to reach for, and placing one as a task has always worked.

.. _topics:workflows:graphs:waiting:

Waiting for something outside the graph
=======================================

A graph waits for what it runs itself by taking its outputs.
Waiting for something else takes one of two forms, depending on whether the engine already knows about it.

A :func:`~aiida.engine.processes.graphs.build_execution.monitor` is a task whose function says whether a condition is met, looked at again every ``interval`` seconds until it is, or until ``timeout`` seconds have gone by and the task fails:

.. include:: include/snippets/graphs/monitor.py
    :code: python

``after`` is what orders a task against one it takes no value from, which is how anything waits for a monitor.

A monitor that has seen enough says so by returning :class:`~aiida.engine.processes.graphs.monitors.Stop` with the reason:

.. code-block:: python

    @monitor
    def file_is_there(path: str) -> bool | Stop:
        if Path(path).with_suffix('.failed').exists():
            return Stop('the run that produces it gave up')

        return Path(path).exists()

The monitor then ends with exit status 411, every task waiting on it is skipped, and the graph finishes with whatever else it had to do.
The reason is the exit message on the monitor's node, which is where someone reading the graph afterwards finds why that part of it did not run.

What a monitor found while looking is passed on by declaring ``outputs`` and answering with :class:`~aiida.engine.processes.graphs.monitors.Met`, so a task after it reads what it saw:

.. code-block:: python

    @monitor(outputs=['path'])
    def data_arrives(directory: str) -> Met | bool:
        found = next(Path(directory).glob('*.nc'), None)

        return Met(path=str(found)) if found else False

    @graph
    def read_what_arrives(directory):
        arrived = data_arrives(directory=directory, interval=5)
        return {'size': size_of(path=arrived.path).size}

A monitor is looked at over and over because what it watches changes, so it is never taken from the cache.

.. warning::

    A monitor waits resident, holding one of the process slots a worker has.
    A monitor waiting on something that needs a free slot to be produced holds the slot that would produce it, and only the timeout ends that.
    Give it a ``timeout`` it should never reach rather than leaving it at a day, and prefer a condition the engine has no other way of hearing about.

A process ending is not one of those, since the engine is told when it happens.
Waiting for one the graph did not run is :func:`~aiida.engine.processes.graphs.build_execution.wait_for`, which needs no interval and no timeout because it is woken when it happens:

.. code-block:: python

    @graph
    def carry_on(earlier):
        return {'total': add(x=1, y=2).after(wait_for(pk=earlier)).total}

.. _topics:workflows:graphs:inspecting:

Reaching what a graph ran
=========================

Every task is a process called under the name the graph knows it by, so :func:`~aiida.engine.processes.graphs.run.tasks` reaches one after the fact: its result, and the process to pause, play or kill:

.. include:: include/snippets/graphs/inspecting.py
    :code: python

A task inside a graph that a task ran is reached by the names on the way to it, ``tasks(node)['refine.relax']``, and one run of a fan-out by the item it was for, ``tasks(node)['add_item_2']``.

.. _topics:workflows:graphs:rerunning:

Running a graph again
---------------------

With :ref:`caching <topics:provenance:caching>` on, running a graph again takes every task from the cache, so nothing that has not changed is computed twice.
:func:`~aiida.engine.processes.graphs.run.rerun_from` says which runs the cache may no longer answer with, and what follows one of those runs again only where its own inputs change.

Naming nothing takes every task that did not finish well, at any depth, which is the case a graph that stopped is run again for.
That has to be said, because a task that failed is as valid a cache source as one that worked, so a graph run again would otherwise take the failure from the cache and stop in the same place.
