###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `aiida.brokers.zmq` module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aiida.brokers.zmq import ZmqBroker
from aiida.brokers.zmq.communicator import ZmqCommunicator
from aiida.brokers.zmq.queue import PersistentQueue
from aiida.brokers.zmq.server import ZmqBrokerServer
from aiida.brokers.zmq.service import ZmqBrokerService
from tests.conftest import start_zmq_broker, stop_zmq_broker


def _create_broker_with_base_path(base_path: Path) -> ZmqBroker:
    """Create a ZmqBroker with a custom base path for testing."""
    with patch('aiida.brokers.zmq.broker.get_broker_base_path', return_value=base_path):
        return ZmqBroker(MagicMock())


class TestZmqBrokerStatusQueries:
    """Tests for ZmqBroker status queries (file-based)."""

    def test_is_running_no_pid_file(self, tmp_path):
        """Test is_running returns False when no PID file exists."""
        broker = _create_broker_with_base_path(tmp_path)
        assert not broker.is_running

    def test_get_service_pid_no_file(self, tmp_path):
        """Test get_service_pid returns None when no PID file exists."""
        broker = _create_broker_with_base_path(tmp_path)
        assert broker.get_service_pid() is None

    def test_get_service_status_no_file(self, tmp_path):
        """Test get_service_status returns None when no status file exists."""
        broker = _create_broker_with_base_path(tmp_path)
        assert broker.get_service_status() is None

    def test_endpoints_no_sockets_file(self, tmp_path):
        """Test endpoints return None when sockets file doesn't exist."""
        broker = _create_broker_with_base_path(tmp_path)
        assert broker.router_endpoint is None

    def test_start_stop_cycle(self, tmp_path):
        """Test querying a running broker service."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zmq_broker(broker)

        try:
            assert broker.is_running
            assert broker.get_service_pid() is not None
            assert broker.router_endpoint is not None
        finally:
            stop_zmq_broker(broker)

        assert not broker.is_running

    def test_start_already_running(self, tmp_path):
        """Test starting when already running is idempotent."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zmq_broker(broker)

        try:
            start_zmq_broker(broker)  # idempotent
            assert broker.is_running
        finally:
            stop_zmq_broker(broker)

    def test_stop_not_running(self, tmp_path):
        """Test stopping when not running is a no-op."""
        broker = _create_broker_with_base_path(tmp_path)
        stop_zmq_broker(broker)  # Should not raise

    def test_restart(self, tmp_path):
        """Test restarting the broker service."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zmq_broker(broker)

        try:
            old_pid = broker.get_service_pid()
            stop_zmq_broker(broker)
            start_zmq_broker(broker)
            assert broker.is_running

            new_pid = broker.get_service_pid()
            assert new_pid != old_pid
        finally:
            stop_zmq_broker(broker)


class TestZmqBrokerServer:
    """Tests for the ZmqBrokerServer."""

    def test_init(self, tmp_path):
        """Test server initialization."""
        storage_path = tmp_path / 'storage'
        sockets_path = tmp_path / 'sockets'

        server = ZmqBrokerServer(storage_path=storage_path, sockets_path=sockets_path)
        assert server.storage_path == storage_path
        assert server.sockets_path == sockets_path

    def test_start_stop(self):
        """Test starting and stopping the server."""
        import tempfile

        # Use short temp directory to avoid socket path length limit
        with tempfile.TemporaryDirectory(prefix='zmq') as tmp:
            tmp_path = Path(tmp)
            storage_path = tmp_path / 's'
            sockets_path = tmp_path / 'k'

            server = ZmqBrokerServer(storage_path=storage_path, sockets_path=sockets_path)
            server.start()

            try:
                status = server.get_status()
                assert 'pending_tasks' in status
                assert 'processing_tasks' in status
            finally:
                server.stop()

    def test_get_status(self):
        """Test getting server status."""
        import tempfile

        # Use short temp directory to avoid socket path length limit
        with tempfile.TemporaryDirectory(prefix='zmq') as tmp:
            tmp_path = Path(tmp)
            storage_path = tmp_path / 's'
            sockets_path = tmp_path / 'k'

            server = ZmqBrokerServer(storage_path=storage_path, sockets_path=sockets_path)
            server.start()

            try:
                status = server.get_status()
                assert status['pending_tasks'] == 0
                assert status['processing_tasks'] == 0
            finally:
                server.stop()


class TestZmqBrokerService:
    """Tests for the ZmqBrokerService."""

    def test_init(self, tmp_path):
        """Test service initialization."""
        service = ZmqBrokerService(base_path=tmp_path)
        assert service.base_path == tmp_path
        assert service.pid_file == tmp_path / 'broker.pid'
        assert service.status_file == tmp_path / 'broker.status'

    def test_start_stop(self, tmp_path):
        """Test starting and stopping the service."""
        service = ZmqBrokerService(base_path=tmp_path)
        service.start()

        try:
            assert service.pid_file.exists()
            assert service.status_file.exists()
        finally:
            service.stop()

        assert not service.pid_file.exists()
        assert not service.status_file.exists()


class TestPersistentQueue:
    """Tests for the PersistentQueue."""

    def test_init(self, tmp_path):
        """Test queue initialization."""
        queue = PersistentQueue(tmp_path)
        assert queue._storage_path == tmp_path

    def test_push_pop(self, tmp_path):
        """Test pushing and popping tasks."""
        queue = PersistentQueue(tmp_path)

        # Push a task
        task_id = 'task-001'
        queue.push(task_id, {'type': 'test', 'data': 'hello'})

        # Pop the task
        popped_id, task_data = queue.pop()
        assert popped_id == task_id
        assert task_data['type'] == 'test'
        assert task_data['data'] == 'hello'

    def test_pop_empty(self, tmp_path):
        """Test popping from empty queue."""
        queue = PersistentQueue(tmp_path)
        result = queue.pop()
        assert result is None

    def test_ack_task(self, tmp_path):
        """Test acknowledging a task."""
        queue = PersistentQueue(tmp_path)

        task_id = 'task-002'
        queue.push(task_id, {'type': 'test'})
        queue.pop()
        result = queue.ack(task_id)

        assert result is True
        # Task should no longer be in queue
        assert queue.pop() is None

    def test_nack_task(self, tmp_path):
        """Test negative acknowledgment (requeue)."""
        queue = PersistentQueue(tmp_path)

        task_id = 'task-003'
        queue.push(task_id, {'type': 'test'})
        queue.pop()
        result = queue.nack(task_id, requeue=True)

        assert result is True
        # Task should be requeued
        popped_id, _ = queue.pop()
        assert popped_id == task_id

    def test_get_all_pending(self, tmp_path):
        """Test getting all pending tasks."""
        queue = PersistentQueue(tmp_path)

        task_id1 = 'task-004'
        task_id2 = 'task-005'
        queue.push(task_id1, {'type': 'test1'})
        queue.push(task_id2, {'type': 'test2'})

        pending = queue.get_all_pending()
        assert len(pending) == 2

        task_ids = [t[0] for t in pending]
        assert task_id1 in task_ids
        assert task_id2 in task_ids


class TestZmqCommunicator:
    """Tests for the ZmqCommunicator."""

    def test_init(self, tmp_path):
        """Test communicator initialization."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zmq_broker(broker)

        try:
            communicator = ZmqCommunicator(
                router_endpoint=broker.router_endpoint,
            )
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
            with ZmqCommunicator(
                router_endpoint=broker.router_endpoint,
            ) as communicator:
                assert communicator.is_closed() is False

            assert communicator.is_closed() is True
        finally:
            stop_zmq_broker(broker)


class TestZmqBrokerIntegration:
    """Integration tests for the ZMQ broker with AiiDA."""

    @pytest.fixture
    def zmq_broker(self, tmp_path):
        """Create a ZMQ broker for testing."""
        broker_dir = tmp_path / 'broker' / 'test-uuid'
        broker = _create_broker_with_base_path(broker_dir)
        start_zmq_broker(broker)

        yield broker

        stop_zmq_broker(broker)

    def test_broker_lifecycle(self, zmq_broker):
        """Test the broker lifecycle."""
        assert zmq_broker.is_running

        status = zmq_broker.get_service_status()
        assert status is not None
        assert 'pid' in status

    def test_communicator_connection(self, zmq_broker):
        """Test connecting a communicator to the broker."""
        communicator = ZmqCommunicator(
            router_endpoint=zmq_broker.router_endpoint,
        )
        communicator.start()

        try:
            assert not communicator.is_closed()
        finally:
            communicator.close()
