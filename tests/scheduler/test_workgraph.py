###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for scheduling workgraph processes."""

from __future__ import annotations

from types import SimpleNamespace

from aiida.engine import WorkGraphProcess
from aiida.scheduler import KIND_WORKGRAPH, Scheduler


class FakeCommunicator:
    """Minimal queue-capable communicator double: records instead of sending."""

    def __init__(self):
        self.sent: list[tuple[str, dict]] = []
        self.subscriptions: list[tuple[str, str]] = []

    def task_send(self, task, no_reply=False, queue='default'):
        self.sent.append((queue, dict(task)))

    def add_task_subscriber(self, subscriber, identifier=None, queue='default'):
        self.subscriptions.append((identifier, queue))
        return identifier

    def add_broadcast_subscriber(self, subscriber, identifier=None):
        self.subscriptions.append((identifier, 'broadcast'))
        return identifier

    def close(self):
        pass


def test_workgraph_is_admitted_like_every_other_process():
    """Test the scheduler dispatches workgraphs rather than orchestrating them."""
    communicator = FakeCommunicator()
    identifier = f'{WorkGraphProcess.__module__}:{WorkGraphProcess.__name__}'
    scheduler = Scheduler(
        communicator=communicator,
        kind_by_identifier={identifier: KIND_WORKGRAPH},
        node_loader=lambda pid: SimpleNamespace(node_type='process.ProcessNode.', process_type=identifier),
    )
    scheduler.start()

    task_id = scheduler._on_submitted(communicator, {'task': 'continue', 'args': {'pid': 7}})

    assert scheduler._tasks[task_id]['kind'] == KIND_WORKGRAPH
    assert scheduler._tasks[task_id]['state'] == 'DISPATCHED'
    assert communicator.sent[0][1]['scheduler_task_id'] == task_id
