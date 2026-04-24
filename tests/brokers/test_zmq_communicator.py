###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``aiida.brokers.zmq.communicator.ZmqCommunicator``."""

from __future__ import annotations

import time
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import MagicMock, patch

import kiwipy
import pytest

from aiida.brokers.zmq import ZmqBroker
from aiida.brokers.zmq.communicator import ZmqCommunicator
from tests.conftest import start_zmq_broker, stop_zmq_broker


def _create_broker_with_base_path(base_path: Path) -> ZmqBroker:
    with patch('aiida.brokers.zmq.broker.get_broker_base_path', return_value=base_path):
        return ZmqBroker(MagicMock())


class TestZmqCommunicatorLifecycle:
    """Tests for communicator initialization and lifecycle."""

    def test_init(self, tmp_path):
        """Test communicator initialization."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zmq_broker(broker)

        try:
            communicator = ZmqCommunicator(router_endpoint=broker.router_endpoint)
            communicator.start()

            try:
                assert communicator.is_closed() is False
            finally:
                communicator.close()

            assert communicator.is_closed() is True
        finally:
            stop_zmq_broker(broker)

    def test_context_manager(self, tmp_path):
        """Test communicator as context manager."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zmq_broker(broker)

        try:
            with ZmqCommunicator(router_endpoint=broker.router_endpoint) as communicator:
                assert communicator.is_closed() is False

            assert communicator.is_closed() is True
        finally:
            stop_zmq_broker(broker)

    def test_close_idempotent(self, tmp_path):
        """Test close is idempotent."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zmq_broker(broker)

        try:
            comm = ZmqCommunicator(router_endpoint=broker.router_endpoint)
            comm.start()
            comm.close()
            comm.close()  # should not raise
            assert comm.is_closed()
        finally:
            stop_zmq_broker(broker)

    def test_ensure_open_raises_when_closed(self):
        """Test _ensure_open raises when communicator is closed."""
        comm = ZmqCommunicator(router_endpoint='ipc:///tmp/fake')
        with pytest.raises(RuntimeError, match='closed'):
            comm.task_send({'x': 1})


class TestZmqCommunicatorMessaging:
    """Tests for communicator messaging operations with a real broker."""

    @pytest.fixture
    def broker_and_comm(self, tmp_path):
        broker = _create_broker_with_base_path(tmp_path / 'broker')
        start_zmq_broker(broker)

        comm = ZmqCommunicator(router_endpoint=broker.router_endpoint)
        comm.start()

        yield broker, comm

        comm.close()
        stop_zmq_broker(broker)

    def test_task_send_no_reply(self, broker_and_comm):
        """Test task_send with no_reply=True returns None."""
        _, comm = broker_and_comm
        result = comm.task_send({'cmd': 'test'}, no_reply=True)
        assert result is None

    def test_task_send_with_reply(self, broker_and_comm):
        """Test task_send returns a Future."""
        _, comm = broker_and_comm
        future = comm.task_send({'cmd': 'test'}, no_reply=False)
        assert isinstance(future, Future)

    def test_add_remove_task_subscriber(self, broker_and_comm):
        """Test task subscriber management."""
        _, comm = broker_and_comm
        ident = comm.add_task_subscriber(lambda c, t: None, identifier='test-worker')
        assert ident == 'test-worker'
        comm.remove_task_subscriber('test-worker')

    def test_rpc_send(self, broker_and_comm):
        """Test rpc_send returns a Future."""
        _, comm = broker_and_comm
        future = comm.rpc_send('some-recipient', {'action': 'ping'})
        assert isinstance(future, Future)

    def test_add_remove_rpc_subscriber(self, broker_and_comm):
        """Test RPC subscriber management."""
        _, comm = broker_and_comm
        ident = comm.add_rpc_subscriber(lambda c, m: 'ok', identifier='my-rpc')
        assert ident == 'my-rpc'
        comm.remove_rpc_subscriber('my-rpc')

    def test_duplicate_rpc_subscriber(self, broker_and_comm):
        """Test duplicate RPC subscriber raises."""
        _, comm = broker_and_comm
        comm.add_rpc_subscriber(lambda c, m: None, identifier='dup')
        with pytest.raises(kiwipy.DuplicateSubscriberIdentifier):
            comm.add_rpc_subscriber(lambda c, m: None, identifier='dup')

    def test_broadcast_send(self, broker_and_comm):
        """Test broadcast_send returns True."""
        _, comm = broker_and_comm
        result = comm.broadcast_send(body='hello', subject='test.subject')
        assert result is True

    def test_add_remove_broadcast_subscriber(self, broker_and_comm):
        """Test broadcast subscriber management."""
        _, comm = broker_and_comm
        ident = comm.add_broadcast_subscriber(lambda c, b, s, subj, cid: None, identifier='my-bcast')
        assert ident == 'my-bcast'
        comm.remove_broadcast_subscriber('my-bcast')


class TestZmqCommunicatorRoundTrip:
    """Integration tests for full task, RPC, and broadcast round-trips."""

    @pytest.fixture
    def sender_and_worker(self, tmp_path):
        broker = _create_broker_with_base_path(tmp_path / 'broker')
        start_zmq_broker(broker)

        sender = ZmqCommunicator(router_endpoint=broker.router_endpoint, client_id='sender')
        sender.start()

        worker = ZmqCommunicator(router_endpoint=broker.router_endpoint, client_id='worker')
        worker.start()

        yield broker, sender, worker

        worker.close()
        sender.close()
        stop_zmq_broker(broker)

    def test_task_round_trip(self, sender_and_worker):
        """Test full task send -> subscribe -> handle -> response cycle."""
        _, sender, worker = sender_and_worker

        def handle_task(comm, body):
            return body.get('x', 0) * 2

        worker.add_task_subscriber(handle_task, identifier='worker')
        time.sleep(0.5)

        future = sender.task_send({'x': 21})
        assert future is not None

        result = future.result(timeout=5.0)
        assert result.result() == 42

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
        """Test task handler returning a Future (deferred ACK path)."""
        _, sender, worker = sender_and_worker

        def handle_task(comm, body):
            f = Future()
            f.set_result(body.get('val', 0) + 100)
            return f

        worker.add_task_subscriber(handle_task, identifier='worker')
        time.sleep(0.5)

        future = sender.task_send({'val': 5})
        result = future.result(timeout=5.0)
        assert result.result() == 105

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
