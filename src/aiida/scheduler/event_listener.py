###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Worker-side completion announcer for the scheduler.

A :class:`SchedulerEventListener` is a plain :class:`plumpy.ProcessListener` bound
to one launched task: attach it to the process and it reports the terminal
state to the scheduler when the process finishes, excepts, or is killed. No
``Process`` subclass changes anything — listeners are additive, which is the
whole point: the scheduler learns completions through the process's existing
event API instead of a new one.

Receipts go to the durable completions queue (see
:data:`aiida.scheduler.scheduler.SCHEDULER_COMPLETIONS`), not broadcasts:
the broker holds them while the scheduler is down and redelivers until they
are acknowledged, so no lost event can strand a throttled task. The
scheduler's bookkeeping is idempotent, so a receipt that arrives twice
applies once.

Wiring (not done globally yet — attach where a task is launched with
knowledge of its scheduler id)::

    announcer = SchedulerEventListener(communicator, task_id)
    process.add_process_listener(announcer)
"""

from __future__ import annotations

import logging
import typing as t

from plumpy import ProcessListener

import kiwipy
from aiida.scheduler.scheduler import SCHEDULER_COMPLETIONS

_LOGGER = logging.getLogger(__name__)


class SchedulerEventListener(ProcessListener):
    """Announce one task's terminal state to the scheduler.

    :param communicator: used to send the receipt; must already be started.
    :param task_id: scheduler-assigned id of the launched task, echoed back
        so the scheduler can correlate the receipt.
    :param completions_queue: queue carrying receipts (testing seam).
    """

    def __init__(
        self,
        communicator: kiwipy.Communicator,
        task_id: str,
        *,
        completions_queue: str = SCHEDULER_COMPLETIONS,
    ):
        self._communicator = communicator
        self._task_id = task_id
        self._completions_queue = completions_queue

    def on_process_finished(self, process: t.Any, outputs: t.Any) -> None:
        """Report normal completion."""
        self._announce('FINISHED')

    def on_process_excepted(self, process: t.Any, reason: str) -> None:
        """Report failure, carrying the reason for debuggability."""
        self._announce('FAILED', reason)

    def on_process_killed(self, process: t.Any, msg: str) -> None:
        """Report kills as failures; the registry tracks finished/failed only."""
        self._announce('FAILED', msg)

    def _announce(self, terminal: str, detail: str | None = None) -> None:
        body: dict[str, t.Any] = {'scheduler_task_id': self._task_id, 'terminal': terminal}
        if detail:
            body['detail'] = detail
        _LOGGER.debug('Announcing %s for task %s.', terminal, self._task_id)
        self._communicator.task_send(body, no_reply=True, queue=self._completions_queue)
