###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for waiting on something outside the graph before going on."""

from __future__ import annotations

from pathlib import Path

import pytest

from aiida.engine import WaitProcess, graph, monitor, run_get_node, submit, task, tasks, wait_for


@monitor
def looked_at_three_times(path) -> bool:
    """Say yes on the third look, leaving a mark each time so that the looks can be counted afterwards."""
    marks = Path(path.value)
    marks.write_text(f'{marks.read_text()}x' if marks.exists() else 'x')

    return len(marks.read_text()) >= 3


@monitor
def never(path) -> bool:
    """Never say yes, so that whatever waits on it waits until there is no time left."""
    return False


@task(outputs=['looks'])
def count_marks(path) -> dict:
    return {'looks': len(Path(path.value).read_text())}


def test_a_monitor_holds_back_what_waits_for_it(tmp_path):
    """A monitor looks again until the condition holds, and only then does what waits for it run."""
    marks = tmp_path / 'marks'

    @graph
    def count_once_settled(path):
        settled = looked_at_three_times(path=path, interval=0.01)
        return {'looks': count_marks(path=path).after(settled).looks}

    results, node = run_get_node(count_once_settled, path=str(marks))

    assert node.is_finished_ok, node.exit_message
    assert results['looks'] == 3, 'the task after the monitor ran once the third look settled it'


def test_a_monitor_that_is_never_satisfied_times_out(tmp_path):
    """A monitor gives up rather than looking forever, which fails it and so the graph waiting on it."""
    watching = never.process_class

    _, node = run_get_node(never, path=str(tmp_path), interval=0.01, timeout=0.05)

    assert not node.is_finished_ok
    assert node.exit_status == watching.exit_codes.ERROR_TIMED_OUT.status
    assert '0.05 seconds' in node.exit_message


def test_a_monitor_is_a_task_of_the_graph(tmp_path):
    """A monitor is a process of its own, so waiting is recorded where every other task is."""
    marks = tmp_path / 'marks'

    @graph
    def count_once_settled(path):
        settled = looked_at_three_times(path=path, interval=0.01)
        return {'looks': count_marks(path=path).after(settled).looks}

    _, node = run_get_node(count_once_settled, path=str(marks))
    ran = tasks(node)

    assert sorted(ran) == ['count_marks', 'looked_at_three_times']
    assert ran['looked_at_three_times'].pk < ran['count_marks'].pk
    assert ran['looked_at_three_times'].is_finished_ok


def test_what_a_monitor_waits_between_looks_is_an_input(tmp_path):
    """How long to wait is a port of the process that runs it, so a graph may say it per run."""
    assert 'interval' in looked_at_three_times.task_spec.inputs
    assert looked_at_three_times.task_spec.inputs['timeout'].default().value == pytest.approx(86400.0)


@task(outputs=['total'])
def add(x, y) -> dict:
    return {'total': x + y}


def test_waiting_for_a_process_that_already_ended_goes_straight_on(tmp_path):
    """The engine is what says a process ended, so one that already has is not looked at on a timer."""
    _, earlier = run_get_node(add, x=1, y=1)

    @graph
    def carry_on(earlier):
        return {'total': add(x=1, y=2).after(wait_for(pk=earlier)).total}

    results, node = run_get_node(carry_on, earlier=earlier.pk)

    assert node.is_finished_ok, node.exit_message
    assert results['total'] == 3
    assert tasks(node)['WaitProcess'].is_finished_ok


def test_waiting_for_a_process_that_failed_stops_the_graph(tmp_path):
    """What waits on a process waits on it going well, so a failure of it is a failure of the wait."""
    _, failed = run_get_node(never, path=str(tmp_path), interval=0.01, timeout=0.02)

    assert not failed.is_finished_ok

    @graph
    def carry_on(earlier):
        return {'total': add(x=1, y=2).after(wait_for(pk=earlier)).total}

    _, node = run_get_node(carry_on, earlier=failed.pk)

    assert not node.is_finished_ok
    assert tasks(node)['WaitProcess'].exit_status == WaitProcess.exit_codes.ERROR_PROCESS_DID_NOT_FINISH_OK.status


@pytest.mark.requires_broker
def test_waiting_for_a_process_that_is_still_running(tmp_path, submit_and_await):
    """A process still going is waited for by being told when it ends, which is what a broker carries."""
    running = submit(never, path=str(tmp_path), interval=0.1, timeout=3.0)

    @graph
    def carry_on(earlier):
        return {'total': add(x=1, y=2).after(wait_for(pk=earlier)).total}

    _, node = run_get_node(carry_on, earlier=running.pk)
    submit_and_await(running, timeout=30)

    assert not node.is_finished_ok, 'the monitor ran out of time, so what waited for it fails too'
    assert tasks(node)['WaitProcess'].exit_status == WaitProcess.exit_codes.ERROR_PROCESS_DID_NOT_FINISH_OK.status
