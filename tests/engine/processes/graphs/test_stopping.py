###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for a task that ends by saying what waits on it will not happen."""

from __future__ import annotations

from aiida.engine import Stop, graph, monitor, run_get_node, task, tasks
from aiida.engine.processes.graphs.run import STOPPED


@task(outputs=['total'])
def add(x: int, y: int) -> int:
    return x + y


@monitor
def watches(give_up: bool) -> bool | Stop:
    """Answer whether the condition is met, or that it is not going to be."""
    if give_up:
        return Stop('the thing it waits for is not coming')

    return True


@graph
def waits_then_adds(x, y, give_up):
    watched = watches(give_up=give_up, interval=0.1)

    return {'total': add(x=x, y=y).after(watched).total}


def test_a_monitor_that_is_met_lets_what_waits_run():
    """The ordinary answer, so that the third one is read against it."""
    results, node = run_get_node(waits_then_adds, x=2, y=3, give_up=False)

    assert node.is_finished_ok, node.exit_message
    assert results['total'].value == 5


def test_a_monitor_that_gives_up_skips_what_waits_on_it():
    """What waits is skipped, and the graph is done rather than failed."""
    results, node = run_get_node(waits_then_adds, x=2, y=3, give_up=True)

    assert node.is_finished_ok, node.exit_message
    assert results == {}, 'the task that waited never ran, so the graph produced nothing'
    assert sorted(tasks(node)) == ['watches'], 'and it is not among the processes the graph ran'


def test_the_monitor_says_why_it_stopped():
    """The message is on its node, which is where someone reading the graph afterwards finds it."""
    _, node = run_get_node(waits_then_adds, x=2, y=3, give_up=True)

    watched = tasks(node)['watches']

    assert watched.exit_status == STOPPED
    assert watched.exit_message == 'the thing it waits for is not coming'
