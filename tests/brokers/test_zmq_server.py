###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``aiida.brokers.zmq.server.ZmqBrokerServer``."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aiida.brokers.zmq.protocol import MessageType, decode_message, encode_message
from aiida.brokers.zmq.server import ZmqBrokerServer


class TestZmqBrokerServerInit:
    """Tests for ZmqBrokerServer initialization and lifecycle."""

    def test_init(self, tmp_path):
        """Test server initialization."""
        storage_path = tmp_path / 'storage'
        sockets_path = tmp_path / 'sockets'

        server = ZmqBrokerServer(storage_path=storage_path, sockets_path=sockets_path)
        assert server.storage_path == storage_path
        assert server.sockets_path == sockets_path

    def test_start_stop(self):
        """Test starting and stopping the server."""
        with tempfile.TemporaryDirectory(prefix='zmq') as tmp:
            tmp_path = Path(tmp)
            server = ZmqBrokerServer(storage_path=tmp_path / 's', sockets_path=tmp_path / 'k')
            server.start()

            try:
                status = server.get_status()
                assert 'pending_tasks' in status
                assert 'processing_tasks' in status
            finally:
                server.stop()

    def test_start_idempotent(self):
        """Test start is idempotent."""
        with tempfile.TemporaryDirectory(prefix='zmq') as tmp:
            tmp_path = Path(tmp)
            server = ZmqBrokerServer(storage_path=tmp_path / 's', sockets_path=tmp_path / 'k')
            server.start()
            try:
                server.start()  # should be no-op
                assert server.is_running
            finally:
                server.stop()

    def test_stop_idempotent(self, tmp_path):
        """Test stop when not running is no-op."""
        server = ZmqBrokerServer(storage_path=tmp_path / 's', sockets_path=tmp_path / 'k')
        server.stop()  # should not raise

    def test_run_once_not_running(self, tmp_path):
        """Test run_once when not running returns False."""
        server = ZmqBrokerServer(storage_path=tmp_path / 's', sockets_path=tmp_path / 'k')
        assert server.run_once() is False

    def test_get_status(self, tmp_path):
        """Test get_status returns expected keys."""
        with tempfile.TemporaryDirectory(prefix='zmq') as tmp:
            tmp_path = Path(tmp)
            server = ZmqBrokerServer(storage_path=tmp_path / 's', sockets_path=tmp_path / 'k')
            server.start()

            try:
                status = server.get_status()
                assert status['pending_tasks'] == 0
                assert status['processing_tasks'] == 0
            finally:
                server.stop()


class TestZmqBrokerServerMessageHandling:
    """Tests for server message handling paths.

    Calls handler methods directly to test dispatch logic without real sockets.
    """

    @pytest.fixture
    def server(self, tmp_path):
        storage_path = tmp_path / 'storage'
        sockets_path = tmp_path / 'sockets'
        return ZmqBrokerServer(storage_path=storage_path, sockets_path=sockets_path)

    # --- Task handling ---

    def test_handle_task_no_reply(self, server):
        """Test _handle_task queues a task with no_reply=True (no ack sent)."""
        server._send_to_client = MagicMock()
        msg = {
            'type': MessageType.TASK.value,
            'id': 'task-001',
            'sender': 'client-1',
            'body': {'cmd': 'run'},
            'no_reply': True,
        }
        server._handle_task(b'worker-1', msg)

        assert server._task_queue.size() == 1
        # no_reply=True means no immediate acknowledgment sent
        server._send_to_client.assert_not_called()

    def test_handle_task_with_reply(self, server):
        """Test _handle_task sends immediate acknowledgment when reply expected."""
        server._send_to_client = MagicMock()
        msg = {
            'type': MessageType.TASK.value,
            'id': 'task-002',
            'sender': 'client-1',
            'body': None,
            'no_reply': False,
        }
        server._handle_task(b'client-1', msg)

        # Broker sends immediate TASK_RESPONSE acknowledgment
        server._send_to_client.assert_called_once()
        ack_msg = server._send_to_client.call_args[0][1]
        assert ack_msg['type'] == MessageType.TASK_RESPONSE.value
        assert ack_msg['task_id'] == 'task-002'
        assert ack_msg['result'] is True

    def test_handle_task_response_discarded(self, server):
        """Test _handle_task_response discards worker responses (sender already acked)."""
        msg = {
            'type': MessageType.TASK_RESPONSE.value,
            'task_id': 'task-100',
            'result': 'done',
        }
        # Should not raise — worker responses are simply logged and discarded
        server._handle_task_response(b'worker-1', msg)

    def test_handle_task_ack(self, server):
        """Test _handle_task_ack removes task and marks worker available."""
        server._task_queue.push('task-200', {'body': 'x'})
        server._task_queue.pop()
        server._task_worker_assignments['task-200'] = b'worker-1'

        msg = {'type': MessageType.TASK_ACK.value, 'task_id': 'task-200'}
        server._handle_task_ack(b'worker-1', msg)

        assert server._task_queue.processing_count() == 0
        assert 'task-200' not in server._task_worker_assignments
        assert b'worker-1' in server._available_workers

    def test_handle_task_nack(self, server):
        """Test _handle_task_nack requeues task and marks worker available."""
        server._task_queue.push('task-300', {'body': 'x'})
        server._task_queue.pop()

        msg = {'type': MessageType.TASK_NACK.value, 'task_id': 'task-300'}
        server._handle_task_nack(b'worker-1', msg)

        assert server._task_queue.size() == 1  # requeued
        assert b'worker-1' in server._available_workers

    # --- RPC handling ---

    def test_handle_rpc_missing_recipient(self, server):
        """Test _handle_rpc with no recipient sends error response."""
        server._send_to_client = MagicMock()
        msg = {'type': MessageType.RPC.value, 'id': 'rpc-1'}
        server._handle_rpc(b'client', msg)

        call_msg = server._send_to_client.call_args[0][1]
        assert call_msg['type'] == MessageType.RPC_RESPONSE.value
        assert 'error' in call_msg

    def test_handle_rpc_recipient_not_found(self, server):
        """Test _handle_rpc with unknown recipient sends error response."""
        server._send_to_client = MagicMock()
        msg = {'type': MessageType.RPC.value, 'id': 'rpc-2', 'recipient': 'nobody'}
        server._handle_rpc(b'client', msg)

        call_msg = server._send_to_client.call_args[0][1]
        assert 'not found' in call_msg['error'].lower()

    def test_handle_rpc_success(self, server):
        """Test _handle_rpc with valid recipient forwards message."""
        server._rpc_subscribers['worker-proc'] = b'worker-1'
        server._send_to_client = MagicMock()

        msg = {'type': MessageType.RPC.value, 'id': 'rpc-3', 'recipient': 'worker-proc', 'body': 'ping'}
        server._handle_rpc(b'client', msg)

        assert 'rpc-3' in server._pending_rpc_responses
        server._send_to_client.assert_called_once_with(b'worker-1', msg)

    def test_handle_rpc_response(self, server):
        """Test _handle_rpc_response routes back to original caller."""
        server._pending_rpc_responses['rpc-10'] = (b'client-1', time.time())
        server._send_to_client = MagicMock()

        msg = {'type': MessageType.RPC_RESPONSE.value, 'rpc_id': 'rpc-10', 'result': 42}
        server._handle_rpc_response(b'worker', msg)

        server._send_to_client.assert_called_once_with(b'client-1', msg)

    def test_handle_rpc_response_missing_rpc_id(self, server):
        """Test _handle_rpc_response without rpc_id is a no-op."""
        server._send_to_client = MagicMock()
        msg = {'type': MessageType.RPC_RESPONSE.value}
        server._handle_rpc_response(b'worker', msg)
        server._send_to_client.assert_not_called()

    def test_handle_rpc_response_no_pending(self, server):
        """Test _handle_rpc_response with no matching pending is a no-op."""
        server._send_to_client = MagicMock()
        msg = {'type': MessageType.RPC_RESPONSE.value, 'rpc_id': 'unknown'}
        server._handle_rpc_response(b'worker', msg)
        server._send_to_client.assert_not_called()

    def test_send_rpc_error(self, server):
        """Test _send_rpc_error sends error response."""
        server._send_to_client = MagicMock()
        server._send_rpc_error(b'client', 'rpc-99', 'Something broke')

        call_msg = server._send_to_client.call_args[0][1]
        assert call_msg['type'] == MessageType.RPC_RESPONSE.value
        assert call_msg['error'] == 'Something broke'

    # --- Broadcast handling ---

    def test_handle_broadcast(self, server):
        """Test _handle_broadcast fans out to all subscribers."""
        server._task_subscribers['w1'] = b'worker-1'
        server._rpc_subscribers['w2'] = b'worker-2'
        server._send_to_client = MagicMock()

        msg = {'type': MessageType.BROADCAST.value, 'body': 'hello', 'subject': 'test'}
        server._handle_broadcast(b'sender', msg)

        assert server._send_to_client.call_count == 2

    # --- Subscription handling ---

    def test_handle_subscribe_task(self, server):
        """Test _handle_subscribe_task registers subscriber and marks worker available."""
        msg = {'type': MessageType.SUBSCRIBE_TASK.value, 'identifier': 'worker-1', 'sender': 's'}
        server._handle_subscribe_task(b'w1-identity', msg)

        assert 'worker-1' in server._task_subscribers
        assert b'w1-identity' in server._available_workers

    def test_handle_subscribe_task_missing_identifier(self, server):
        """Test _handle_subscribe_task with no identifier is a no-op."""
        msg = {'type': MessageType.SUBSCRIBE_TASK.value}
        server._handle_subscribe_task(b'w', msg)
        assert len(server._task_subscribers) == 0

    def test_handle_subscribe_rpc(self, server):
        """Test _handle_subscribe_rpc registers subscriber."""
        msg = {'type': MessageType.SUBSCRIBE_RPC.value, 'identifier': 'rpc-handler'}
        server._handle_subscribe_rpc(b'handler-id', msg)
        assert 'rpc-handler' in server._rpc_subscribers

    def test_handle_subscribe_rpc_missing_identifier(self, server):
        """Test _handle_subscribe_rpc with no identifier is a no-op."""
        msg = {'type': MessageType.SUBSCRIBE_RPC.value}
        server._handle_subscribe_rpc(b'h', msg)
        assert len(server._rpc_subscribers) == 0

    def test_handle_unsubscribe_task(self, server):
        """Test _handle_unsubscribe_task removes subscriber."""
        server._task_subscribers['w1'] = b'w1-id'
        msg = {'type': MessageType.UNSUBSCRIBE_TASK.value, 'identifier': 'w1'}
        server._handle_unsubscribe_task(b'w1-id', msg)
        assert 'w1' not in server._task_subscribers

    def test_handle_unsubscribe_rpc(self, server):
        """Test _handle_unsubscribe_rpc removes subscriber."""
        server._rpc_subscribers['r1'] = b'r1-id'
        msg = {'type': MessageType.UNSUBSCRIBE_RPC.value, 'identifier': 'r1'}
        server._handle_unsubscribe_rpc(b'r1-id', msg)
        assert 'r1' not in server._rpc_subscribers

    # --- Task dispatch ---

    def test_dispatch_pending_tasks(self, server):
        """Test _dispatch_pending_tasks sends task to available worker."""
        server._task_subscribers['w1'] = b'worker-1'
        server._available_workers.append(b'worker-1')
        server._task_queue.push('task-500', {'body': 'data', 'no_reply': True})

        server._send_to_client = MagicMock()
        server._dispatch_pending_tasks()

        server._send_to_client.assert_called_once()
        call_msg = server._send_to_client.call_args[0][1]
        assert call_msg['id'] == 'task-500'
        assert 'task-500' in server._task_worker_assignments

    def test_dispatch_unsubscribed_worker_skipped(self, server):
        """Test dispatch skips workers that unsubscribed."""
        server._available_workers.append(b'dead-worker')
        server._task_queue.push('task-600', {'body': 'data'})

        server._send_to_client = MagicMock()
        server._dispatch_pending_tasks()

        server._send_to_client.assert_not_called()
        assert server._task_queue.size() == 1

    def test_dispatch_empty_queue_returns_worker(self, server):
        """Test dispatch with empty queue does not send."""
        server._task_subscribers['w1'] = b'worker-1'
        server._available_workers.append(b'worker-1')

        server._send_to_client = MagicMock()
        server._dispatch_pending_tasks()
        server._send_to_client.assert_not_called()

    # --- Worker management ---

    def test_remove_dead_worker(self, server):
        """Test _remove_dead_worker cleans all registries."""
        dead_id = b'dead-worker'
        server._task_subscribers['sub1'] = dead_id
        server._rpc_subscribers['rpc1'] = dead_id
        server._available_workers.append(dead_id)
        server._task_worker_assignments['task-700'] = dead_id

        server._task_queue.push('task-700', {'body': 'x'})
        server._task_queue.pop()

        server._remove_dead_worker(dead_id)

        assert 'sub1' not in server._task_subscribers
        assert 'rpc1' not in server._rpc_subscribers
        assert dead_id not in server._available_workers
        assert 'task-700' not in server._task_worker_assignments

    def test_mark_worker_available_dedup(self, server):
        """Test _mark_worker_available doesn't add duplicates."""
        server._mark_worker_available(b'worker-1')
        server._mark_worker_available(b'worker-1')
        assert list(server._available_workers).count(b'worker-1') == 1

    def test_send_to_client_no_router(self, server):
        """Test _send_to_client when router is None is a no-op."""
        server._router = None
        server._send_to_client(b'identity', {'type': 'test'})

    # --- Status queries ---

    def test_get_pending_tasks(self, server):
        """Test get_pending_tasks."""
        server._task_queue.push('t1', {'a': 1})
        result = server.get_pending_tasks()
        assert len(result) == 1

    def test_get_processing_tasks(self, server):
        """Test get_processing_tasks."""
        server._task_queue.push('t1', {'a': 1})
        server._task_queue.pop()
        result = server.get_processing_tasks()
        assert len(result) == 1

    def test_get_status_not_running(self, server):
        """Test get_status when not running."""
        status = server.get_status()
        assert status['running'] is False
        assert status['pending_tasks'] == 0


class TestZmqBrokerServerWithSockets:
    """Tests using a real running server with ZMQ sockets."""

    @pytest.fixture
    def running_server(self):
        with tempfile.TemporaryDirectory(prefix='zmq') as tmp:
            tmp_path = Path(tmp)
            server = ZmqBrokerServer(storage_path=tmp_path / 's', sockets_path=tmp_path / 'k')
            server.start()
            try:
                yield server
            finally:
                server.stop()

    def test_poll_once_no_messages(self, running_server):
        """Test _poll_once with no incoming messages."""
        result = running_server._poll_once(0)
        assert result is False

    def test_handle_router_message_live(self, running_server):
        """Test sending a message through the actual ROUTER socket."""
        import zmq as zmq_sync

        ctx = zmq_sync.Context()
        try:
            dealer = ctx.socket(zmq_sync.DEALER)
            dealer.setsockopt_string(zmq_sync.IDENTITY, 'test-client')
            dealer.connect(running_server.router_endpoint)
            time.sleep(0.1)

            # Send a subscribe task message
            msg = {
                'type': MessageType.SUBSCRIBE_TASK.value,
                'identifier': 'test-subscriber',
                'sender': 'test-client',
            }
            dealer.send_multipart([b'', encode_message(msg)])
            running_server.run_once(timeout=1.0)

            assert 'test-subscriber' in running_server._task_subscribers

            # Send a task
            task_msg = {
                'type': MessageType.TASK.value,
                'id': 'live-task-1',
                'sender': 'test-client',
                'body': {'cmd': 'test'},
                'no_reply': True,
            }
            dealer.send_multipart([b'', encode_message(task_msg)])

            # Process the task message AND dispatch in the same poll cycle
            running_server.run_once(timeout=1.0)
            # May need a second poll cycle if dispatch didn't happen in the first
            running_server.run_once(timeout=0.5)

            # Worker should receive the task (poll with timeout to avoid race)
            poller = zmq_sync.Poller()
            poller.register(dealer, zmq_sync.POLLIN)
            socks = dict(poller.poll(timeout=2000))
            assert dealer in socks, 'Worker did not receive dispatched task'

            frames = dealer.recv_multipart()
            received = decode_message(frames[1] if frames[0] == b'' else frames[0])
            assert received['type'] == MessageType.TASK.value
            assert received['id'] == 'live-task-1'

        finally:
            dealer.close()
            ctx.term()
