###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for running a graph again, which is what restarting one from a task is."""

from __future__ import annotations

import pytest

from aiida.engine import ExitCode, graph, rerun_from, run_get_node, task, tasks
from aiida.manage.caching import enable_caching

REFUSING = {'still': True}


@task(outputs=['total'])
def add(x, y) -> dict:
    return {'total': x + y}


@task(outputs=['doubled'])
def double(value) -> dict:
    """Fail until it is told to stop, standing for a task whose reason for failing is fixed between runs."""
    if REFUSING['still']:
        return ExitCode(410, 'not today')

    return {'doubled': value * 2}


@graph
def pipeline(x, y):
    return {'doubled': double(value=add(x=x, y=y).total).doubled}


@pytest.fixture
def refusing():
    """Make `double` fail, and let it work again once the test is over."""
    REFUSING['still'] = True
    yield
    REFUSING['still'] = False


@pytest.fixture(autouse=True)
def caching():
    """Run with caching on, which is what makes running a graph again cost nothing."""
    with enable_caching(identifier='*'):
        yield


def cached(node) -> dict[str, bool]:
    """Return which of the tasks of a graph were taken from the cache."""
    return {name: task.base.caching.is_created_from_cache for name, task in tasks(node).items()}


def test_running_a_graph_again_takes_every_task_from_the_cache():
    """A graph is a template, so running it again runs the same tasks, and every one of them is already there."""
    REFUSING['still'] = False

    _, first = run_get_node(pipeline, x=11, y=2)
    _, again = run_get_node(pipeline, x=11, y=2)

    assert first.is_finished_ok, first.exit_message
    assert cached(first) == {'add': False, 'double': False}
    assert cached(again) == {'add': True, 'double': True}


def test_a_named_task_runs_again_and_what_it_does_not_change_does_not():
    """Running one task again is what a restart from it is, and only what its results change follows it."""
    REFUSING['still'] = False

    _, first = run_get_node(pipeline, x=22, y=2)

    assert rerun_from(first, 'add') == [tasks(first)['add']]

    _, again = run_get_node(pipeline, x=22, y=2)

    assert cached(again) == {'add': False, 'double': True}, '`double` takes the same value, so it stays cached'


def test_a_graph_that_failed_repeats_the_failure_until_it_is_told_not_to(refusing):
    """A task that failed is as valid a cache source as one that worked, so the failure comes back with it."""
    _, first = run_get_node(pipeline, x=33, y=2)

    assert first.exit_status == pipeline.process_class.exit_codes.ERROR_TASK_FAILED.status
    assert tasks(first)['double'].exit_status == 410

    REFUSING['still'] = False
    _, again = run_get_node(pipeline, x=33, y=2)

    assert cached(again) == {'add': True, 'double': True}
    assert not again.is_finished_ok, 'the failure was taken from the cache, so the graph stopped in the same place'


def test_what_did_not_finish_well_runs_again_when_nothing_is_named(refusing):
    """A graph that stopped somewhere is run again once the reason is fixed, which is what naming nothing means."""
    _, first = run_get_node(pipeline, x=44, y=2)

    assert rerun_from(first) == [tasks(first)['double']]

    REFUSING['still'] = False
    results, again = run_get_node(pipeline, x=44, y=2)

    assert again.is_finished_ok, again.exit_message
    assert results['doubled'] == 92
    assert cached(again) == {'add': True, 'double': False}, 'only what failed ran again'
