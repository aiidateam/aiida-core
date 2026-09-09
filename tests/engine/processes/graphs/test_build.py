###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for writing a graph of tasks as ordinary Python."""

from __future__ import annotations

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine import (
    BranchTask,
    Endpoint,
    MapTask,
    SubgraphTask,
    branch,
    each,
    graph,
    run_get_node,
    submit,
    task,
)

pytestmark = pytest.mark.requires_broker


@task(outputs=['total'])
def add(x, y):
    return x + y


@task(outputs=['quotient', 'remainder'])
def divide(x, y):
    return x // y, x % y


@graph
def add_twice(x, y):
    """Take the output of one task into the next."""
    first = add(x=x, y=y)
    return add(x=first.total, y=y)


@graph
def shift_all(values, by):
    """Run one task per item of a collection, which is what `each` marks."""
    return add(x=each(values), y=by)


@task(outputs=['values'])
def spread(n):
    """Produce the collection that a later task is run over."""
    return list(range(int(n)))


@graph
def shift_spread(n, by):
    made = spread(n=n)
    return add(x=each(made.values), y=by)


@graph
def shift_and_echo(x, y):
    """Return a computed output beside one of the graph's own inputs, passed on unchanged."""
    return {'total': add(x=x, y=y).total, 'echo': x}


@graph
def add_four_times(x, y):
    """Place a graph inside a graph, taking what the first produced into the second."""
    once = add_twice(x=x, y=y)
    return add_twice(x=once.total, y=y)


@graph
def doubled(x):
    """Stand in for the branch a condition selects."""
    return add(x=x, y=x)


@graph
def negated(x):
    """Return the same output as `doubled`, so the two can be the sides of one branch."""
    return add(x=x, y=0)


@graph
def maybe_double(x, flag):
    """Run a branch that produces nothing when its condition does not hold."""
    return branch(flag, then=doubled, x=x)


@graph
def double_or_not(x, flag):
    """Run a branch that produces the same outputs whichever side is taken."""
    return branch(flag, then=doubled, otherwise=negated, x=x)


@graph
def reaches_for_an_outer_task(x, y):
    """Write an inner graph that takes a value from a task in the graph around it."""
    first = add(x=x, y=y)

    @graph
    def inner(z):
        return add(x=z, y=first.total)

    return inner(z=x)


@graph
def reaches_for_an_outer_input(x, y):
    """Write an inner graph that takes an input of the graph around it."""

    @graph
    def inner(z):
        return add(x=z, y=y)

    return inner(z=x)


def test_records_tasks_links_and_inputs():
    """The body is not executed: it declares the tasks, what feeds them, and what the graph returns."""
    declaration = add_twice.build()

    assert [node.name for node in declaration.tasks] == ['add', 'add_2']
    assert [(link.source, link.source_port, link.target, link.target_port) for link in declaration.dependencies] == [
        ('add', 'total', 'add_2', 'x')
    ]
    assert declaration.outputs == {'total': Endpoint(task='add_2', port='total')}


def test_the_declaration_holds_no_values():
    """The graph names its inputs and records where each goes, so one declaration describes every run."""
    declaration = add_twice.build()

    assert [node.inputs for node in declaration.tasks] == [{}, {}]
    assert declaration.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('add_2', 'y'))}


def test_the_same_declaration_serves_every_run():
    """Two runs with different values store the same declaration, which is what makes it a template."""
    first, first_node = run_get_node(add_twice, x=1, y=2)
    second, second_node = run_get_node(add_twice, x=10, y=20)

    assert first['total'] == 5
    assert second['total'] == 50
    assert first_node.inputs.graph.get_dict() == second_node.inputs.graph.get_dict()
    assert first_node.inputs.graph_inputs.x != second_node.inputs.graph_inputs.x


def test_runs_what_was_written():
    """Running the graph gives the result the same code would give if the tasks had simply been called."""
    results, node = run_get_node(add_twice, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5  # (1 + 2) + 2

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
    assert sorted(entry.link_label for entry in called) == ['add', 'add_2']


def test_each_places_a_task_that_fans_out():
    """Marking an input with `each` declares a task run once per item, over that input."""
    declaration = shift_all.build()
    (node,) = declaration.tasks

    assert isinstance(node, MapTask)
    assert node.item_port == 'x'
    assert declaration.inputs == {'values': (('add', 'x'),), 'by': (('add', 'y'),)}


def test_a_fan_out_runs_once_per_item():
    """Every item gets a process of its own, and the results come back under the key of the item."""
    results, node = run_get_node(shift_all, values=[1, 2, 3], by=10)

    assert node.is_finished_ok, node.exit_message
    assert {key: value.value for key, value in results['total'].items()} == {
        'item_0': 11,
        'item_1': 12,
        'item_2': 13,
    }


def test_a_fan_out_can_take_its_collection_from_a_task():
    """How many items there are can depend on what another task produced, so it is only known while running."""
    declaration = shift_spread.build()

    assert isinstance(declaration.task('add'), MapTask)
    assert [(link.source, link.source_port, link.target, link.target_port) for link in declaration.dependencies] == [
        ('spread', 'values', 'add', 'x')
    ]

    results, node = run_get_node(shift_spread, n=3, by=100)

    assert node.is_finished_ok, node.exit_message
    assert {key: value.value for key, value in results['total'].items()} == {
        'item_0': 100,
        'item_1': 101,
        'item_2': 102,
    }


def test_a_fan_out_result_passed_to_a_task_is_refused_where_it_is_written():
    """A result per item handed to a task that takes one value fails at the call that wrote it.

    What a fan-out returns carries that it is per item, so this is caught while the graph is being written
    rather than when the finished declaration is validated.
    """

    @graph
    def reduce_it(values):
        mapped = add(x=each(values), y=1)
        return add(x=mapped.total, y=2)

    with pytest.raises(ValueError, match='runs once per item'):
        reduce_it.build()


def test_an_output_inside_a_container_is_refused():
    """An output buried in a container would be stored as a value, leaving the task it comes from unwaited for."""

    @graph
    def buried(x, y):
        first = divide(x=x, y=y)
        return add(x=each([first.quotient, first.remainder]), y=100)

    with pytest.raises(ValueError, match='inside a list'):
        buried.build()


def test_only_one_input_can_be_mapped_over():
    """A task runs over one of its inputs, so marking two says which choice has to be made."""

    @graph
    def two_at_once(values, others):
        return add(x=each(values), y=each(others))

    with pytest.raises(ValueError, match='runs once per item of'):
        two_at_once.build()


def test_a_task_used_twice_keeps_the_uses_apart():
    """The second use of a task gets its own name, so both are addressable."""
    declaration = add_twice.build()

    assert [node.name for node in declaration.tasks] == ['add', 'add_2']


def test_independent_tasks_join_again():
    """Two tasks that only depend on the first are both recorded, and their outputs meet in the last."""

    @graph
    def diamond(x):
        start = add(x=x, y=1)
        left = add(x=start.total, y=10)
        right = add(x=start.total, y=100)
        return add(x=left.total, y=right.total)

    results, node = run_get_node(diamond, x=1)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 114  # (2 + 10) + (2 + 100)


def test_a_single_output_can_be_passed_without_naming_it():
    """A task with one output can be handed straight to the next, since there is nothing to choose."""

    @graph
    def chained(x, y):
        return add(x=add(x=x, y=y), y=y)

    declaration = chained.build()

    assert [(link.source, link.source_port, link.target_port) for link in declaration.dependencies] == [
        ('add', 'total', 'x')
    ]


def test_several_outputs_have_to_be_named():
    """With more than one output there is nothing to pick, so the graph says so instead of guessing."""

    @graph
    def ambiguous(x, y):
        return add(x=divide(x=x, y=y), y=1)

    with pytest.raises(ValueError, match='declares 2 outputs'):
        ambiguous.build()


def test_returning_a_dictionary_names_the_graph_outputs():
    """A graph can return several outputs, under the names it gives them."""

    @graph
    def both(x, y):
        result = divide(x=x, y=y)
        return {'whole': result.quotient, 'rest': result.remainder}

    results, node = run_get_node(both, x=7, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['whole'] == 3
    assert results['rest'] == 1


def test_returning_something_that_is_not_an_output_is_refused():
    """A graph returns the outputs of its tasks or its own inputs, so a plain value cannot be one of them."""

    @graph
    def returns_a_value(x, y):
        add(x=x, y=y)
        return 42

    with pytest.raises(ValueError, match='has to return one of those'):
        returns_a_value.build()


def test_a_graph_can_pass_one_of_its_inputs_on():
    """An input can be an output of the graph, which nothing produces and which is recorded as such."""
    declaration = shift_and_echo.build()

    assert declaration.outputs == {
        'total': Endpoint(task='add', port='total'),
        'echo': Endpoint(task=None, port='x'),
    }

    results, node = run_get_node(shift_and_echo, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 3
    assert results['echo'] == 1


def test_a_graph_inside_a_graph_is_placed_as_one_task():
    """The inner graph is one task carrying its own declaration, so the two graphs stay separate."""
    declaration = add_four_times.build()

    assert [node.name for node in declaration.tasks] == ['add_twice', 'add_twice_2']
    assert all(isinstance(node, SubgraphTask) for node in declaration.tasks)
    assert [node.name for node in declaration.task('add_twice').body.tasks] == ['add', 'add_2']
    assert declaration.outputs == {'total': Endpoint(task='add_twice_2', port='total')}


def test_runs_a_graph_written_inside_a_graph():
    """The inner graph runs as a child process of its own, and what it returns feeds the task after it."""
    results, node = run_get_node(add_four_times, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 9  # ((1 + 2) + 2) + 2 + 2

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()
    assert sorted(entry.link_label for entry in called) == ['add_twice', 'add_twice_2']


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(reaches_for_an_outer_task, id='task-output'),
        pytest.param(reaches_for_an_outer_input, id='graph-input'),
    ],
)
def test_a_graph_inside_another_reaches_nothing_outside_it(declaration):
    """A value from the graph around it would never be passed in, so it is refused where the graph is written."""
    with pytest.raises(ValueError, match='not part of this graph'):
        declaration.build()


def test_a_branch_is_placed_as_one_task_carrying_both_sides():
    """Both branches are declared, so the only thing a run decides is which of the two it takes."""
    declaration = double_or_not.build()
    (branch,) = declaration.tasks

    assert isinstance(branch, BranchTask)
    assert branch.name == 'branch_doubled'
    assert [node.name for node in branch.body.tasks] == ['add']
    assert [node.name for node in branch.otherwise.tasks] == ['add']
    assert declaration.inputs == {'x': (('branch_doubled', 'x'),), 'flag': (('branch_doubled', 'condition'),)}


@pytest.mark.parametrize('flag, expected', [pytest.param(True, 6, id='taken'), pytest.param(False, 3, id='not-taken')])
def test_a_branch_runs_the_side_its_condition_selects(flag, expected):
    """Which side runs is decided while the graph runs, and the branch produces what that side produced."""
    results, node = run_get_node(double_or_not, x=3, flag=flag)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == expected


@pytest.mark.parametrize(
    'flag, expected',
    [pytest.param(True, {'total': 6}, id='taken'), pytest.param(False, {}, id='not-taken')],
)
def test_a_branch_without_an_otherwise_produces_nothing_when_it_is_not_taken(flag, expected):
    """A condition that does not hold leaves the branch with nothing to return, so the output stays off."""
    results, node = run_get_node(maybe_double, x=3, flag=flag)

    assert node.is_finished_ok, node.exit_message
    assert {key: value.value for key, value in results.items()} == expected


def test_a_branch_that_did_not_run_leaves_out_what_takes_its_outputs():
    """A task after a branch that produced nothing has nothing to run on, so it is left out of the run too."""

    @graph
    def add_after_a_branch(x, flag):
        return add(x=branch(flag, then=doubled, x=x).total, y=1)

    results, node = run_get_node(add_after_a_branch, x=3, flag=False)

    assert node.is_finished_ok, node.exit_message
    assert dict(results) == {}
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all() == []


def test_calling_branch_outside_a_graph_is_refused():
    """A branch is part of a graph, so writing one anywhere else says what to do instead."""
    with pytest.raises(TypeError, match='written in the body of a `@graph`'):
        branch(True, then=doubled, x=1)


def test_running_a_graph_once_per_item_is_refused():
    """A graph cannot yet be the thing that fans out, and says so where the fan-out is written."""

    @graph
    def shift_all_twice(values, by):
        return add_twice(x=each(values), y=by)

    with pytest.raises(ValueError, match='Running a graph once per item'):
        shift_all_twice.build()


def test_calling_a_graph_is_refused():
    """A graph is launched rather than called, and says so."""
    with pytest.raises(TypeError, match='launched rather than called'):
        add_twice(1, 2)


def test_a_graph_can_be_submitted():
    """A graph is handed to the launchers like any other process."""
    node = submit(add_twice, x=1, y=2)

    assert isinstance(node, orm.WorkChainNode)


def test_a_task_outside_a_graph_still_runs():
    """Recording a task only happens while a graph is being built."""
    result, node = add.run_get_node(x=orm.Int(1), y=orm.Int(2))

    assert node.is_finished_ok
    assert result['total'] == 3


def test_outputs_rejects_a_bare_string():
    """A bare string would silently declare one output port per character."""
    with pytest.raises(TypeError, match='sequence of port names'):

        @task(outputs='result')
        def bare_string(x):
            return x
