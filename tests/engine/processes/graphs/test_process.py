###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for running a graph of tasks on the process state machine."""

from __future__ import annotations

from typing import TypedDict

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine import (
    Dependency,
    Endpoint,
    GraphProcess,
    GraphSpec,
    MapTask,
    ProcessTask,
    SubgraphTask,
    ToContext,
    WorkChain,
    run_get_node,
    submit,
    task,
)

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
            ProcessTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
            ProcessTask(name='sum', spec=add.task_spec, inputs={'y': 3}),
        ),
        dependencies=(Dependency(source='start', source_port='total', target='sum', target_port='x'),),
        outputs={'total': Endpoint(task='sum', port='total')},
    )


def nested_graph() -> GraphSpec:
    """Return a graph that adds 3 to what its first task produced, in a graph of its own."""
    body = GraphSpec(
        tasks=(ProcessTask(name='sum', spec=add.task_spec, inputs={'y': 3}),),
        inputs={'start': (('sum', 'x'),)},
        outputs={'total': Endpoint(task='sum', port='total')},
    )
    return GraphSpec(
        tasks=(
            ProcessTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
            SubgraphTask(name='inner', body=body),
        ),
        dependencies=(Dependency(source='start', source_port='total', target='inner', target_port='start'),),
        outputs={'total': Endpoint(task='inner', port='total')},
    )


def mapped_graph(collection) -> GraphSpec:
    """Return a graph adding 10 to every item of ``collection``, one process per item."""
    return GraphSpec(
        tasks=(MapTask(name='shifted', spec=add.task_spec, inputs={'x': collection, 'y': 10}, item_port='x'),),
        outputs={'total': Endpoint(task='shifted', port='total')},
    )


@task
def count(items):
    """Take and return plain Python values."""
    return len(items)


@task(outputs=['total', 'product'])
def sum_product(x, y):
    """Declare two named outputs and return them positionally."""
    return x + y, x * y


class Stats(TypedDict):
    """Return annotation declaring one output socket per field."""

    minimum: int
    maximum: int


@task
def stats(items) -> Stats:
    return {'minimum': min(items), 'maximum': max(items)}


@task(outputs=['first', 'second'])
def wrong_arity(x):
    """Return fewer values than the declared outputs."""
    return x


def _written_in_a_script(x, y):
    """Stand in for a task defined where it cannot be imported, as in a script or a notebook."""
    return x + y


_written_in_a_script.__module__ = 'a_module_that_cannot_be_imported'


scripted = task(outputs=['total'])(_written_in_a_script)


def test_runs_a_linear_graph():
    """Each task runs once its input is available, and the declared graph output is returned."""
    results, node = run_get_node(GraphProcess, graph=orm.Dict(dict=linear_graph().to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5


def test_tasks_are_called_under_their_graph_names():
    """Every task is a child process in its own right, recorded under the name the graph gave it."""
    _, node = run_get_node(GraphProcess, graph=orm.Dict(dict=linear_graph().to_dict()))

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()

    assert sorted(entry.link_label for entry in called) == ['start', 'sum']
    assert all(isinstance(entry.node, orm.CalcFunctionNode) for entry in called)


def test_runs_a_diamond_graph():
    """Two tasks that only depend on the first are both dispatched, and their outputs join in the last."""
    graph = GraphSpec(
        tasks=(
            ProcessTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
            ProcessTask(name='left', spec=add.task_spec, inputs={'y': 1}),
            ProcessTask(name='right', spec=multiply.task_spec, inputs={'y': 3}),
            ProcessTask(name='join', spec=add.task_spec),
        ),
        dependencies=(
            Dependency(source='start', source_port='total', target='left', target_port='x'),
            Dependency(source='start', source_port='total', target='right', target_port='x'),
            Dependency(source='left', source_port='total', target='join', target_port='x'),
            Dependency(source='right', source_port='product', target='join', target_port='y'),
        ),
        outputs={'total': Endpoint(task='join', port='total')},
    )

    results, node = run_get_node(GraphProcess, graph=orm.Dict(dict=graph.to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 9  # (2 + 1) + (2 * 3)


def test_runs_a_graph_placed_in_a_graph():
    """A graph inside a graph runs as a child process of its own, producing what its body declares."""
    results, node = run_get_node(GraphProcess, graph=orm.Dict(dict=nested_graph().to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5  # (1 + 1) + 3

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()

    assert [entry.link_label for entry in called] == ['inner']
    assert isinstance(called[0].node, orm.WorkChainNode)


def test_reports_a_failing_task():
    """A task that does not finish well stops the graph and names the task that failed."""
    graph = GraphSpec(tasks=(ProcessTask(name='doomed', spec=boom.task_spec),))

    _, node = run_get_node(GraphProcess, graph=orm.Dict(dict=graph.to_dict()))

    assert not node.is_finished_ok
    assert node.exit_status == GraphProcess.exit_codes.ERROR_TASK_FAILED.status
    assert 'doomed' in node.exit_message


def test_a_failing_task_stops_what_depends_on_it():
    """A task downstream of a failure is never dispatched, since its inputs will never exist."""
    graph = GraphSpec(
        tasks=(
            ProcessTask(name='doomed', spec=boom.task_spec),
            ProcessTask(name='after', spec=add.task_spec, inputs={'y': 1}),
        ),
        dependencies=(Dependency(source='doomed', source_port='result', target='after', target_port='x'),),
    )

    _, node = run_get_node(GraphProcess, graph=orm.Dict(dict=graph.to_dict()))

    assert not node.is_finished_ok
    assert node.exit_status == GraphProcess.exit_codes.ERROR_TASK_FAILED.status
    assert 'doomed' in node.exit_message

    called = {entry.link_label for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()}
    assert called == {'doomed'}


@pytest.mark.parametrize(
    'collection, expected',
    [
        pytest.param([1, 2, 3], {'item_0': 11, 'item_1': 12, 'item_2': 13}, id='list'),
        pytest.param({'a': 1, 'b': 2}, {'a': 11, 'b': 12}, id='dict'),
    ],
)
def test_map_runs_once_per_item(collection, expected):
    """Every item gets its own process, and the results are gathered under the key of the item."""
    results, node = run_get_node(GraphProcess, graph=orm.Dict(dict=mapped_graph(collection).to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert {key: value.value for key, value in results['total'].items()} == expected

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
    assert sorted(link.link_label for link in called) == sorted(f'shifted_{key}' for key in expected)


def test_map_leaves_the_stored_graph_a_template():
    """The expansion is runtime state, so a graph that ran a map still describes the one task it declared."""
    results, node = run_get_node(GraphProcess, graph=orm.Dict(dict=mapped_graph([1, 2, 3]).to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert len(results['total']) == 3

    stored = node.inputs.graph.get_dict()

    assert [task['name'] for task in stored['tasks']] == ['shifted']
    assert stored == mapped_graph([1, 2, 3]).to_dict()


def test_map_over_an_empty_collection_runs_nothing():
    """A collection that turns out to be empty leaves the graph with nothing to run and nothing to gather."""
    _, node = run_get_node(GraphProcess, graph=orm.Dict(dict=mapped_graph([]).to_dict()))

    assert node.is_finished_ok, node.exit_message
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all() == []


def test_map_reports_an_unmappable_collection():
    """Mapping over something that is not a collection says so, naming the task and the port.

    What a map runs over can come from another task, so this is only known once the graph is running.
    """
    with pytest.raises(ValueError, match='has to be a list or a dictionary'):
        run_get_node(GraphProcess, graph=orm.Dict(dict=mapped_graph(7).to_dict()))


def test_plain_python_values():
    """A task takes and returns plain Python values, stored as the corresponding data nodes."""
    result, node = run_get_node(count, items=[1, 2, 3])

    assert node.is_finished_ok, node.exit_message
    assert isinstance(result, orm.Int)
    assert result == 3


def test_declared_outputs_from_kwarg():
    """``outputs=`` declares named output ports, onto which a returned tuple is mapped in order."""
    results, node = run_get_node(sum_product, x=2, y=3)

    assert node.is_finished_ok, node.exit_message
    assert set(results) == {'total', 'product'}
    assert results['total'] == 5
    assert results['product'] == 6


def test_declared_outputs_from_return_annotation():
    """A ``TypedDict`` return annotation declares one output port per field."""
    assert list(stats.task_spec.outputs.keys()) == ['minimum', 'maximum']

    results, node = run_get_node(stats, items=[3, 1, 2])

    assert node.is_finished_ok, node.exit_message
    assert results['minimum'] == 1
    assert results['maximum'] == 3


def test_returned_values_must_match_declared_outputs():
    """Returning a different number of values than declared outputs is reported, not silently dropped."""
    with pytest.raises(ValueError, match='declares 2 outputs'):
        run_get_node(wrong_arity, x=1)


def test_a_task_that_cannot_be_imported_still_runs_where_it_was_defined():
    """A task written in a script has no importable name, and runs in the session that declared it."""
    assert scripted.task_spec.executor.module == 'a_module_that_cannot_be_imported'
    assert scripted.task_spec.executor.load() is scripted.process_class

    results, node = run_get_node(scripted, x=2, y=3)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5


def test_submit_standalone():
    """A task can be submitted on its own."""
    node = submit(count, items=[1, 2, 3])

    assert isinstance(node, orm.CalcFunctionNode)


def test_submit_from_process():
    """A running workflow dispatches a task as a called child, under the name it gives it."""

    class ParentWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.outline(cls.submit_child, cls.collect)
            spec.outputs.dynamic = True

        def submit_child(self):
            child = self.submit(sum_product, x=2, y=3, metadata={'call_link_label': 'arithmetic'})
            return ToContext(arithmetic=child)

        def collect(self):
            self.out('total', self.ctx.arithmetic.outputs.total)

    results, node = run_get_node(ParentWorkChain)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5
