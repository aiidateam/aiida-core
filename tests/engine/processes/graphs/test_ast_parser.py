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

from aiida.engine import UnsupportedSyntax, lower_to_graph_spec, parse_graph
from aiida.engine.processes.graphs.lower import graph, task
from aiida.engine.processes.graphs.spec import BranchTask, GraphSpec, LoopTask, MapGraphTask, ProcessTask, SubgraphTask


@task
def sum_two(x: int, y: int) -> int:
    return x + y


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
            parse_graph(function)


def test_control_flow_specs():
    chosen = parse_graph(choose)
    branch = chosen.tasks[0]
    assert isinstance(branch, BranchTask)
    assert branch.otherwise is not None
    assert branch.body.outputs.keys() == branch.otherwise.outputs.keys()
    assert chosen.dependencies[0].source == branch.name

    counted = parse_graph(count)
    loop = counted.tasks[0]
    assert isinstance(loop, LoopTask)
    assert loop.condition_port == 'keep_going'
    assert set(loop.body.outputs) == {'x', 'keep_going'}
    assert counted.outputs['x'].task == loop.name

    mapped = parse_graph(transform)
    each = mapped.tasks[0]
    assert isinstance(each, MapGraphTask)
    assert each.item_port == 'value'
    assert mapped.inputs['values'] == ((each.name, 'value'),)
    for spec in (chosen, counted, mapped):
        assert GraphSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_wires_tasks_without_running_graph_body():
    spec = lower_to_graph_spec(chain)
    assert isinstance(spec, GraphSpec)
    assert spec == parse_graph(chain)
    assert [item.name for item in spec.tasks] == ['sum_two', 'sum_two_2']
    assert all(isinstance(item, ProcessTask) for item in spec.tasks)
    assert [(edge.source, edge.source_port, edge.target, edge.target_port) for edge in spec.dependencies] == [
        ('sum_two', 'result', 'sum_two_2', 'x')
    ]
    assert spec.inputs == {'x': (('sum_two', 'x'),), 'y': (('sum_two', 'y'), ('sum_two_2', 'y'))}
    assert spec.outputs['result'].task == 'sum_two_2'
    assert GraphSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_nested_graph():
    spec = parse_graph(outer)
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
        parse_graph(function)


def test_error_points_to_original_source():
    with pytest.raises(UnsupportedSyntax) as error:
        parse_graph(bad_assignment)
    assert f'{__file__}:' in str(error.value)
    assert '        a = 0\n            ^' in str(error.value)
