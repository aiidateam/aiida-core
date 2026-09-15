###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for carrying several graphs from outside the engine."""

from __future__ import annotations

from aiida.engine import (
    Dependency,
    Endpoint,
    GraphRun,
    GraphSpec,
    Orchestrated,
    ProcessTask,
    launched_as,
    run_get_node,
    task,
)


@task(outputs=['total'])
def add(x, y):
    return x + y


def linear(start: int) -> GraphSpec:
    """Return a graph of two tasks, the second taking what the first produced."""
    return GraphSpec(
        tasks=(
            ProcessTask(name='first', spec=add.task_spec, inputs={'x': start, 'y': 1}),
            ProcessTask(name='second', spec=add.task_spec, inputs={'y': 10}),
        ),
        dependencies=(Dependency(source='first', source_port='total', target='second', target_port='x'),),
        outputs={'total': Endpoint(task='second', port='total')},
    )


def carry(runs: dict[str, Orchestrated]) -> list[str]:
    """Carry several graphs to the end, a step of each in turn, and return the runs in the order they were begun.

    This is the shape of an orchestrator: ask every graph what it could start, choose between them, and only
    then let the chosen one decide. Nothing here knows what a task is, and the graphs know nothing of each
    other.
    """
    begun = []

    while able := [label for label, run in runs.items() if run.frontier()]:
        for label in able:
            run = runs[label]

            for start in run.step().starts:
                process_class, inputs = launched_as(start)
                _, node = run_get_node(process_class, **inputs)
                run.started(start.instance, node.pk)
                run.completed(start.instance, node.pk)
                begun.append(f'{label}.{start.instance}')

    return begun


def test_a_graph_run_answers_what_an_orchestrator_asks():
    """The protocol is what such a thing may lean on, so a graph run has to keep answering to it."""
    assert isinstance(GraphRun(graph=linear(1)), Orchestrated)


def test_two_graphs_are_carried_by_something_outside_the_engine():
    """The decisions are the graph's and the running is the caller's, which is what lets both graphs advance."""
    runs = {'a': GraphRun(graph=linear(1)), 'b': GraphRun(graph=linear(100))}

    begun = carry(runs)

    assert begun == ['a.first', 'b.first', 'a.second', 'b.second'], 'neither graph waited for the other to finish'
    assert runs['a'].outputs()['total'].value == 12
    assert runs['b'].outputs()['total'].value == 111
