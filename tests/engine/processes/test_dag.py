###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the declaration and execution of a graph of tasks."""

from __future__ import annotations

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine import Dependency, GraphProcess, GraphSpec, GraphTask, run_get_node, task

pytestmark = pytest.mark.requires_broker


@task(outputs=['total'])
def add(x, y):
    return x + y


@task(outputs=['product'])
def multiply(x, y):
    return x * y


@task
def boom():
    raise ValueError('this task always fails')


def linear_graph() -> GraphSpec:
    """Return ``add(add(1, 1), 3)``, so the second task waits on the first."""
    return GraphSpec(
        tasks=(
            GraphTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
            GraphTask(name='sum', spec=add.task_spec, inputs={'y': 3}),
        ),
        links=(Dependency(source='start', source_port='total', target='sum', target_port='x'),),
        outputs={'total': ('sum', 'total')},
    )


def test_spec_round_trip():
    """The graph is a value that can be written out and read back."""
    graph = linear_graph()
    restored = GraphSpec.from_dict(graph.to_dict())

    assert restored == graph
    assert restored.task('sum').spec.process_class is add.process_class


def test_ready_returns_the_frontier():
    """Only tasks whose predecessors have finished, and that were not dispatched, are ready."""
    graph = linear_graph()

    assert graph.ready(done=set(), dispatched=set()) == ['start']
    assert graph.ready(done=set(), dispatched={'start'}) == []
    assert graph.ready(done={'start'}, dispatched={'start'}) == ['sum']
    assert graph.ready(done={'start', 'sum'}, dispatched={'start', 'sum'}) == []


def test_rejects_duplicate_task_names():
    with pytest.raises(ValueError, match='task names have to be unique'):
        GraphSpec(
            tasks=(
                GraphTask(name='same', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
                GraphTask(name='same', spec=add.task_spec, inputs={'x': 2, 'y': 2}),
            )
        )


def test_rejects_link_to_unknown_task():
    with pytest.raises(ValueError, match='unknown task `nope`'):
        GraphSpec(
            tasks=(GraphTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),),
            links=(Dependency(source='start', source_port='total', target='nope', target_port='x'),),
        )


def test_rejects_link_to_unknown_port():
    with pytest.raises(ValueError, match='not a valid inputs'):
        GraphSpec(
            tasks=(
                GraphTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
                GraphTask(name='sum', spec=add.task_spec),
            ),
            links=(Dependency(source='start', source_port='total', target='sum', target_port='nope'),),
        )


def test_rejects_cycle():
    """A cycle would leave every task waiting, so the graph is refused when it is declared."""
    with pytest.raises(ValueError, match='contain a cycle'):
        GraphSpec(
            tasks=(
                GraphTask(name='first', spec=add.task_spec, inputs={'y': 1}),
                GraphTask(name='second', spec=add.task_spec, inputs={'y': 1}),
            ),
            links=(
                Dependency(source='first', source_port='total', target='second', target_port='x'),
                Dependency(source='second', source_port='total', target='first', target_port='x'),
            ),
        )


def test_runs_a_linear_graph():
    """Each task runs once its input is available, and the declared graph output is returned."""
    results, node = run_get_node(GraphProcess, dag=orm.Dict(dict=linear_graph().to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5


def test_tasks_are_called_under_their_graph_names():
    """Every task is a child process in its own right, recorded under the name the graph gave it."""
    _, node = run_get_node(GraphProcess, dag=orm.Dict(dict=linear_graph().to_dict()))

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()

    assert sorted(entry.link_label for entry in called) == ['start', 'sum']
    assert all(isinstance(entry.node, orm.CalcFunctionNode) for entry in called)


def test_runs_a_diamond_graph():
    """Two tasks that only depend on the first are both dispatched, and their outputs join in the last."""
    graph = GraphSpec(
        tasks=(
            GraphTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
            GraphTask(name='left', spec=add.task_spec, inputs={'y': 1}),
            GraphTask(name='right', spec=multiply.task_spec, inputs={'y': 3}),
            GraphTask(name='join', spec=add.task_spec),
        ),
        links=(
            Dependency(source='start', source_port='total', target='left', target_port='x'),
            Dependency(source='start', source_port='total', target='right', target_port='x'),
            Dependency(source='left', source_port='total', target='join', target_port='x'),
            Dependency(source='right', source_port='product', target='join', target_port='y'),
        ),
        outputs={'total': ('join', 'total')},
    )

    results, node = run_get_node(GraphProcess, dag=orm.Dict(dict=graph.to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 9  # (2 + 1) + (2 * 3)


def test_reports_a_failing_task():
    """A task that does not finish well stops the graph and names the task that failed."""
    graph = GraphSpec(tasks=(GraphTask(name='doomed', spec=boom.task_spec),))

    _, node = run_get_node(GraphProcess, dag=orm.Dict(dict=graph.to_dict()))

    assert not node.is_finished_ok
    assert node.exit_status == GraphProcess.exit_codes.ERROR_TASK_FAILED.status
    assert 'doomed' in node.exit_message


def test_a_failing_task_stops_what_depends_on_it():
    """A task downstream of a failure is never dispatched, since its inputs will never exist."""
    graph = GraphSpec(
        tasks=(
            GraphTask(name='doomed', spec=boom.task_spec),
            GraphTask(name='after', spec=add.task_spec, inputs={'y': 1}),
        ),
        links=(Dependency(source='doomed', source_port='result', target='after', target_port='x'),),
    )

    _, node = run_get_node(GraphProcess, dag=orm.Dict(dict=graph.to_dict()))

    assert not node.is_finished_ok
    assert node.exit_status == GraphProcess.exit_codes.ERROR_TASK_FAILED.status
    assert 'doomed' in node.exit_message

    called = {entry.link_label for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()}
    assert called == {'doomed'}
