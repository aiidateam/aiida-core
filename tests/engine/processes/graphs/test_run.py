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
from aiida.engine import (
    Dependency,
    Endpoint,
    GraphRun,
    GraphSpec,
    LoopTask,
    ProcessTask,
    branch,
    each,
    graph,
    run_get_node,
    task,
    tasks,
)


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


def linear() -> GraphSpec:
    """Return `add(add(1, 1), 3)`, so that the second task waits for the first."""
    return GraphSpec(
        tasks=(
            ProcessTask(name='first', spec=add.task_spec, inputs={'x': 1, 'y': 1}),
            ProcessTask(name='second', spec=add.task_spec, inputs={'y': 3}),
        ),
        dependencies=(Dependency(source='first', source_port='total', target='second', target_port='x'),),
        outputs={'total': Endpoint(task='second', port='total')},
    )


def test_the_frontier_is_what_could_start_now():
    """What orders several graphs against each other asks each of them this before saying which of them may."""
    run = GraphRun(graph=linear(), given={})

    assert run.frontier() == ['first'], 'the second waits for what the first produces'


def test_asking_for_the_frontier_decides_nothing():
    """It is a question, so a graph that is asked twice answers the same, and has started nothing either time."""
    run = GraphRun(graph=linear(), given={})

    assert run.frontier() == run.frontier() == ['first']
    assert run.decided == set()
    assert not run.pending


def test_the_frontier_is_what_a_step_begins():
    """A step decides what the frontier named, so the two agree on what a graph is able to do."""
    run = GraphRun(graph=linear(), given={})
    named = run.frontier()

    assert [start.instance for start in run.step().starts] == named
    assert run.frontier() == [], 'what has been decided is not on the frontier again'


def test_the_frontier_moves_on_once_what_it_named_has_finished():
    """A task settles the ones after it, which is what carries a graph from one frontier to the next."""
    _, node = run_get_node(add, x=1, y=1)

    run = GraphRun(graph=linear(), given={})
    run.step()
    run.started('first', node.pk)

    assert run.frontier() == [], 'nothing may start while the first is still running'

    run.completed('first', node.pk)

    assert run.frontier() == ['second']


@task(outputs=['value', 'keep_going'])
def step_down(value):
    """Take one off the value, and say whether there is anything left to take off."""
    return value - 1, value - 1 > 0


@graph
def stepping(value):
    stepped = step_down(value=value)
    return {'value': stepped.value, 'keep_going': stepped.keep_going}


def going_round(max_iterations: int = 10) -> GraphSpec:
    """Return a graph whose one task is a loop over `stepping`."""
    return GraphSpec(
        tasks=(
            LoopTask(
                name='loop',
                body=stepping.build(),
                condition_port='keep_going',
                max_iterations=max_iterations,
                inputs={'value': 3},
            ),
        )
    )


def after_one_run(spec: GraphSpec, value: int) -> GraphRun:
    """Return a run of the graph whose loop has been round once, on a real run of the body."""
    run = GraphRun(graph=spec, given={})
    run.step()

    _, node = run_get_node(stepping, value=value)
    run.started('loop_iteration_0', node.pk)
    run.completed('loop_iteration_0', node.pk)

    return run


@pytest.mark.parametrize(
    ('value', 'expected'),
    ((3, ['loop']), (1, [])),
    ids=('goes-round-again', 'condition-turned'),
)
def test_a_loop_is_on_the_frontier_while_it_has_a_run_to_go(value, expected):
    """A loop that has run before can start again, which is something the tasks it waits for cannot."""
    assert after_one_run(going_round(), value).frontier() == expected


def test_a_loop_that_has_run_as_often_as_it_may_is_not_on_the_frontier():
    """A loop stops where it is told to, so there is nothing it could start however its condition reads."""
    assert after_one_run(going_round(max_iterations=1), value=3).frontier() == []
