###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Does a broker restart preserve the pending order the in-memory queue reports?

One property, no reference model, let Hypothesis search for the interleaving that breaks it.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
from hypothesis import settings
from hypothesis.stateful import RuleBasedStateMachine, precondition, rule

from aiida.brokers.zeromq.queue import PersistentQueue


class RestartPreservesOrder(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.path = Path(tempfile.mkdtemp())
        self.queue = PersistentQueue(self.path)
        self.counter = 0
        self.checked_out: list[str] = []

    def teardown(self):
        shutil.rmtree(self.path, ignore_errors=True)

    @rule()
    def push(self):
        task_id = f'task-{self.counter:04d}'
        self.counter += 1
        self.queue.push(task_id, {'n': self.counter})

    @rule()
    def pop(self):
        result = self.queue.pop()
        if result is not None:
            self.checked_out.append(result[0])

    @precondition(lambda self: self.checked_out)
    @rule()
    def nack_requeue(self):
        self.queue.nack(self.checked_out.pop(0), requeue=True)

    @rule()
    def restart(self):
        before = [task_id for task_id, _ in self.queue.get_all_pending()]
        self.queue = PersistentQueue(self.path)  # crash + fresh process
        after = [task_id for task_id, _ in self.queue.get_all_pending()]
        self.checked_out = []
        # recovery legitimately *adds* the in-flight tasks back into pending, so only
        # check that the tasks that were already pending keep their relative order
        survivors = [task_id for task_id in after if task_id in before]
        assert survivors == before, f'restart reordered the queue: before={before} after={after}'


RestartPreservesOrder.TestCase.settings = settings(max_examples=500, stateful_step_count=30)


@pytest.mark.xfail(
    strict=True,
    reason=(
        'Known finding: nack(requeue=True) puts the task at the FRONT of the in-memory deque '
        '(queue.py:181), but _load() re-sorts recovered files by the push timestamp baked into '
        'the filename (queue.py:129). Retry priority is therefore lost on broker restart. '
        'Remove this marker once the ordering is made durable.'
    ),
)
class TestRestartPreservesOrder(RestartPreservesOrder.TestCase):
    pass
