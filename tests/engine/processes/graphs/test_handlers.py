###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for recovering from the failed runs of a task."""

from __future__ import annotations

import pytest

from aiida import orm
from aiida.common.loaders import get_object_loader
from aiida.engine import (
    ExitCode,
    ProcessHandlerReport,
    TaskWorkChain,
    WorkChain,
    graph,
    handler,
    run_get_node,
    task,
)

DID_NOT_CONVERGE = ExitCode(410, 'did not converge')
RAN_OUT_OF_ROOM = ExitCode(411, 'ran out of room')


@handler(exit_codes=DID_NOT_CONVERGE)
def push_further(node, inputs):
    """Ask for one more step than the run that gave up took."""
    inputs['steps'] = orm.Int(inputs['steps'].value + 1)
    return ProcessHandlerReport(do_break=True)


@task(outputs=['value'], handlers=[push_further])
def converge(steps: int) -> dict:
    """Converge only once it is given enough steps, which is what the handler gives it."""
    if steps < 3:
        return DID_NOT_CONVERGE
    return {'value': steps * 10}


@task(outputs=['value'], handlers=[push_further])
def run_out_of_room(steps: int) -> dict:
    """Fail with something the handler does not name, so nothing recovers from it."""
    return RAN_OUT_OF_ROOM


@task(outputs=['value'])
def converge_alone(steps: int) -> dict:
    """The same task, without the handlers, so that the two can be compared."""
    if steps < 3:
        return DID_NOT_CONVERGE
    return {'value': steps * 10}


@task(outputs=['doubled'])
def double(value: int) -> dict:
    return {'doubled': value * 2}


def test_a_handler_fixes_the_inputs_of_the_next_run():
    """A run that failed is given to the handlers, and what they change is what the next run is launched with."""
    results, node = run_get_node(converge, steps=1)

    assert node.is_finished_ok, node.exit_message
    assert results['value'] == 30
    assert [child.exit_status for child in sorted(node.called, key=lambda child: child.pk)] == [410, 410, 0]


def test_a_handler_is_only_called_for_the_exit_codes_it_names():
    """A failure the handlers say nothing about is left alone, so the task fails rather than looping."""
    _, node = run_get_node(run_out_of_room, steps=1)

    assert not node.is_finished_ok
    assert node.exit_status == run_out_of_room.process_class.exit_codes.ERROR_UNHANDLED_FAILURE.status
    assert [child.exit_status for child in node.called] == [411]


def test_what_a_task_takes_and_produces_does_not_change_when_it_handles():
    """Handling is a way to run a task, so what a graph wires against stays what the task itself declares."""
    assert list(converge.task_spec.inputs) == list(converge_alone.task_spec.inputs)
    assert list(converge.task_spec.outputs) == list(converge_alone.task_spec.outputs)


def test_a_handled_task_in_a_graph_feeds_what_comes_after():
    """A graph places a handled task like any other, and takes its outputs from the run that finally worked."""

    @graph
    def converge_and_double(steps):
        return {'doubled': double(value=converge(steps=steps).value).doubled}

    results, node = run_get_node(converge_and_double, steps=1)

    assert node.is_finished_ok, node.exit_message
    assert results['doubled'] == 60


def test_a_handled_task_that_keeps_failing_stops_the_graph():
    """Handling gives a task more tries, and a task that fails them all still fails the graph."""

    @graph
    def double_what_never_converges(steps):
        return {'doubled': double(value=run_out_of_room(steps=steps).value).doubled}

    _, node = run_get_node(double_what_never_converges, steps=1)

    assert not node.is_finished_ok
    assert 'run_out_of_room' in node.exit_message


def test_a_process_cannot_be_given_handlers():
    """A process is reached by the name it already has, which leaves nowhere to reach a handled one by."""

    class Noop(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.outline()

    with pytest.raises(TypeError, match='Write a `BaseRestartWorkChain` around it'):
        task(Noop, handlers=[push_further])


def test_two_handlers_cannot_share_a_name():
    """A handler is addressed by its name, so two of one name would leave one of them out of reach."""

    @handler
    def push_further(node, inputs):
        return None

    with pytest.raises(ValueError, match="named \\['push_further'\\]"):

        @task(handlers=[push_further, push_further])
        def twice(steps: int) -> int:
            return steps


def test_a_handled_task_and_its_own_process_are_reached_by_different_names():
    """A run records the module and name of its process and is read back from them, so the two need two names."""
    loader = get_object_loader()
    handling = loader.load_object(f'{__name__}:converge_handled')

    assert issubclass(handling, TaskWorkChain)
    assert handling is converge.process_class

    # And the name of the task itself still reaches what runs one attempt of it, which is what a worker picking
    # such an attempt back up off its checkpoint is given.
    assert loader.load_object(f'{__name__}:converge') is converge
    assert converge.recreate_from.__self__ is handling._process_class
