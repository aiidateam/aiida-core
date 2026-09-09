###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the declaration of a graph of tasks."""

from __future__ import annotations

import typing as t

import pytest

from aiida.engine import (
    BranchTask,
    Dependency,
    Endpoint,
    ExecutorReference,
    GraphSpec,
    MapTask,
    ProcessTask,
    SubgraphTask,
    TaskSpec,
    task,
)
from aiida.engine.processes.graphs.spec import TASK_KINDS, TaskKind

pytestmark = pytest.mark.requires_broker


@task(outputs=['total'])
def add(x, y):
    return x + y


@task(outputs=['product'])
def multiply(x, y):
    return x * y


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


def mapped_graph(collection) -> GraphSpec:
    """Return a graph adding 10 to every item of ``collection``, one process per item."""
    return GraphSpec(
        tasks=(MapTask(name='shifted', spec=add.task_spec, inputs={'x': collection, 'y': 10}, item_port='x'),),
        outputs={'total': Endpoint(task='shifted', port='total')},
    )


def shifting_graph() -> GraphSpec:
    """Return a graph that takes one input, adds 3 to it, and returns the result."""
    return GraphSpec(
        tasks=(ProcessTask(name='sum', spec=add.task_spec, inputs={'y': 3}),),
        inputs={'start': (('sum', 'x'),)},
        outputs={'total': Endpoint(task='sum', port='total')},
    )


@task(outputs=['total', 'product'])
def sum_product(x, y):
    """Declare two named outputs and return them positionally."""
    return x + y, x * y


def test_spec_round_trip():
    """The graph is a value that can be written out and read back."""
    graph = linear_graph()
    restored = GraphSpec.from_dict(graph.to_dict())

    assert restored == graph
    assert restored.task('sum').spec.process_class is add.process_class


def test_round_trip_records_the_task_kind():
    """Every task records what kind it is, so a reader can tell a task that runs a process from one it does not know."""
    graph = linear_graph()
    serialized = graph.to_dict()

    assert [task['kind'] for task in serialized['tasks']] == ['process', 'process']
    assert GraphSpec.from_dict(serialized) == graph


def test_rejects_an_unknown_task_kind():
    """A graph carrying a kind this version cannot run is refused, so a newer format is never half-read."""
    serialized = linear_graph().to_dict()
    serialized['tasks'][0]['kind'] = 'from_a_newer_aiida'

    with pytest.raises(ValueError, match='is of kind `from_a_newer_aiida`'):
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


def test_an_output_can_pass_on_an_input():
    """An output the graph passes on comes from no task, and says so where a task name would be."""
    graph = GraphSpec(
        tasks=(ProcessTask(name='sum', spec=add.task_spec, inputs={'x': 1, 'y': 2}),),
        inputs={'echoed': (('sum', 'x'),)},
        outputs={'total': Endpoint(task='sum', port='total'), 'echo': Endpoint(task=None, port='echoed')},
    )

    assert graph.to_dict()['outputs']['echo'] == {'task': None, 'port': 'echoed'}
    assert GraphSpec.from_dict(graph.to_dict()) == graph


def test_passing_on_something_that_is_not_an_input_is_refused():
    """An output that passes on a name the graph does not take is refused where the graph is declared."""
    with pytest.raises(ValueError, match='passes on `nope`'):
        GraphSpec(
            tasks=(ProcessTask(name='sum', spec=add.task_spec, inputs={'x': 1, 'y': 2}),),
            outputs={'echo': Endpoint(task=None, port='nope')},
        )


def test_node_kinds_cover_the_declared_kinds():
    """Every kind the format allows can be read back, so the two cannot drift apart."""
    assert set(TASK_KINDS) == set(t.get_args(TaskKind))


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


def test_map_results_cannot_be_taken_into_another_task_yet():
    """A task taking the results of a map is refused where the graph is declared, since nothing has to run first."""
    with pytest.raises(ValueError, match='runs once per item'):
        GraphSpec(
            tasks=(
                MapTask(name='shifted', spec=add.task_spec, inputs={'x': [1, 2], 'y': 10}, item_port='x'),
                ProcessTask(name='after', spec=multiply.task_spec, inputs={'y': 2}),
            ),
            dependencies=(Dependency(source='shifted', source_port='total', target='after', target_port='x'),),
            outputs={'product': Endpoint(task='after', port='product')},
        )


def test_a_graph_can_be_a_task_in_another_graph():
    """A graph placed in another is a task of kind `graph`, and reads back carrying its body."""
    graph = GraphSpec(
        tasks=(
            ProcessTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
            SubgraphTask(name='inner', body=shifting_graph()),
        ),
        dependencies=(Dependency(source='start', source_port='total', target='inner', target_port='start'),),
        outputs={'total': Endpoint(task='inner', port='total')},
    )
    serialized = graph.to_dict()

    assert [task['kind'] for task in serialized['tasks']] == ['process', 'graph']

    restored = GraphSpec.from_dict(serialized)

    assert restored == graph
    assert restored.task('inner').body == shifting_graph()


@pytest.mark.parametrize(
    'edge, expected',
    [
        pytest.param(
            Dependency(source='start', source_port='total', target='inner', target_port='nope'),
            'not an input of `inner`',
            id='input',
        ),
        pytest.param(
            Dependency(source='inner', source_port='nope', target='after', target_port='x'),
            'not an output of `inner`',
            id='output',
        ),
    ],
)
def test_a_placed_graph_has_the_ports_its_body_declares(edge, expected):
    """The body says what the task takes and produces, so wiring to anything else is refused where it is declared."""
    with pytest.raises(ValueError, match=expected):
        GraphSpec(
            tasks=(
                ProcessTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
                SubgraphTask(name='inner', body=shifting_graph()),
                ProcessTask(name='after', spec=add.task_spec, inputs={'y': 1}),
            ),
            dependencies=(edge,),
        )


def test_a_task_carrying_a_body_round_trips():
    """A task that runs a graph writes its body out with it, and reads back carrying the same declaration."""
    task_ = BranchTask(name='choice', body=shifting_graph())
    graph = GraphSpec(tasks=(task_,))
    serialized = graph.to_dict()

    assert serialized['tasks'][0]['kind'] == 'branch'

    restored = GraphSpec.from_dict(serialized)

    assert restored == graph
    assert restored.task(task_.name).body == task_.body


def test_a_branch_whose_sides_produce_different_outputs_is_refused():
    """What a branch produces cannot depend on which side ran, so differing outputs are refused when declared."""
    with pytest.raises(ValueError, match='which branch ran'):
        GraphSpec(
            tasks=(
                BranchTask(
                    name='choice',
                    body=shifting_graph(),
                    otherwise=GraphSpec(
                        tasks=(ProcessTask(name='sum', spec=add.task_spec, inputs={'x': 1, 'y': 1}),),
                        outputs={'other': Endpoint(task='sum', port='total')},
                    ),
                ),
            )
        )


def test_a_branch_sharing_a_name_between_its_condition_and_a_body_input_is_refused():
    """The condition and an input of the same name would arrive on one port, so the clash is refused."""
    with pytest.raises(ValueError, match='which a branch also takes'):
        GraphSpec(tasks=(BranchTask(name='choice', body=shifting_graph(), condition_port='start'),))


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
                ProcessTask(name='same', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
                ProcessTask(name='same', spec=add.task_spec, inputs={'x': 2, 'y': 2}),
            )
        )


def test_rejects_link_to_unknown_task():
    with pytest.raises(ValueError, match='unknown task `nope`'):
        GraphSpec(
            tasks=(ProcessTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),),
            dependencies=(Dependency(source='start', source_port='total', target='nope', target_port='x'),),
        )


def test_rejects_link_to_unknown_port():
    with pytest.raises(ValueError, match='not an input of'):
        GraphSpec(
            tasks=(
                ProcessTask(name='start', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
                ProcessTask(name='sum', spec=add.task_spec),
            ),
            dependencies=(Dependency(source='start', source_port='total', target='sum', target_port='nope'),),
        )


def test_rejects_cycle():
    """A cycle would leave every task waiting, so the graph is refused when it is declared."""
    with pytest.raises(ValueError, match='contain a cycle'):
        GraphSpec(
            tasks=(
                ProcessTask(name='first', spec=add.task_spec, inputs={'y': 1}),
                ProcessTask(name='second', spec=add.task_spec, inputs={'y': 1}),
            ),
            dependencies=(
                Dependency(source='first', source_port='total', target='second', target_port='x'),
                Dependency(source='second', source_port='total', target='first', target_port='x'),
            ),
        )


def test_task_spec_declares_ports():
    """The decorator produces a declaration of the task, not just a callable."""
    spec = sum_product.task_spec

    assert spec.identifier == 'sum_product'
    assert spec.process_class is sum_product.process_class
    assert set(spec.inputs.keys()) >= {'x', 'y'}
    assert list(spec.outputs.keys()) == ['total', 'product']


def test_task_spec_round_trip():
    """The declaration is a value that can be written out and read back."""
    spec = sum_product.task_spec
    restored = TaskSpec.from_dict(spec.to_dict())

    assert restored == spec
    assert restored.process_class is sum_product.process_class
    assert list(restored.outputs.keys()) == ['total', 'product']


def test_executor_reference_resolves_process_class():
    """A process function is referenced by its importable name, and resolves back to its process class."""
    reference = sum_product.task_spec.executor

    assert reference.module == __name__
    assert reference.name == 'sum_product'
    assert reference.load() is sum_product.process_class


def test_a_task_that_was_never_declared_here_says_so():
    """A task that neither imports nor was declared in this interpreter reports what to do about it."""
    reference = ExecutorReference(module='a_module_that_cannot_be_imported', name='never_declared')

    with pytest.raises(ImportError, match='define it in a module that can be imported'):
        reference.load()
