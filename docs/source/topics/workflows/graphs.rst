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

A task is an ordinary Python function, marked with :func:`~aiida.engine.processes.graphs.build.task`.
It takes and returns plain Python values, and the engine stores them as nodes on the way in and on the way out:

.. include:: include/snippets/graphs/task.py
    :code: python

``outputs`` names the ports the returned values are attached to, and a returned tuple is mapped onto them in order.
Without it, the task produces one output called ``result``, unless the return annotation is a structured container, in which case each of its fields is a port.

A node holding one plain value arrives as that value, so the function is written the way it would be written without a graph around it.
Anything else arrives as the node it is, since a :class:`~aiida.orm.nodes.data.structure.StructureData` or a :class:`~aiida.orm.nodes.data.folder.FolderData` is not a value there is a plain Python spelling of.

A task can be launched on its own, with :func:`~aiida.engine.launch.run` or :func:`~aiida.engine.launch.submit`, exactly as a calculation function can.

.. _topics:workflows:graphs:tasks:containers:

Saying what a task takes and produces
-------------------------------------

A ``TypedDict``, a dataclass, a ``NamedTuple`` and a pydantic model all say the same thing in different words:
these names, of these types, some of them with a default.
That is what a namespace of ports says too, so a parameter annotated with one names a namespace whose ports are
its fields, and a returned one says which output each of its fields is:

.. include:: include/snippets/graphs/containers.py
    :code: python

The fields are ordinary ports, so a graph wires into one of them, ``relax(given={'structure': prepared.structure})``,
and the function is handed back an instance of the container it asked for.
Validation belongs to the ports, wherever the value came from, so the container is a way of saying what a namespace
holds rather than a second place where types live.
A pydantic model is the richest way to say it, since it can also say how a field is rendered for storage, which is
how a value AiiDA has no way to store is stored and read back as the type the model declares.

A function that carries no annotations, because it came from somewhere else, is described where it is placed:

.. code-block:: python

    relax = task(their_relax, inputs=RelaxInputs, outputs=RelaxOutputs)

which names the ports at the top level, one per field, since such a function takes them one by one.

.. _topics:workflows:graphs:tasks:processes:

Placing a calculation or a work chain
-------------------------------------

A process class is placed as a task as it is, wired through the ports it already declares, however deeply those are nested:

.. include:: include/snippets/graphs/process_class.py
    :code: python

This is how a graph meets the rest of AiiDA: a ``CalcJob``, a ``WorkChain``, a :class:`~aiida.calculations.shell.ShellJob` and a task written as a function are all tasks, and nothing about them has to be rewritten to be placed in one.

.. _topics:workflows:graphs:writing:

Writing a graph
===============

A graph is written as a function marked with :func:`~aiida.engine.processes.graphs.build.graph`.
Its body is traced once, so calling a task inside it records the call rather than running it, and passing what one task produced to another records that the second waits for the first:

.. include:: include/snippets/graphs/graph.py
    :code: python

The parameters of the function are the inputs of the graph, and what it returns are its outputs.
Because the body is ordinary Python, a graph is built programmatically wherever that is useful: a ``for`` loop over a list of structures places one task per structure.

.. _topics:workflows:graphs:each:

Running a task once per item
============================

:func:`~aiida.engine.processes.graphs.build.each` runs a task once for every item of a collection, whether or not the length of that collection is known before the graph runs:

.. include:: include/snippets/graphs/each.py
    :code: python

Each run is a process of its own, named after the item it was for.
What they produced arrives together at whatever takes it, which is what :class:`~aiida.engine.processes.functions.Many` declares: a parameter that takes many values at once, keyed by name.

``each`` is also written as a block, with ``with each(values) as item:``, which runs everything inside it once per item rather than only one task.

.. _topics:workflows:graphs:branches:

Choosing between two graphs
===========================

:func:`~aiida.engine.processes.graphs.build.branch` runs one of two graphs, and each side is written where it is used:

.. include:: include/snippets/graphs/branch.py
    :code: python

Both sides have to return the same outputs, since what comes after the branch takes them without knowing which side ran.
A task on the side that was not taken never runs, and neither does anything that waited for one of its outputs.

Where the choice is between two values that already exist, :func:`~aiida.engine.processes.graphs.build.select` is the cheap version: it costs one task rather than a process for each side, and returns the node it was handed rather than a copy of it.

.. _topics:workflows:graphs:loops:

Going round until a condition turns
===================================

:func:`~aiida.engine.processes.graphs.build.loop` runs a graph again and again, each run starting from what the one before it produced:

.. include:: include/snippets/graphs/loop.py
    :code: python

The state the loop carries is what the body returns, and one of those values decides whether to go round again.
That is what lets a loop be written without an edge pointing backwards, which a graph has no way to record.
``max_iterations`` bounds it, so a condition that never turns stops rather than running forever.

.. _topics:workflows:graphs:subgraphs:

Grouping tasks
==============

:func:`~aiida.engine.processes.graphs.build.subgraph` groups what is written inside it into a graph of its own, run as one task:

.. include:: include/snippets/graphs/subgraph.py
    :code: python

The graph around it waits on the whole group and takes what the group returns, rather than on each of the tasks inside it.
That is what makes the group a contract: what it takes and produces is declared, and how it does it is its own business.

.. _topics:workflows:graphs:handlers:

Recovering from a run that failed
=================================

A task can say how to recover from a run that failed, with :func:`~aiida.engine.processes.graphs.build.handler`:

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

A :func:`~aiida.engine.processes.graphs.build.monitor` is a task whose function says whether a condition is met, looked at again every ``interval`` seconds until it is, or until ``timeout`` seconds have gone by and the task fails:

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

.. warning::

    A monitor waits resident, holding one of the process slots a worker has.
    A monitor waiting on something that needs a free slot to be produced holds the slot that would produce it, and only the timeout ends that.
    Give it a ``timeout`` it should never reach rather than leaving it at a day, and prefer a condition the engine has no other way of hearing about.

A process ending is not one of those, since the engine is told when it happens.
Waiting for one the graph did not run is :func:`~aiida.engine.processes.graphs.build.wait_for`, which needs no interval and no timeout because it is woken when it happens:

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
