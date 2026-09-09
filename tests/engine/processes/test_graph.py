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
from aiida.engine import Endpoint, MapTask, each, graph, run_get_node, submit, task

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


def test_records_tasks_links_and_inputs():
    """The body is not executed: it declares the tasks, what feeds them, and what the graph returns."""
    dag = add_twice.build()

    assert [node.name for node in dag.tasks] == ['add', 'add_2']
    assert [(link.source, link.source_port, link.target, link.target_port) for link in dag.links] == [
        ('add', 'total', 'add_2', 'x')
    ]
    assert dag.outputs == {'total': Endpoint(task='add_2', port='total')}


def test_the_declaration_holds_no_values():
    """The graph names its inputs and records where each goes, so one declaration describes every run."""
    dag = add_twice.build()

    assert [node.inputs for node in dag.tasks] == [{}, {}]
    assert dag.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('add_2', 'y'))}


def test_the_same_declaration_serves_every_run():
    """Two runs with different values store the same declaration, which is what makes it a template."""
    first, first_node = run_get_node(add_twice, x=1, y=2)
    second, second_node = run_get_node(add_twice, x=10, y=20)

    assert first['total'] == 5
    assert second['total'] == 50
    assert first_node.inputs.dag.get_dict() == second_node.inputs.dag.get_dict()
    assert first_node.inputs.graph_inputs.x != second_node.inputs.graph_inputs.x


def test_runs_what_was_written():
    """Running the graph gives the result the same code would give if the tasks had simply been called."""
    results, node = run_get_node(add_twice, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 5  # (1 + 2) + 2

    called = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
    assert sorted(entry.link_label for entry in called) == ['add', 'add_2']


@graph
def shift_all(values, by):
    """Run one task per item of a collection, which is what `each` marks."""
    return add(x=each(values), y=by)


def test_each_places_a_task_that_fans_out():
    """Marking an input with `each` declares a task run once per item, over that input."""
    dag = shift_all.build()
    (node,) = dag.tasks

    assert isinstance(node, MapTask)
    assert node.item_port == 'x'
    assert dag.inputs == {'values': (('add', 'x'),), 'by': (('add', 'y'),)}


def test_a_fan_out_runs_once_per_item():
    """Every item gets a process of its own, and the results come back under the key of the item."""
    results, node = run_get_node(shift_all, values=[1, 2, 3], by=10)

    assert node.is_finished_ok, node.exit_message
    assert {key: value.value for key, value in results['total'].items()} == {
        'item_0': 11,
        'item_1': 12,
        'item_2': 13,
    }


@task(outputs=['values'])
def spread(n):
    """Produce the collection that a later task is run over."""
    return list(range(int(n)))


@graph
def shift_spread(n, by):
    made = spread(n=n)
    return add(x=each(made.values), y=by)


def test_a_fan_out_can_take_its_collection_from_a_task():
    """How many items there are can depend on what another task produced, so it is only known while running."""
    dag = shift_spread.build()

    assert isinstance(dag.task('add'), MapTask)
    assert [(link.source, link.source_port, link.target, link.target_port) for link in dag.links] == [
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
    dag = add_twice.build()

    assert [node.name for node in dag.tasks] == ['add', 'add_2']


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

    dag = chained.build()

    assert [(link.source, link.source_port, link.target_port) for link in dag.links] == [('add', 'total', 'x')]


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


@graph
def shift_and_echo(x, y):
    """Return a computed output beside one of the graph's own inputs, passed on unchanged."""
    return {'total': add(x=x, y=y).total, 'echo': x}


def test_a_graph_can_pass_one_of_its_inputs_on():
    """An input can be an output of the graph, which nothing produces and which is recorded as such."""
    dag = shift_and_echo.build()

    assert dag.outputs == {
        'total': Endpoint(task='add', port='total'),
        'echo': Endpoint(task=None, port='x'),
    }

    results, node = run_get_node(shift_and_echo, x=1, y=2)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 3
    assert results['echo'] == 1


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
