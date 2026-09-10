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
    assert ('scheduler-completions', 'scheduler-completions') in communicator.subscriptions
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
    task_id = scheduler._on_submitted(communicator, body)
    assert isinstance(task_id, str)
    assert communicator.sent == [('default', {**body, 'scheduler_task_id': task_id})]
    assert scheduler.in_flight == 1


def test_completion_lifecycle(scheduler, communicator):
    """Test completions move registry records to terminal states."""
    from aiida.scheduler import COMPLETED_SUBJECT, FAILED_SUBJECT

    scheduler.start()
    first = scheduler._on_submitted(communicator, {'task': 'launch'})
    second = scheduler._on_submitted(communicator, {'task': 'launch'})
    assert scheduler.in_flight == 2

    scheduler._on_broadcast(communicator, {'scheduler_task_id': first}, 'worker', COMPLETED_SUBJECT, None)
    assert scheduler.in_flight == 1
    assert scheduler.duplicates == 0

    # Duplicate delivery changes nothing but counts.
    scheduler._on_broadcast(communicator, {'scheduler_task_id': first}, 'worker', COMPLETED_SUBJECT, None)
    assert scheduler.in_flight == 1
    assert scheduler.duplicates == 1

    # Unknown task ids and subjects never create state.
    scheduler._on_broadcast(communicator, {'scheduler_task_id': 'ghost'}, 'worker', COMPLETED_SUBJECT, None)
    scheduler._on_broadcast(communicator, {'scheduler_task_id': second}, 'worker', 'unrelated.subject', None)
    assert scheduler.in_flight == 1
    assert scheduler.duplicates == 2

    scheduler._on_broadcast(communicator, {'scheduler_task_id': second}, 'worker', FAILED_SUBJECT, None)
    assert scheduler.in_flight == 0


def test_durable_receipt_advances_registry(scheduler, communicator):
    """Test completion receipts from the durable queue advance terminal states."""
    scheduler.start()
    first = scheduler._on_submitted(communicator, {'task': 'launch'})
    assert scheduler.in_flight == 1

    scheduler._on_completion_task(communicator, {'scheduler_task_id': first, 'terminal': 'FINISHED'})
    assert scheduler.in_flight == 0
    assert scheduler.duplicates == 0

    # Missing terminals and non-dicts are ignored without touching the registry.
    scheduler._on_completion_task(communicator, {'scheduler_task_id': first})
    scheduler._on_completion_task(communicator, 'not-a-dict')
    assert scheduler.in_flight == 0
    assert scheduler.duplicates == 0

    # A valid receipt for an unknown id is indistinguishable from a duplicate.
    scheduler._on_completion_task(communicator, {'no-id': True, 'terminal': 'FINISHED'})
    assert scheduler.duplicates == 1


def test_double_delivery_applies_once(scheduler, communicator):
    """Test the same receipt via queue and broadcast advances exactly once."""
    from aiida.scheduler import COMPLETED_SUBJECT

    scheduler.start()
    first = scheduler._on_submitted(communicator, {'task': 'launch'})
    receipt = {'scheduler_task_id': first, 'terminal': 'FINISHED'}
    scheduler._on_completion_task(communicator, dict(receipt))
    scheduler._on_broadcast(communicator, dict(receipt), 'worker', COMPLETED_SUBJECT, None)
    assert scheduler.in_flight == 0
    assert scheduler.duplicates == 1


def test_throttle_holds_and_releases(communicator):
    """Test per-kind caps hold excess submissions until completions free capacity."""
    from aiida.engine import WorkChain
    from aiida.engine.processes.calcjobs.calcjob import CalcJob
    from aiida.scheduler import COMPLETED_SUBJECT

    class MyCalc(CalcJob):
        pass

    class MyChain(WorkChain):
        pass

    class StubLoader:
        def load_object(self, identifier):
            return {'calc': MyCalc, 'chain': MyChain}[identifier]

    scheduler = Scheduler(communicator=communicator, max_in_flight_per_kind={'calcjob': 1}, loader=StubLoader())
    scheduler.start()
    calc_body = {'task': 'launch', 'args': {'process_class': 'calc'}}
    chain_body = {'task': 'launch', 'args': {'process_class': 'chain'}}
    first = scheduler._on_submitted(communicator, calc_body)
    second = scheduler._on_submitted(communicator, calc_body)
    scheduler._on_submitted(communicator, chain_body)
    # First calcjob and the (uncapped) workchain dispatch; second calcjob holds.
    assert [queue for queue, _ in communicator.sent] == ['default', 'default']
    assert scheduler.in_flight == 2
    assert scheduler.in_flight_for('calcjob') == 1

    scheduler._on_broadcast(communicator, {'scheduler_task_id': first}, 'worker', COMPLETED_SUBJECT, None)
    held = [body for _, body in communicator.sent][2]
    assert held['scheduler_task_id'] == second
    assert scheduler.in_flight == 2


def test_process_counts_group_dispatched_tasks(communicator):
    """Test scheduler process counts do not depend on process implementations."""
    scheduler = Scheduler(
        communicator=communicator,
        kind_by_identifier={'calc': 'calcjob', 'graph': 'workgraph'},
    )
    scheduler.start()
    calcjob = scheduler._on_submitted(communicator, {'task': 'launch', 'args': {'process_class': 'calc'}})
    workgraph = scheduler._on_submitted(communicator, {'task': 'launch', 'args': {'process_class': 'graph'}})
    scheduler._on_submitted(communicator, {'task': 'launch'})

    assert scheduler.process_counts == {'calcjob': 1, 'workgraph': 1, 'other': 1}

    scheduler._on_completion_task(communicator, {'scheduler_task_id': workgraph, 'terminal': 'FINISHED'})
    assert scheduler.process_counts == {'calcjob': 1, 'workgraph': 0, 'other': 1}

    scheduler._on_completion_task(communicator, {'scheduler_task_id': calcjob, 'terminal': 'FINISHED'})
    assert scheduler.process_counts == {'calcjob': 0, 'workgraph': 0, 'other': 1}


def test_process_kind_launch_body_loads_class():
    """Test launch bodies classify by loading the named process class."""
    from aiida.engine import WorkChain
    from aiida.engine.processes.calcjobs.calcjob import CalcJob
    from aiida.scheduler.scheduler import process_kind

    class MyChain(WorkChain):
        pass

    class MyCalc(CalcJob):
        pass

    class StubLoader:
        def __init__(self, mapping):
            self.mapping = mapping

        def load_object(self, identifier):
            return self.mapping[identifier]

    loader = StubLoader({'wc': MyChain, 'calc': MyCalc, 'plain': int})
    assert process_kind({'task': 'launch', 'args': {'process_class': 'wc'}}, loader=loader) == 'workchain'
    assert process_kind({'task': 'launch', 'args': {'process_class': 'calc'}}, loader=loader) == 'calcjob'
    assert process_kind({'task': 'create', 'args': {'process_class': 'plain'}}, loader=loader) == 'process'
    assert process_kind({'task': 'launch', 'args': {}}) == 'unknown'
    assert process_kind({'nope': True}) == 'unknown'
    assert process_kind(None) == 'unknown'

    def boom(identifier):
        raise ImportError(identifier)

    loader.load_object = boom
    assert process_kind({'task': 'launch', 'args': {'process_class': 'ghost'}}, loader=loader) == 'unknown'


def test_process_kind_registry_wins_without_loading():
    """Test the explicit registry answers without importing anything."""
    from aiida.scheduler.scheduler import KIND_CALCJOB, process_kind

    loaded = []

    class SpyLoader:
        def load_object(self, identifier):
            loaded.append(identifier)
            raise AssertionError('registry should have answered first')

    registry = {'my.pkg:MyCalc': KIND_CALCJOB, 'aiida.calculations:': KIND_CALCJOB}
    body = {'task': 'launch', 'args': {'process_class': 'my.pkg:MyCalc'}}
    assert process_kind(body, loader=SpyLoader(), registry=registry) == KIND_CALCJOB
    assert loaded == []
    entry_point = {'task': 'launch', 'args': {'process_class': 'aiida.calculations:arithmetic.add'}}
    assert process_kind(entry_point, loader=SpyLoader(), registry=registry) == KIND_CALCJOB


def test_process_kind_continue_body_loads_node():
    """Test continue bodies classify from checkpoint node metadata, not classes."""
    from types import SimpleNamespace

    from aiida.scheduler import Scheduler

    def node_loader(pid):
        return {
            1: SimpleNamespace(node_type='process.calculation.calcjob.CalcJobNode.'),
            2: SimpleNamespace(node_type='process.workflow.workchain.WorkChainNode.'),
            3: SimpleNamespace(node_type='process.workflow.WorkflowNode.'),
            4: SimpleNamespace(node_type='data.core.int.Int.'),
            5: SimpleNamespace(),
        }[pid]

    scheduler = Scheduler(communicator=FakeCommunicator(), node_loader=node_loader)
    submitted = scheduler._process_kind
    assert submitted({'task': 'continue', 'args': {'pid': 1}}) == 'calcjob'
    assert submitted({'task': 'continue', 'args': {'pid': 2}}) == 'workchain'
    assert submitted({'task': 'continue', 'args': {'pid': 3}}) == 'process'
    assert submitted({'task': 'continue', 'args': {'pid': 4}}) == 'unknown'
    assert submitted({'task': 'continue', 'args': {'pid': 5}}) == 'unknown'
    assert submitted({'task': 'continue', 'args': {'pid': 999}}) == 'unknown'
    assert submitted({'task': 'continue', 'args': {}}) == 'unknown'


def test_create_communicator_is_zeromq():
    """Test the default communicator factory builds a ZeroMQ communicator."""
    from aiida.brokers.zeromq.communicator import ZeromqCommunicator

    scheduler = Scheduler.__new__(Scheduler)
    scheduler.router_endpoint = 'ipc:///tmp/does-not-exist/router.sock'
    scheduler.client_id = 'scheduler'
    communicator = scheduler.create_communicator()
    assert isinstance(communicator, ZeromqCommunicator)
