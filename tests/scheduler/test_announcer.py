###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the worker-side completion announcer."""

from __future__ import annotations

import pytest

from aiida.scheduler import SCHEDULER_COMPLETIONS, SchedulerEventListener


class FakeCommunicator:
    """Minimal queue-capable communicator double: records instead of sending."""

    def __init__(self):
        self.sent: list[tuple[str, dict]] = []

    def task_send(self, task, no_reply=False, queue='default'):
        self.sent.append((queue, dict(task)))


@pytest.fixture
def communicator():
    return FakeCommunicator()


def test_finished_announces(communicator):
    """Test normal completion publishes a FINISHED receipt to the durable queue."""
    announcer = SchedulerEventListener(communicator, 'task-1')
    announcer.on_process_finished(process=None, outputs={})
    assert communicator.sent == [(SCHEDULER_COMPLETIONS, {'scheduler_task_id': 'task-1', 'terminal': 'FINISHED'})]


def test_excepted_announces_failed_with_reason(communicator):
    """Test failures publish FAILED receipts carrying the reason."""
    announcer = SchedulerEventListener(communicator, 'task-2')
    announcer.on_process_excepted(process=None, reason='boom')
    (queue, body), *_ = communicator.sent
    assert queue == SCHEDULER_COMPLETIONS
    assert body['scheduler_task_id'] == 'task-2'
    assert body['terminal'] == 'FAILED'
    assert body['detail'] == 'boom'


def test_killed_announces_failed(communicator):
    """Test kills publish FAILED receipts (the registry tracks finished/failed only)."""
    announcer = SchedulerEventListener(communicator, 'task-3')
    announcer.on_process_killed(process=None, msg='stop')
    (queue, body), *_ = communicator.sent
    assert queue == SCHEDULER_COMPLETIONS
    assert body['terminal'] == 'FAILED'


def test_is_process_listener():
    """Test the announcer plugs into the existing process event API."""
    from plumpy import ProcessListener

    assert issubclass(SchedulerEventListener, ProcessListener)
