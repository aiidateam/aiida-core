###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Process scheduling service.

The :class:`Scheduler` is the gatekeeper between submission and execution:
clients submit process tasks to the scheduler queue and the scheduler admits
them onto the worker queue. Anything submitted straight to the worker queue
bypasses scheduling entirely, which is why
:class:`~aiida.engine.processes.communications.RemoteProcessThreadController`
supports injecting the scheduler queue for submissions.

Current admission policy is forward-everything: the structure (queue
separation, gate point, receipts) is the deliverable, scheduling policy
(dependencies, throttling, pool routing) follows. Submissions are always
forwarded fire-and-forget; on the ZeroMQ broker, task futures resolve at
queue acceptance anyway, so no reply semantics are lost in forwarding.
"""

from __future__ import annotations

import logging
import typing as t

import kiwipy
from aiida.engine.processes.communications import RemoteProcessThreadController

_LOGGER = logging.getLogger(__name__)

#: Name of the broker task queue that feeds the scheduler. Submitters address
#: this queue; the scheduler subscribes to it and dispatches admitted tasks to
#: the default worker queue.
SCHEDULER_QUEUE = 'scheduler'

#: Broadcast subject workers publish when a task finishes. The scheduler
#: subscribes to learn completions (sender futures resolve at queue
#: acceptance, so completions must travel as events, not as futures).
COMPLETED_SUBJECT = 'scheduler.task.completed'

#: Broadcast subject workers publish when a task fails.
FAILED_SUBJECT = 'scheduler.task.failed'


class Scheduler:
    """Gate process submissions before they reach workers.

    The scheduler subscribes to :data:`SCHEDULER_QUEUE`, admits each submitted
    process task and forwards it to the worker queue through its owned
    controller. It owns its communicator (created behind
    :meth:`create_communicator`) and shares no state with the broker beyond
    broker messages.

    The controller is composed, not inherited: a scheduler *uses* submission
    vocabulary for the forwarding path, it *is not* a controller. This keeps
    the scheduler's public surface narrow as orchestration grows.
    """

    def __init__(
        self,
        router_endpoint: str | None = None,
        communicator: kiwipy.Communicator | None = None,
        client_id: str = 'scheduler',
    ):
        """Create the scheduler.

        :param router_endpoint: broker endpoint used when creating the communicator.
        :param communicator: an existing communicator, used as-is (mainly for tests).
        :param client_id: scheduler identity on the broker.
        """
        msg = 'Provide either `router_endpoint` or `communicator`.'
        if (router_endpoint is None) == (communicator is None):
            raise ValueError(msg)
        self.router_endpoint = router_endpoint
        self.client_id = client_id
        self._communicator = communicator if communicator is not None else self.create_communicator()
        self._delivery = RemoteProcessThreadController(self._communicator)
        # Lifecycle registry: logical task id -> record. The only source of
        # completion facts until workers announce; see ``COMPLETED_SUBJECT``.
        self._tasks: dict[str, dict[str, t.Any]] = {}
        self._duplicates = 0

    def create_communicator(self) -> kiwipy.Communicator:
        """Create the broker connection.

        Override to change transports, authentication, or tuning. The default
        connects a :class:`~aiida.brokers.zeromq.communicator.ZeromqCommunicator`.

        :return: an unstarted communicator; :meth:`start` starts it.
        """
        from aiida.brokers.zeromq.communicator import ZeromqCommunicator

        assert self.router_endpoint is not None
        return ZeromqCommunicator(router_endpoint=self.router_endpoint, client_id=self.client_id)

    def start(self) -> None:
        """Start the communicator and subscribe to the scheduler queue."""
        communicator = self._communicator
        assert communicator is not None
        # ``start`` is transport-specific (absent on the kiwipy base); the
        # scheduler queue subscription below is what actually matters.
        start_method = getattr(communicator, 'start', None)
        if start_method is not None:
            start_method()
        communicator.add_task_subscriber(
            self._on_submitted, identifier=f'{self.client_id}-queue', queue=SCHEDULER_QUEUE
        )
        communicator.add_broadcast_subscriber(self._on_broadcast, identifier=f'{self.client_id}-events')

    def stop(self) -> None:
        """Close the communicator."""
        communicator = self._communicator
        if communicator is not None:
            communicator.close()

    def _on_submitted(self, comm: kiwipy.Communicator, body: t.Any) -> None:
        """Admit one submitted process task onto the worker queue.

        Runs on the communicator's loop thread; forwards fire-and-forget so it
        never blocks. Returns ``None``: submitters use ``no_reply`` towards the
        scheduler queue (acceptance is the broker's immediate ack).
        """
        _LOGGER.debug('Scheduler admitting submitted task.')
        task_id = body.get('task_id') if isinstance(body, dict) else None
        if task_id is not None:
            self._tasks[task_id] = {'state': 'DISPATCHED', 'body': body}
        self._delivery.task_send(body, no_reply=True)

    def _on_broadcast(
        self,
        comm: kiwipy.Communicator,
        body: t.Any,
        sender: str,
        subject: str | None,
        correlation_id: t.Any | None,
    ) -> None:
        """Record worker completions into the lifecycle registry.

        Runs on the communicator's loop thread; registry updates only, never
        blocks. Unknown subjects are ignored; completions for unknown or
        already-terminal tasks count as duplicates, never as state changes.
        """
        if subject == COMPLETED_SUBJECT:
            self._complete(body, terminal='FINISHED')
        elif subject == FAILED_SUBJECT:
            self._complete(body, terminal='FAILED')

    def _complete(self, body: t.Any, terminal: str) -> None:
        task_id = body.get('task_id') if isinstance(body, dict) else None
        record = self._tasks.get(task_id) if task_id is not None else None
        if record is None or record['state'] in {'FINISHED', 'FAILED'}:
            self._duplicates += 1
            return
        record['state'] = terminal

    @property
    def in_flight(self) -> int:
        """Return the number of dispatched tasks without a terminal state."""
        return sum(1 for record in self._tasks.values() if record['state'] not in {'FINISHED', 'FAILED'})

    @property
    def duplicates(self) -> int:
        """Return the number of duplicate or unknown completions seen."""
        return self._duplicates
