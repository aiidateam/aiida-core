###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``aiida.brokers.zeromq.communicator.ZeromqCommunicator``."""

from __future__ import annotations

import time
from concurrent.futures import Future

import kiwipy
import pytest

from aiida.brokers.zeromq.communicator import ZeromqCommunicator


class TestZeromqCommunicatorLifecycle:
    """Tests for communicator initialization and lifecycle."""

    def test_init(self, zeromq_broker_server):
        """Test communicator initialization."""
        communicator = ZeromqCommunicator(router_endpoint=zeromq_broker_server.router_endpoint)
        communicator.start()

        try:
            assert communicator.is_closed() is False
        finally:
            communicator.close()

        assert communicator.is_closed() is True

    def test_context_manager(self, zeromq_broker_server):
        """Test communicator as context manager."""
        with ZeromqCommunicator(router_endpoint=zeromq_broker_server.router_endpoint) as communicator:
            assert communicator.is_closed() is False

        assert communicator.is_closed() is True

    def test_close_idempotent(self, zeromq_broker_server):
        """Test close is idempotent."""
        comm = ZeromqCommunicator(router_endpoint=zeromq_broker_server.router_endpoint)
        comm.start()
        comm.close()
        comm.close()  # should not raise
        assert comm.is_closed()

    def test_ensure_open_raises_when_closed(self):
        """Test _ensure_open raises when communicator is closed."""
        comm = ZeromqCommunicator(router_endpoint='ipc:///tmp/fake')
        with pytest.raises(RuntimeError, match='closed'):
            comm.task_send({'x': 1})


class TestZeromqCommunicatorMessaging:
    """Tests for communicator messaging operations with a real zeromq_broker."""

    @pytest.fixture
    def zeromq_broker_and_comm(self, zeromq_broker_server):
        comm = ZeromqCommunicator(router_endpoint=zeromq_broker_server.router_endpoint)
        comm.start()

        yield zeromq_broker_server, comm

        comm.close()

    def test_task_send_no_reply(self, zeromq_broker_and_comm):
        """Test task_send with no_reply=True returns None."""
        _, comm = zeromq_broker_and_comm
        result = comm.task_send({'cmd': 'test'}, no_reply=True)
        assert result is None

    def test_task_send_with_reply(self, zeromq_broker_and_comm):
        """Test task_send returns a Future."""
        _, comm = zeromq_broker_and_comm
        future = comm.task_send({'cmd': 'test'}, no_reply=False)
        assert isinstance(future, Future)

    def test_add_remove_task_subscriber(self, zeromq_broker_and_comm):
        """Test task subscriber management."""
        _, comm = zeromq_broker_and_comm
        ident = comm.add_task_subscriber(lambda c, t: None, identifier='test-worker')
        assert ident == 'test-worker'
        comm.remove_task_subscriber('test-worker')

    def test_rpc_send(self, zeromq_broker_and_comm):
        """Test rpc_send returns a Future."""
        _, comm = zeromq_broker_and_comm
        future = comm.rpc_send('some-recipient', {'action': 'ping'})
        assert isinstance(future, Future)

    def test_add_remove_rpc_subscriber(self, zeromq_broker_and_comm):
        """Test RPC subscriber management."""
        _, comm = zeromq_broker_and_comm
        ident = comm.add_rpc_subscriber(lambda c, m: 'ok', identifier='my-rpc')
        assert ident == 'my-rpc'
        comm.remove_rpc_subscriber('my-rpc')

    def test_duplicate_rpc_subscriber(self, zeromq_broker_and_comm):
        """Test duplicate RPC subscriber raises."""
        _, comm = zeromq_broker_and_comm
        comm.add_rpc_subscriber(lambda c, m: None, identifier='dup')
        with pytest.raises(kiwipy.DuplicateSubscriberIdentifier):
            comm.add_rpc_subscriber(lambda c, m: None, identifier='dup')

    def test_broadcast_send(self, zeromq_broker_and_comm):
        """Test broadcast_send returns True."""
        _, comm = zeromq_broker_and_comm
        result = comm.broadcast_send(body='hello', subject='test.subject')
        assert result is True

    def test_add_remove_broadcast_subscriber(self, zeromq_broker_and_comm):
        """Test broadcast subscriber management."""
        _, comm = zeromq_broker_and_comm
        ident = comm.add_broadcast_subscriber(lambda c, b, s, subj, cid: None, identifier='my-bcast')
        assert ident == 'my-bcast'
        comm.remove_broadcast_subscriber('my-bcast')


class TestZeromqCommunicatorRoundTrip:
    """Integration tests for full task, RPC, and broadcast round-trips."""

    @pytest.fixture
    def sender_and_worker(self, zeromq_broker_server):
        sender = ZeromqCommunicator(router_endpoint=zeromq_broker_server.router_endpoint, client_id='sender')
        sender.start()

        worker = ZeromqCommunicator(router_endpoint=zeromq_broker_server.router_endpoint, client_id='worker')
        worker.start()

        yield zeromq_broker_server, sender, worker

        worker.close()
        sender.close()

    def test_task_round_trip(self, sender_and_worker):
        """Test task send gets immediate zeromq_broker acknowledgment.

        The zeromq broker sends an immediate TASK_RESPONSE when the task is queued
        (matching RabbitMQ publisher-confirm semantics).  The worker processes
        the task independently.
        """
        _, sender, worker = sender_and_worker

        worker.add_task_subscriber(lambda comm, body: body.get('x', 0) * 2, identifier='worker')
        time.sleep(0.5)

        future = sender.task_send({'x': 21})
        assert future is not None

        # The sender's Future resolves with the zeromq_broker's acceptance, not the worker's result
        result = future.result(timeout=5.0)
        assert result.result() is True

    def test_rpc_round_trip(self, sender_and_worker):
        """Test full RPC send -> subscribe -> handle -> response cycle."""
        _, sender, worker = sender_and_worker

        def handle_rpc(comm, msg):
            return f'echo: {msg}'

        worker.add_rpc_subscriber(handle_rpc, identifier='echo-service')
        time.sleep(0.5)

        future = sender.rpc_send('echo-service', 'hello')
        result = future.result(timeout=5.0)
        assert result == 'echo: hello'

    def test_broadcast_round_trip(self, sender_and_worker):
        """Test broadcast send and receive."""
        _, sender, worker = sender_and_worker
        received = []

        def on_broadcast(comm, body, bsender, subject, cid):
            received.append((body, subject))

        worker.add_broadcast_subscriber(on_broadcast, identifier='listener')
        worker.add_task_subscriber(lambda c, t: None, identifier='worker')
        time.sleep(0.5)

        sender.broadcast_send(body='ping', subject='test.ping')
        time.sleep(1.0)

        assert len(received) >= 1
        assert received[0] == ('ping', 'test.ping')

    def test_task_with_deferred_future(self, sender_and_worker):
        """Test task send with deferred handler gets immediate zeromq_broker ack."""
        _, sender, worker = sender_and_worker

        def handle_task(comm, body):
            f = Future()
            f.set_result(body.get('val', 0) + 100)
            return f

        worker.add_task_subscriber(handle_task, identifier='worker')
        time.sleep(0.5)

        future = sender.task_send({'val': 5})
        # Sender gets immediate zeromq_broker acknowledgment, not the worker's deferred result
        result = future.result(timeout=5.0)
        assert result.result() is True

    def test_rpc_with_deferred_future(self, sender_and_worker):
        """Test RPC handler returning a Future."""
        _, sender, worker = sender_and_worker

        def handle_rpc(comm, msg):
            f = Future()
            f.set_result(f'deferred: {msg}')
            return f

        worker.add_rpc_subscriber(handle_rpc, identifier='deferred-svc')
        time.sleep(0.5)

        future = sender.rpc_send('deferred-svc', 'test')
        result = future.result(timeout=5.0)
        assert result == 'deferred: test'

    def test_rpc_subscriber_exception(self, sender_and_worker):
        """Test RPC handler that raises an exception propagates error."""
        _, sender, worker = sender_and_worker

        def handle_rpc(comm, msg):
            raise ValueError('handler error')

        worker.add_rpc_subscriber(handle_rpc, identifier='error-svc')
        time.sleep(0.5)

        future = sender.rpc_send('error-svc', 'test')
        with pytest.raises(Exception, match='handler error'):
            future.result(timeout=5.0)
