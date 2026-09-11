###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""End-to-end submission through the scheduler queue.

Proves the production path with real broker messages and no mocks:
submitter controller (scheduler queue) -> broker -> ``Scheduler`` service ->
broker -> worker subscriber (default queue). Needs no profile, daemon, or
external services: the server runs in-process and communicators connect over
IPC.
"""

from __future__ import annotations

import tempfile
import threading
import time
from pathlib import Path

import pytest

from aiida.brokers.zeromq.communicator import ZeromqCommunicator
from aiida.brokers.zeromq.server import ZeromqBrokerServer
from aiida.engine.processes.communications import RemoteProcessThreadController
from aiida.scheduler import SCHEDULER_QUEUE, Scheduler


@pytest.fixture
def endpoint():
    """Run a live broker server in-process and yield its endpoint."""
    with tempfile.TemporaryDirectory(prefix='scheduler-fwd') as tmp:
        tmp_path = Path(tmp)
        server = ZeromqBrokerServer(storage_path=tmp_path / 's', sockets_path=tmp_path / 'k')
        server.start()
        thread = threading.Thread(target=server.run_forever, kwargs={'poll_timeout': 0.001}, daemon=True)
        thread.start()
        try:
            yield server.router_endpoint
        finally:
            server.stop()
            thread.join(timeout=5.0)


def _wait_until(predicate, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise TimeoutError('condition not met in time')


def test_submission_flows_through_scheduler(endpoint):
    """Test a task submitted to the scheduler queue reaches a default-queue worker."""
    scheduler = Scheduler(router_endpoint=endpoint)
    scheduler.start()

    worker_comm = ZeromqCommunicator(router_endpoint=endpoint, client_id='worker', task_prefetch_count=10)
    worker_comm.start()
    received: list = []
    worker_comm.add_task_subscriber(lambda comm, body: received.append(body) or {'ok': True})

    submitter_comm = ZeromqCommunicator(router_endpoint=endpoint, client_id='submitter')
    submitter_comm.start()
    controller = RemoteProcessThreadController(submitter_comm, task_queue=SCHEDULER_QUEUE)

    try:
        controller.task_send({'process': 'launch', 'x': 1}, no_reply=True)
        _wait_until(lambda: len(received) == 1)
        body = dict(received[0])
        assert body.pop('scheduler_task_id')
        assert body == {'process': 'launch', 'x': 1}
    finally:
        submitter_comm.close()
        worker_comm.close()
        scheduler.stop()


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
def test_submit_process_via_scheduler_queue_to_daemon(started_daemon_client):
    """Test a real process submitted through the scheduler queue runs on a daemon worker."""
    # NOTE: fixture order matters (mirrors test_control.py): the profile must be
    # cleaned *before* the daemon starts, otherwise ``reset_storage`` stops it.
    from aiida.engine import ProcessState
    from aiida.manage import get_manager
    from aiida.scheduler import SCHEDULER_QUEUE
    from tests.utils.processes import DummyProcess

    manager = get_manager()
    endpoint = manager.get_broker()._router_endpoint
    assert endpoint is not None

    scheduler = Scheduler(router_endpoint=endpoint)
    scheduler.start()
    runner = manager.create_runner(broker_submit=True, task_queue=SCHEDULER_QUEUE)
    try:
        node = runner.submit(DummyProcess)
        _wait_until(lambda: node.process_state is ProcessState.FINISHED, timeout=60.0)
        assert node.is_finished_ok
    finally:
        scheduler.stop()
        runner.close()


def test_default_queue_bypasses_scheduler(endpoint):
    """Test tasks sent without a queue still go straight to default workers."""
    received: list = []
    worker_comm = ZeromqCommunicator(router_endpoint=endpoint, client_id='worker', task_prefetch_count=10)
    worker_comm.start()
    worker_comm.add_task_subscriber(lambda comm, body: received.append(body) or {'ok': True})

    submitter_comm = ZeromqCommunicator(router_endpoint=endpoint, client_id='submitter')
    submitter_comm.start()
    try:
        # No scheduler running and no queue requested: direct delivery, as before.
        submitter_comm.task_send({'process': 'launch'}, no_reply=True)
        _wait_until(lambda: len(received) == 1)
        assert received == [{'process': 'launch'}]
    finally:
        submitter_comm.close()
        worker_comm.close()
