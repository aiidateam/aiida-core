###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the process scheduling service."""

from __future__ import annotations

import pytest

from aiida.scheduler import SCHEDULER_QUEUE, Scheduler


class FakeCommunicator:
    """Minimal queue-capable communicator double: records instead of sending."""

    def __init__(self):
        self.sent: list[tuple[str, dict]] = []
        self.subscriptions: list[tuple[str, str]] = []
        self.closed = False

    def task_send(self, task, no_reply=False, queue='default'):
        self.sent.append((queue, dict(task)))

    def add_task_subscriber(self, subscriber, identifier=None, queue='default'):
        self.subscriptions.append((identifier, queue))
        return identifier

    def add_broadcast_subscriber(self, subscriber, identifier=None):
        self.subscriptions.append((identifier, 'broadcast'))
        return identifier

    def close(self):
        self.closed = True


@pytest.fixture
def communicator():
    return FakeCommunicator()


@pytest.fixture
def scheduler(communicator):
    return Scheduler(communicator=communicator)


def test_scheduler_queue_constant():
    """Test the scheduler queue has a stable, documented name."""
    assert SCHEDULER_QUEUE == 'scheduler'


def test_requires_endpoint_or_communicator():
    """Test the scheduler refuses ambiguous construction."""
    with pytest.raises(ValueError, match='either'):
        Scheduler()
    with pytest.raises(ValueError, match='either'):
        Scheduler(router_endpoint='ipc:///tmp/x', communicator=FakeCommunicator())


def test_start_subscribes_scheduler_queue(scheduler, communicator):
    """Test starting subscribes to the scheduler queue, not the default."""
    scheduler.start()
    assert ('scheduler-queue', SCHEDULER_QUEUE) in communicator.subscriptions
    assert ('scheduler-events', 'broadcast') in communicator.subscriptions


def test_stop_closes_communicator(scheduler, communicator):
    """Test stopping closes the owned communicator."""
    scheduler.start()
    scheduler.stop()
    assert communicator.closed


def test_forwards_submission_to_worker_queue(scheduler, communicator):
    """Test an admitted submission is forwarded to the default worker queue."""
    scheduler.start()
    body = {'task': 'launch', 'process_class': 'some.Class'}
    assert scheduler._on_submitted(communicator, body) is None
    assert communicator.sent == [('default', body)]


def test_completion_lifecycle(scheduler, communicator):
    """Test completions move registry records to terminal states."""
    from aiida.scheduler import COMPLETED_SUBJECT, FAILED_SUBJECT

    scheduler.start()
    scheduler._on_submitted(communicator, {'task_id': 'a'})
    scheduler._on_submitted(communicator, {'task_id': 'b'})
    assert scheduler.in_flight == 2

    scheduler._on_broadcast(communicator, {'task_id': 'a'}, 'worker', COMPLETED_SUBJECT, None)
    assert scheduler.in_flight == 1
    assert scheduler.duplicates == 0

    # Duplicate delivery changes nothing but counts.
    scheduler._on_broadcast(communicator, {'task_id': 'a'}, 'worker', COMPLETED_SUBJECT, None)
    assert scheduler.in_flight == 1
    assert scheduler.duplicates == 1

    # Unknown task ids and subjects never create state.
    scheduler._on_broadcast(communicator, {'task_id': 'ghost'}, 'worker', COMPLETED_SUBJECT, None)
    scheduler._on_broadcast(communicator, {'task_id': 'b'}, 'worker', 'unrelated.subject', None)
    assert scheduler.in_flight == 1
    assert scheduler.duplicates == 2

    scheduler._on_broadcast(communicator, {'task_id': 'b'}, 'worker', FAILED_SUBJECT, None)
    assert scheduler.in_flight == 0


def test_create_communicator_is_zeromq():
    """Test the default communicator factory builds a ZeroMQ communicator."""
    from aiida.brokers.zeromq.communicator import ZeromqCommunicator

    scheduler = Scheduler.__new__(Scheduler)
    scheduler.router_endpoint = 'ipc:///tmp/does-not-exist/router.sock'
    scheduler.client_id = 'scheduler'
    communicator = scheduler.create_communicator()
    assert isinstance(communicator, ZeromqCommunicator)
