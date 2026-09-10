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

Admission policy is per-kind concurrency caps (``max_in_flight_per_kind``),
defaulting to admit-everything: tasks beyond a cap stay ``SUBMITTED`` until
completions release capacity. Kinds come from the tasks themselves — launch
bodies name their process class, continue bodies carry a pid whose checkpoint
(node metadata) records the process type — so the scheduler never adapts the
message protocol and never touches transports. Completions arrive two ways:
the durable completions queue (bookkeeping source of truth — redelivered until
acknowledged, so no lost event can strand a held task) and broadcasts
(best-effort observability); both feed the same idempotent registry, so a
receipt arriving twice applies once. Submissions are always forwarded
fire-and-forget; on the ZeroMQ broker, task futures resolve at queue acceptance
anyway, so no reply semantics are lost in forwarding.

Rough logic — everything the scheduler does on incoming messages::

    on SUBMISSION (scheduler queue):
        kind = kind of body            # launch: class identifier (+registry);
                                        # continue: pid -> checkpoint node_type
        id = new uuid                   # real bodies carry no usable id
        registry[id] = {kind, SUBMITTED}
        try_admit(id)

    try_admit(id):
        if state != SUBMITTED: return False
        if kind over cap: HOLD, return False   # stays SUBMITTED
        state = DISPATCHED
        stamp body with id                  # workers echo it in receipts
        forward to worker queue
        return True

    on EVENT (completions queue, or broadcast):
        id = resolve(body)              # stamped id, else unknown
        if unknown or already terminal:
            duplicates += 1; return     # replays change nothing, ever
        state = terminal                # FINISHED or FAILED
        for held, oldest first: try_admit  # freed capacity releases holds

Registry states: SUBMITTED (parked) -> DISPATCHED -> FINISHED | FAILED.
Only completions move records forward; only the caps gate admission.
"""

from __future__ import annotations

import logging
import typing as t
import uuid

import kiwipy
from aiida.engine.processes.communications import (
    CONTINUE_TASK,
    CREATE_TASK,
    LAUNCH_TASK,
    PID_KEY,
    PROCESS_CLASS_KEY,
    TASK_ARGS,
    TASK_KEY,
    RemoteProcessThreadController,
)

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

#: Name of the broker task queue carrying completion receipts to the scheduler.
#: Unlike broadcasts (best-effort observability), this queue is durable: receipts
#: wait here while the scheduler is down and are redelivered until acknowledged,
#: so the registry cannot strand on a lost event. Both channels feed the same
#: idempotent bookkeeping, so a receipt arriving twice (once each way) applies once.
SCHEDULER_COMPLETIONS = 'scheduler-completions'

#: Terminal states a completion receipt may report.
TERMINAL_STATES = ('FINISHED', 'FAILED')


#: Process kinds the scheduler distinguishes for throttling.
KIND_UNKNOWN = 'unknown'
KIND_PROCESS = 'process'
KIND_WORKCHAIN = 'workchain'
KIND_CALCJOB = 'calcjob'
#: Workgraph tasks are identified from node metadata or an explicit registry;
#: the scheduler does not import their process implementation.
KIND_WORKGRAPH = 'workgraph'


def process_kind(body: t.Any, loader: t.Any | None = None, registry: dict[str, str] | None = None) -> str:
    """Classify a launch/create task body without necessarily loading its class.

    Resolution order: an explicit ``registry`` of identifier (or identifier
    prefix) to kind wins — deterministic, no imports, auditable, and the only
    correct answer for user code whose import path reveals nothing (even the
    base ``CalcJob`` identifies as a bare ``module:Class`` path). Otherwise the
    named class is loaded and checked against ``CalcJob``/``WorkChain``.
    Anything unresolvable reads ``'unknown'``. Never raises.

    :param loader: object loader override (tests); defaults to the global loader.
    :param registry: optional ``{identifier-or-prefix: kind}`` mapping.
    """
    identifier = None
    if isinstance(body, dict):
        task = body.get(TASK_KEY)
        if task in (LAUNCH_TASK, CREATE_TASK):
            args = body.get(TASK_ARGS) or {}
            identifier = args.get(PROCESS_CLASS_KEY) if isinstance(args, dict) else None
    if not identifier:
        return KIND_UNKNOWN
    for known_id, kind in (registry or {}).items():
        if identifier == known_id or identifier.startswith(known_id):
            return kind
    try:
        from aiida.common import loaders

        process_class = (loader or loaders.get_object_loader()).load_object(identifier)
        from aiida.engine import WorkChain
        from aiida.engine.processes.calcjobs.calcjob import CalcJob

        if not isinstance(process_class, type):
            return KIND_UNKNOWN
        if issubclass(process_class, CalcJob):
            return KIND_CALCJOB
        if issubclass(process_class, WorkChain):
            return KIND_WORKCHAIN
        return KIND_PROCESS
    except Exception:
        _LOGGER.debug('Could not identify process class %r.', identifier)
        return KIND_UNKNOWN


class Scheduler:
    """Gate process submissions before they reach workers.

    The scheduler subscribes to :data:`SCHEDULER_QUEUE`, admits each submitted
    process task and forwards it to the worker queue through its owned
    controller. It owns its communicator (created behind
    :meth:`create_communicator`) and shares no state with the broker beyond
    broker messages.

    The controller is composed, not inherited: a scheduler *uses* submission
    vocabulary for the forwarding path, it *is not* a controller. This keeps
    the scheduler's public surface narrow as admission policy grows.
    """

    def __init__(
        self,
        router_endpoint: str | None = None,
        communicator: kiwipy.Communicator | None = None,
        client_id: str = 'scheduler',
        max_in_flight_per_kind: dict[str, int] | None = None,
        loader: t.Any | None = None,
        node_loader: t.Callable[[int], t.Any] | None = None,
        kind_by_identifier: dict[str, str] | None = None,
    ):
        """Create the scheduler.

        :param router_endpoint: broker endpoint used when creating the communicator.
        :param communicator: an existing communicator, used as-is (mainly for tests).
        :param client_id: scheduler identity on the broker.
        :param max_in_flight_per_kind: concurrency caps by process kind, e.g.
            ``{'calcjob': 10}``. Tasks beyond a cap are held until completions
            release capacity. ``None`` (default) admits everything: caps only
            make sense once workers announce completions (see
            ``COMPLETED_SUBJECT``), otherwise held tasks would wait forever.
        :param loader: object loader override for launch classification (tests).
        :param node_loader: callable mapping a pid to its node, for continue
            classification. Defaults to a lazy ``aiida.orm.load_node``; override
            in tests to avoid storage I/O.
        :param kind_by_identifier: explicit ``{identifier-or-prefix: kind}``
            registry consulted before loading launch classes and against a
            continued node's ``process_type``. Deterministic and import-free;
            the right home for operator-known process types.
        """
        msg = 'Provide either `router_endpoint` or `communicator`.'
        if (router_endpoint is None) == (communicator is None):
            raise ValueError(msg)
        self.router_endpoint = router_endpoint
        self.client_id = client_id
        self._communicator = communicator if communicator is not None else self.create_communicator()
        self._delivery = RemoteProcessThreadController(self._communicator)
        self._caps = dict(max_in_flight_per_kind or {})
        self._loader = loader
        self._node_loader = node_loader
        self._kind_registry = kind_by_identifier
        # Lifecycle registry: scheduler-assigned id -> record. Real task bodies
        # carry no usable id, so the scheduler stamps one on admission and
        # workers echo it in completion announcements.
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
        communicator.add_task_subscriber(
            self._on_completion_task,
            identifier=f'{self.client_id}-completions',
            queue=SCHEDULER_COMPLETIONS,
        )

    def stop(self) -> None:
        """Close the communicator."""
        communicator = self._communicator
        if communicator is not None:
            communicator.close()

    def _kind_from_pid(self, pid: t.Any) -> str:
        """Classify a continue-task pid by loading its node.

        The node metadata records both its type and process identifier. An
        explicit kind registry can therefore classify custom process types,
        while built-in node types identify CalcJobs and WorkChains. Any lookup
        failure reads ``'unknown'`` — classification must never block admission.
        """
        if not isinstance(pid, int) or isinstance(pid, bool):
            return KIND_UNKNOWN
        try:
            loader = self._node_loader
            if loader is None:
                from aiida.orm import load_node

                loader = load_node
            node = loader(pid)
        except Exception:
            _LOGGER.debug('Could not load node for pid %r.', pid)
            return KIND_UNKNOWN
        process_type = getattr(node, 'process_type', None)
        if isinstance(process_type, str):
            for identifier, kind in (self._kind_registry or {}).items():
                if process_type == identifier or process_type.startswith(identifier):
                    return kind
        node_type = getattr(node, 'node_type', '') or ''
        if '.calculation.calcjob.' in node_type:
            return KIND_CALCJOB
        if '.workflow.workgraph.' in node_type:
            return KIND_WORKGRAPH
        if '.workflow.workchain.' in node_type:
            return KIND_WORKCHAIN
        if node_type.startswith('process.') or '.process.' in node_type:
            return KIND_PROCESS
        return KIND_UNKNOWN

    def _process_kind(self, body: t.Any) -> str:
        """Classify a submitted body: launch/create by identifier, continue by pid."""
        if not isinstance(body, dict):
            return KIND_UNKNOWN
        if body.get(TASK_KEY) == CONTINUE_TASK:
            args = body.get(TASK_ARGS) or {}
            pid = args.get(PID_KEY) if isinstance(args, dict) else None
            return self._kind_from_pid(pid)
        return process_kind(body, loader=self._loader, registry=self._kind_registry)

    def _on_submitted(self, comm: kiwipy.Communicator, body: t.Any) -> str | None:
        """Register one submitted process task and admit it if capacity allows."""
        # Fires for anything routed to the scheduler queue — today only explicit
        # opt-in submitters (a runner constructed with the scheduler queue,
        # scripts, tests). Default daemon submissions bypass the scheduler
        # entirely until their runners are configured the same way. Runs on the
        # communicator's loop thread; registry updates and at most one forward,
        # never blocks. Returns the scheduler-assigned id (mainly for tests).
        kind = self._process_kind(body)
        task_id = uuid.uuid4().hex
        _LOGGER.info('Scheduler received %s submission task_id=%s.', kind, task_id)
        record = {'state': 'SUBMITTED', 'kind': kind, 'body': body}
        self._tasks[task_id] = record
        self._try_admit(task_id)
        return task_id

    def _try_admit(self, task_id: str) -> bool:
        """Dispatch a submitted task if its kind has capacity."""
        record = self._tasks[task_id]
        if record['state'] != 'SUBMITTED':
            return False
        kind = record['kind']
        cap = self._caps.get(kind)
        if cap is not None and self.in_flight_for(kind) >= cap:
            _LOGGER.info('Scheduler holding %s task_id=%s at cap %d.', kind, task_id, cap)
            return False
        record['state'] = 'DISPATCHED'
        stamped = dict(record['body']) if isinstance(record['body'], dict) else record['body']
        if isinstance(stamped, dict):
            stamped['scheduler_task_id'] = task_id
        self._delivery.task_send(stamped, no_reply=True)
        _LOGGER.info('Scheduler admitted task_id=%s to worker queue (in_flight=%d).', task_id, self.in_flight)
        return True

    def _release_held(self) -> None:
        """Admit held tasks, oldest first, after capacity freed up."""
        for task_id, record in list(self._tasks.items()):
            if record['state'] == 'SUBMITTED':
                self._try_admit(task_id)

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
        else:
            return

    def _on_completion_task(self, comm: kiwipy.Communicator, body: t.Any) -> None:
        """Advance the registry from a durable completion receipt.

        Receipts look like ``{'scheduler_task_id': ..., 'terminal': ...}``.
        Returning (and thus acknowledging) only after bookkeeping means a
        receipt is never lost between delivery and recording: redelivery just
        replays an idempotent update. Malformed receipts are ignored.
        """
        terminal = body.get('terminal') if isinstance(body, dict) else None
        if terminal not in TERMINAL_STATES:
            _LOGGER.debug('Scheduler ignored malformed completion receipt %r.', body)
            return None
        self._complete(body, terminal=terminal)
        return None

    def _complete(self, body: t.Any, terminal: str) -> str | None:
        """Record a completion; return the transitioned id, if any."""
        task_id = body.get('scheduler_task_id') if isinstance(body, dict) else None
        record = self._tasks.get(task_id) if isinstance(task_id, str) else None
        if record is None or record['state'] in {'FINISHED', 'FAILED'}:
            self._duplicates += 1
            _LOGGER.info('Scheduler ignored duplicate completion task_id=%s.', task_id)
            return None
        record['state'] = terminal
        _LOGGER.info('Scheduler recorded task_id=%s -> %s (in_flight=%d).', task_id, terminal, self.in_flight)
        self._release_held()
        return task_id

    @property
    def in_flight(self) -> int:
        """Return the number of dispatched tasks without a terminal state."""
        return sum(1 for record in self._tasks.values() if record['state'] == 'DISPATCHED')

    def in_flight_for(self, kind: str) -> int:
        """Return the in-flight count for one process kind."""
        return sum(1 for record in self._tasks.values() if record['kind'] == kind and record['state'] == 'DISPATCHED')

    @property
    def process_counts(self) -> dict[str, int]:
        """Return dispatched-process counts for scheduler-level categories.

        Only CalcJobs and WorkGraphs receive dedicated categories. Every other
        process type is counted as ``'other'``. Workgraph identification uses
        only task metadata and the optional ``kind_by_identifier`` registry.
        """
        counts = {KIND_CALCJOB: 0, KIND_WORKGRAPH: 0, 'other': 0}
        for record in self._tasks.values():
            if record['state'] != 'DISPATCHED':
                continue
            kind = record['kind']
            counts[kind if kind in counts else 'other'] += 1
        return counts

    @property
    def duplicates(self) -> int:
        """Return the number of duplicate or unknown completions seen."""
        return self._duplicates
