###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for lowering restricted graph source to GraphSpec."""

import pytest

from aiida.engine import (
    graph_build,
    graph_source,
    task_execution,
    task_source,
)
from aiida.engine.processes.graphs.build_execution import graph as build_graph
from aiida.engine.processes.graphs.build_execution import task as build_task
from aiida.engine.processes.graphs.build_source import UnsupportedSyntax, build_from_source, graph, task
from aiida.engine.processes.graphs.display import format_graph
from aiida.engine.processes.graphs.spec import (
    BranchControl,
    GraphSpec,
    LoopControl,
    MapGraphControl,
    ProcessTask,
    SubgraphTask,
)


@task
def sum_two(x: int, y: int) -> int:
    return x + y


@task
def make_list(x: int) -> list[int]:
    return [x]


def unresolved_annotation(x: 'missing_orm.Int') -> int:  # noqa: F821 - missing import is intentional
    return x


@graph
def chain(x: int, y: int) -> int:
    first = sum_two(x=x, y=y)
    return sum_two(x=first, y=y)


@graph
def outer(x: int, y: int) -> int:
    inner = chain(x=x, y=y)
    return sum_two(x=inner, y=x)


@graph
def recursive(x: int) -> int:
    return recursive(x=x)


def not_registered(x: int) -> int:
    return x


missing = 1  # A Python global is deliberately not a graph input.


@graph
def unknown(x: int) -> int:
    return not_registered(x=x)


@graph
def arbitrary_code(x: int) -> int:
    print('this body must not run')
    return sum_two(x=x, y=1)


@graph
def unbound(x: int) -> int:
    return sum_two(x=x, y=missing)


@graph
def bad_assignment(x: int) -> int:
    a = 0
    return sum_two(x=x, y=a)


@task
def positive(x: int) -> bool:
    return x > 0


@task
def decrement(x: int) -> int:
    return x - 1


@graph
def choose(x: int, flag: bool) -> int:
    if flag:
        selected = sum_two(x=x, y=1)
    else:
        selected = sum_two(x=x, y=2)
    return sum_two(x=selected, y=x)


@graph
def count(x: int, keep_going: bool) -> int:
    while keep_going:
        x = decrement(x=x)
        keep_going = positive(x=x)
    return x


@graph
def transform(values: list[int], y: int) -> list[int]:
    for value in values:
        result = sum_two(x=value, y=y)
    return result


@graph
def missing_else(x: int, flag: bool) -> int:
    if flag:
        chosen = sum_two(x=x, y=1)
    return chosen


@graph
def unchanged_condition(x: int, flag: bool) -> int:
    while flag:
        x = decrement(x=x)
    return x


@graph
def unsupported_iteration(values: list[int]) -> int:
    for value in values:
        result = decrement(x=value)
        result = decrement(x=result)
    return result


def test_control_flow_rejections():
    for function, reason in (
        (missing_else, 'if requires one assignment'),
        (unchanged_condition, 'while body must update'),
        (unsupported_iteration, 'for requires a single item'),
    ):
        with pytest.raises(UnsupportedSyntax, match=reason):
            build_from_source(function)


def test_control_flow_specs():
    chosen = build_from_source(choose)
    branch = chosen.tasks[0]
    assert isinstance(branch, BranchControl)
    assert branch.otherwise is not None
    assert branch.body.outputs.keys() == branch.otherwise.outputs.keys()
    assert chosen.dependencies[0].source == branch.name

    counted = build_from_source(count)
    loop = counted.tasks[0]
    assert isinstance(loop, LoopControl)
    assert loop.condition_port == 'keep_going'
    assert set(loop.body.outputs) == {'x', 'keep_going'}
    assert counted.outputs['x'].task == loop.name

    mapped = build_from_source(transform)
    each = mapped.tasks[0]
    assert isinstance(each, MapGraphControl)
    assert each.item_port == 'value'
    assert mapped.inputs['values'] == ((each.name, 'value'),)
    for spec in (chosen, counted, mapped):
        assert GraphSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_format_graph_shows_wiring_and_nested_control_flow():
    chain_view = format_graph(build_from_source(chain))
    assert 'graph chain(x, y):' in chain_view
    assert 'sum_two_2 [process sum_two](x=sum_two.result, y=y)' in chain_view
    assert 'return result=sum_two_2.result' in chain_view

    branch_view = format_graph(build_from_source(choose))
    assert 'branch_1 [branch on condition](condition=flag, x=x)' in branch_view
    assert 'then:' in branch_view and 'otherwise:' in branch_view
    assert 'y=1' in branch_view and 'y=2' in branch_view

    loop_view = format_graph(build_from_source(count))
    assert 'loop_1 [loop while keep_going]' in loop_view
    assert 'return x=loop_1.x' in loop_view

    map_view = format_graph(build_from_source(transform))
    assert 'each_1 [map over value](value=values, y=y)' in map_view
    assert 'return result=each_1.result' in map_view


def test_graph_decorators_are_exported_with_explicit_names():
    assert graph_build is build_graph
    assert graph_source is graph
    assert task_execution is build_task
    assert task_source is task


def test_source_task_rejects_unresolved_annotations_at_registration():
    with pytest.raises(TypeError, match=r'task `unresolved_annotation`.*missing_orm') as error:
        task(unresolved_annotation)
    assert isinstance(error.value.__cause__, NameError)


def test_list_annotation_declares_one_output():
    assert tuple(make_list.task_spec.outputs) == ('result',)


def test_wires_tasks_without_running_graph_body():
    spec = build_from_source(chain)
    assert isinstance(spec, GraphSpec)
    assert [item.name for item in spec.tasks] == ['sum_two', 'sum_two_2']
    assert all(isinstance(item, ProcessTask) for item in spec.tasks)
    assert [(edge.source, edge.source_port, edge.target, edge.target_port) for edge in spec.dependencies] == [
        ('sum_two', 'result', 'sum_two_2', 'x')
    ]
    assert spec.inputs == {'x': (('sum_two', 'x'),), 'y': (('sum_two', 'y'), ('sum_two_2', 'y'))}
    assert spec.outputs['result'].task == 'sum_two_2'
    assert GraphSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_nested_graph():
    spec = build_from_source(outer)
    assert isinstance(spec.tasks[0], SubgraphTask)
    assert spec.tasks[0].body.identifier == 'chain'
    assert spec.dependencies[0].source == 'chain'


@pytest.mark.parametrize(
    ('function', 'message'),
    [
        (recursive, 'Recursive graph call'),
        (unknown, 'unregistered call'),
        (arbitrary_code, 'only single-name assignments'),
        (unbound, 'unbound name'),
        (bad_assignment, 'graph assignments must call'),
    ],
)
def test_rejects_unsupported_graphs(function, message):
    with pytest.raises(UnsupportedSyntax, match=message):
        build_from_source(function)


def test_error_points_to_original_source():
    with pytest.raises(UnsupportedSyntax) as error:
        build_from_source(bad_assignment)
    assert f'{__file__}:' in str(error.value)
    assert '        a = 0\n            ^' in str(error.value)
