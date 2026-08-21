###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Model-based stateful tests for ``aiida.brokers.zeromq.queue.PersistentQueue``.

Mirrors the Quint/Stateright broker model, but drives the *real* implementation:
each rule is one of the abstract actions, and the reference model is the
abstraction. Hypothesis generates the interleavings.

    pop            ~ dispatch
    nack(requeue)  ~ suspect / requeue
    ack            ~ ack
    restart        ~ RestartBroker (queue.py:_load crash recovery)
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from hypothesis import settings
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

from aiida.brokers.zeromq.queue import PersistentQueue


class QueueStateMachine(RuleBasedStateMachine):
    """Drive PersistentQueue against an in-memory reference model."""

    def __init__(self):
        super().__init__()
        self.path = Path(tempfile.mkdtemp())
        self.queue = PersistentQueue(self.path)
        self.counter = 0
        # reference model
        self.pending: list[str] = []  # task ids, FIFO
        self.processing: list[str] = []  # checked out, awaiting ack/nack
        self.push_index: dict[str, int] = {}  # task id -> push order

    def teardown(self):
        shutil.rmtree(self.path, ignore_errors=True)

    @rule()
    def push(self):
        task_id = f'task-{self.counter:04d}'
        self.counter += 1
        self.push_index[task_id] = self.counter
        self.queue.push(task_id, {'n': self.counter})
        self.pending.append(task_id)

    @rule()
    def pop(self):
        result = self.queue.pop()
        if not self.pending:
            assert result is None, f'popped {result} from an empty queue'
            return
        expected = self.pending.pop(0)
        assert result is not None, f'expected to pop {expected}, got None'
        assert result[0] == expected, f'FIFO violated: expected {expected}, got {result[0]}'
        self.processing.append(expected)

    @precondition(lambda self: self.processing)
    @rule()
    def ack(self):
        task_id = self.processing.pop(0)
        assert self.queue.ack(task_id) is True

    @precondition(lambda self: self.processing)
    @rule()
    def nack_requeue(self):
        task_id = self.processing.pop(0)
        assert self.queue.nack(task_id, requeue=True) is True
        self.pending.insert(0, task_id)  # implementation requeues at the FRONT

    @precondition(lambda self: self.processing)
    @rule()
    def nack_discard(self):
        task_id = self.processing.pop(0)
        assert self.queue.nack(task_id, requeue=False) is True

    @rule()
    def restart(self):
        """Fresh broker process over the same storage directory."""
        self.queue = PersistentQueue(self.path)
        # _load() recovers processing -> pending, then sorts *everything* by filename,
        # i.e. by push timestamp -- any in-memory ordering is discarded.
        recovered = self.pending + self.processing
        self.pending = sorted(recovered, key=lambda t: self.push_index[t])
        self.processing = []

    @invariant()
    def no_task_is_lost(self):
        on_disk = {t for t, _ in self.queue.get_all_pending()} | {t for t, _ in self.queue.get_all_processing()}
        expected = set(self.pending) | set(self.processing)
        assert on_disk == expected, f'lost/leaked: on disk {on_disk}, model {expected}'

    @invariant()
    def counts_agree(self):
        assert self.queue.size() == len(self.pending)
        assert self.queue.processing_count() == len(self.processing)


QueueStateMachine.TestCase.settings = settings(max_examples=300, stateful_step_count=40)
TestQueueStateMachine = QueueStateMachine.TestCase
