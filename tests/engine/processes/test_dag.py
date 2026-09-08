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

import typing as t

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine import Dependency, GraphProcess, GraphSpec, GraphTask, MapTask, run_get_node, task
from aiida.engine.processes.dag import TASK_KINDS, TaskKind

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


def test_round_trip_records_the_task_kind():
    """Every task records what kind it is, so a reader can tell a function task from one it does not know."""
    graph = linear_graph()
    serialized = graph.to_dict()

    assert [task['kind'] for task in serialized['tasks']] == ['function', 'function']
    assert GraphSpec.from_dict(serialized) == graph


def test_rejects_an_unknown_task_kind():
    """A graph carrying a kind this version cannot run is refused, so a newer format is never half-read."""
    serialized = linear_graph().to_dict()
    serialized['tasks'][0]['kind'] = 'while'

    with pytest.raises(ValueError, match='is of kind `while`'):
        GraphSpec.from_dict(serialized)


@pytest.mark.parametrize(
    'mutate, expected',
    [
        pytest.param(lambda data: data.pop('version'), 'version `None`', id='missing'),
        pytest.param(lambda data: data.update(version='2.0'), 'version `2.0`', id='newer'),
    ],
)
def test_rejects_an_unreadable_version(mutate, expected):
    """A declaration is read only when its version is one this version of AiiDA understands."""
    serialized = linear_graph().to_dict()
    mutate(serialized)

    with pytest.raises(ValueError, match=expected):
        GraphSpec.from_dict(serialized)


def test_node_kinds_cover_the_declared_kinds():
    """Every kind the format allows can be read back, so the two cannot drift apart."""
    assert set(TASK_KINDS) == set(t.get_args(TaskKind))


def mapped_graph(collection) -> GraphSpec:
    """Return a graph adding 10 to every item of ``collection``, one process per item."""
    return GraphSpec(
        tasks=(MapTask(name='shifted', spec=add.task_spec, inputs={'x': collection, 'y': 10}, item_port='x'),),
        outputs={'total': ('shifted', 'total')},
    )


def test_map_node_round_trip():
    """A map records what it maps over, and reads back as the kind of node that fans out."""
    graph = mapped_graph([1, 2])
    serialized = graph.to_dict()

    assert serialized['tasks'][0]['kind'] == 'map'
    assert serialized['tasks'][0]['item_port'] == 'x'

    restored = GraphSpec.from_dict(serialized)

    assert restored == graph
    assert isinstance(restored.task('shifted'), MapTask)


def test_map_rejects_an_unknown_item_port():
    """A map over something that is not an input of the task is refused where the graph is declared."""
    with pytest.raises(ValueError, match='maps over `nope`'):
        GraphSpec(tasks=(MapTask(name='shifted', spec=add.task_spec, inputs={'y': 1}, item_port='nope'),))


@pytest.mark.parametrize(
    'collection, expected',
    [
        pytest.param([1, 2, 3], {'item_0': 11, 'item_1': 12, 'item_2': 13}, id='list'),
        pytest.param({'a': 1, 'b': 2}, {'a': 11, 'b': 12}, id='dict'),
    ],
)
def test_map_runs_once_per_item(collection, expected):
    """Every item gets its own process, and the results are gathered under the key of the item."""
    results, node = run_get_node(GraphProcess, dag=orm.Dict(dict=mapped_graph(collection).to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert {key: value.value for key, value in results['total'].items()} == expected

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
    assert sorted(link.link_label for link in called) == sorted(f'shifted_{key}' for key in expected)


def test_map_leaves_the_stored_graph_a_template():
    """The expansion is runtime state, so a graph that ran a map still describes the one task it declared."""
    results, node = run_get_node(GraphProcess, dag=orm.Dict(dict=mapped_graph([1, 2, 3]).to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert len(results['total']) == 3

    stored = node.inputs.dag.get_dict()

    assert [task['name'] for task in stored['tasks']] == ['shifted']
    assert stored == mapped_graph([1, 2, 3]).to_dict()


def test_map_over_an_empty_collection_runs_nothing():
    """A collection that turns out to be empty leaves the graph with nothing to run and nothing to gather."""
    _, node = run_get_node(GraphProcess, dag=orm.Dict(dict=mapped_graph([]).to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all() == []


def test_map_reports_an_unmappable_collection():
    """Mapping over something that is not a collection says so, naming the task and the port.

    What a map runs over can come from another task, so this is only known once the graph is running.
    """
    with pytest.raises(ValueError, match='has to be a list or a dictionary'):
        run_get_node(GraphProcess, dag=orm.Dict(dict=mapped_graph(7).to_dict()))


def test_map_results_cannot_be_taken_into_another_task_yet():
    """A task taking the results of a map is refused where the graph is declared, since nothing has to run first."""
    with pytest.raises(ValueError, match='runs once per item'):
        GraphSpec(
            tasks=(
                MapTask(name='shifted', spec=add.task_spec, inputs={'x': [1, 2], 'y': 10}, item_port='x'),
                GraphTask(name='after', spec=multiply.task_spec, inputs={'y': 2}),
            ),
            links=(Dependency(source='shifted', source_port='total', target='after', target_port='x'),),
            outputs={'product': ('after', 'product')},
        )


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
