###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for reaching what a graph ran after the fact."""

from __future__ import annotations

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine import branch, each, graph, run_get_node, task, tasks


@task(outputs=['total'])
def add(x, y):
    return x + y


@graph
def double(value):
    return {'total': add(x=value, y=value).total}


@graph
def pipeline(value, refine_it):
    """Place a task, a graph, a fan-out and a branch, so each way of naming a run is covered."""
    doubled = double(value=value)
    spread = add(x=each([1, 2]), y=value)

    with branch(refine_it) as refined:
        refined.returns(total=add(x=doubled.total, y=1).total)

    with refined.otherwise:
        refined.returns(total=doubled.total)

    return {'total': refined.total, 'spread': spread.total}


@pytest.fixture
def ran():
    """Run the pipeline and return what it ran, by name."""
    _, node = run_get_node(pipeline, value=3, refine_it=True)
    assert node.is_finished_ok, node.exit_message

    return tasks(node)


def test_a_task_is_reached_by_the_name_the_graph_gave_it(ran):
    """A task is a process of its own, so what it produced is on the node the graph called under its name."""
    assert ran['double'].outputs.total == 6


def test_a_task_inside_a_graph_is_reached_by_the_names_on_the_way_to_it(ran):
    """A graph placed as a task called its own tasks, which the names on the way to one walk through."""
    assert ran['double.add'].outputs.total == 6
    assert ran['double.add'].pk in [child.pk for child in ran['double'].called]


def test_each_run_of_a_fan_out_is_reached_by_the_item_it_was_for(ran):
    """A task that ran once per item ran a process per item, each named after the item it was for."""
    assert [ran[f'add_item_{index}'].outputs.total for index in (0, 1)] == [4, 5]


def test_the_tasks_that_ran_are_listed_by_name(ran):
    """What a graph ran is what it called, under the name it knows each of them by."""
    assert sorted(ran) == ['add_item_0', 'add_item_1', 'branch', 'double']


@pytest.mark.parametrize(('refine_it', 'expected'), ((True, ['add']), (False, [])))
def test_a_branch_lists_only_the_side_that_was_taken(refine_it, expected):
    """A task on the side a branch did not take never ran, so there is no process of it to reach."""
    _, node = run_get_node(pipeline, value=3, refine_it=refine_it)

    assert node.is_finished_ok, node.exit_message
    assert sorted(tasks(tasks(node)['branch'])) == expected


def test_a_name_that_did_not_run_says_what_did(ran):
    """A task is left out of a run where the branch it sits in was not taken, which the message has to say."""
    with pytest.raises(KeyError, match=r'ran no task `relax`. It ran \[.*double.*\]'):
        ran['relax']

    with pytest.raises(KeyError, match=r'`double` ran no task `relax`'):
        ran['double.relax']


def test_a_name_standing_for_more_than_one_process_says_so():
    """A work chain that submits without a call link label leaves every run under the same name."""
    parent = orm.WorkflowNode().store()

    for _ in range(2):
        child = orm.WorkflowNode()
        child.base.links.add_incoming(parent, link_label='CALL', link_type=LinkType.CALL_WORK)
        child.store()

    ran = tasks(parent)

    assert sorted(ran) == ['CALL']

    with pytest.raises(ValueError, match='called 2 processes `CALL`'):
        ran['CALL']
