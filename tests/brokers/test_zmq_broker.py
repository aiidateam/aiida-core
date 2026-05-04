###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``aiida.brokers.zmq.broker.ZmqBroker`` and ``ZmqIncomingTask``."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aiida.brokers.zmq import ZmqBroker
from aiida.brokers.zmq.broker import ZmqIncomingTask
from aiida.brokers.zmq.communicator import ZmqCommunicator
from aiida.brokers.zmq.queue import PersistentQueue
from tests.conftest import start_zmq_broker, stop_zmq_broker


def _create_broker_with_base_path(base_path: Path) -> ZmqBroker:
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

    def test_str_running(self, tmp_path):
        """Test __str__ when running."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zmq_broker(broker)
        try:
            s = str(broker)
            assert 'ZMQ Broker' in s
            assert 'PID' in s
        finally:
            stop_zmq_broker(broker)

    def test_str_not_running(self, tmp_path):
        """Test __str__ when not running."""
        broker = _create_broker_with_base_path(tmp_path)
        s = str(broker)
        assert 'not running' in s

    def test_storage_path(self, tmp_path):
        """Test storage_path property."""
        broker = _create_broker_with_base_path(tmp_path)
        assert broker.storage_path == tmp_path / 'storage'

    def test_base_path(self, tmp_path):
        """Test base_path property."""
        broker = _create_broker_with_base_path(tmp_path)
        assert broker.base_path == tmp_path

    def test_get_sockets_path_no_file(self, tmp_path):
        """Test _get_sockets_path when file missing."""
        broker = _create_broker_with_base_path(tmp_path)
        assert broker._get_sockets_path() is None

    def test_get_sockets_path_os_error(self, tmp_path):
        """Test _get_sockets_path when read fails."""
        broker = _create_broker_with_base_path(tmp_path)
        sockets_file = tmp_path / 'broker.sockets'
        sockets_file.mkdir()  # directory instead of file => OSError on read_text
        assert broker._get_sockets_path() is None

    def test_get_service_pid_sentinel_format(self, tmp_path):
        """Test PID file with sentinel format."""
        broker = _create_broker_with_base_path(tmp_path)
        pid_file = tmp_path / 'broker.pid'
        pid_file.write_text('aiida-zmq-broker 12345')
        assert broker.get_service_pid() == 12345

    def test_get_service_pid_bare_format(self, tmp_path):
        """Test PID file with bare PID fallback."""
        broker = _create_broker_with_base_path(tmp_path)
        pid_file = tmp_path / 'broker.pid'
        pid_file.write_text('54321')
        assert broker.get_service_pid() == 54321

    def test_get_service_pid_invalid(self, tmp_path):
        """Test PID file with invalid content."""
        broker = _create_broker_with_base_path(tmp_path)
        pid_file = tmp_path / 'broker.pid'
        pid_file.write_text('garbage text')
        assert broker.get_service_pid() is None

    def test_is_running_stale_pid(self, tmp_path):
        """Test is_running with stale PID."""
        broker = _create_broker_with_base_path(tmp_path)
        pid_file = tmp_path / 'broker.pid'
        pid_file.write_text('aiida-zmq-broker 999999')  # Non-existent PID
        assert not broker.is_running

    def test_get_service_status_valid(self, tmp_path):
        """Test get_service_status with valid JSON."""
        broker = _create_broker_with_base_path(tmp_path)
        status_file = tmp_path / 'broker.status'
        status_file.write_text(json.dumps({'pid': 123, 'running': True}))
        status = broker.get_service_status()
        assert status is not None
        assert status['pid'] == 123

    def test_get_service_status_invalid_json(self, tmp_path):
        """Test get_service_status with invalid JSON."""
        broker = _create_broker_with_base_path(tmp_path)
        status_file = tmp_path / 'broker.status'
        status_file.write_text('{INVALID JSON')
        assert broker.get_service_status() is None

    def test_cleanup_stale_service_files(self, tmp_path):
        """Test _cleanup_stale_service_files removes all stale files."""
        broker = _create_broker_with_base_path(tmp_path)

        (tmp_path / 'broker.pid').write_text('aiida-zmq-broker 1')
        (tmp_path / 'broker.status').write_text('{}')
        sockets_dir = tmp_path / 'test_sockets'
        sockets_dir.mkdir()
        (tmp_path / 'broker.sockets').write_text(str(sockets_dir))

        broker._cleanup_stale_service_files()

        assert not (tmp_path / 'broker.pid').exists()
        assert not (tmp_path / 'broker.status').exists()
        assert not (tmp_path / 'broker.sockets').exists()
        assert not sockets_dir.exists()


class TestZmqBrokerCommunicator:
    """Tests for ZmqBroker communicator management."""

    def test_get_communicator_and_close(self, tmp_path):
        """Test get_communicator and close."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zmq_broker(broker)

        try:
            with patch('aiida.manage.configuration.get_config_option', return_value=None):
                comm = broker.get_communicator(wait_for_broker=5.0)
                assert comm is not None
                assert not comm.is_closed()

                # Second call returns cached instance
                comm2 = broker.get_communicator()
                assert comm2 is comm
        finally:
            broker.close()
            stop_zmq_broker(broker)

    def test_get_communicator_timeout(self, tmp_path):
        """Test get_communicator raises on timeout when broker not running."""
        broker = _create_broker_with_base_path(tmp_path)
        with pytest.raises(ConnectionError, match='did not become ready'):
            broker.get_communicator(wait_for_broker=0.5)

    def test_context_manager(self, tmp_path):
        """Test __enter__ / __exit__."""
        broker = _create_broker_with_base_path(tmp_path)
        with broker as b:
            assert b is broker


class TestZmqBrokerTasks:
    """Tests for ZmqBroker task iteration."""

    def test_iterate_tasks_no_queue(self, tmp_path):
        """Test iterate_tasks when queue path doesn't exist."""
        broker = _create_broker_with_base_path(tmp_path)
        tasks = list(broker.iterate_tasks())
        assert tasks == []

    def test_iterate_tasks_with_data(self, tmp_path):
        """Test iterate_tasks with pending tasks."""
        broker = _create_broker_with_base_path(tmp_path)
        queue_path = tmp_path / 'storage' / 'tasks'
        queue = PersistentQueue(queue_path)
        queue.push('task-1', {'body': 'hello'})
        queue.push('task-2', {'body': 'world'})

        tasks = list(broker.iterate_tasks())
        assert len(tasks) == 2
        assert all(isinstance(t, ZmqIncomingTask) for t in tasks)

    def test_revive_process_writes_continue_task(self, tmp_path):
        """``revive_process`` should push a continue task to the persistent queue."""
        broker = _create_broker_with_base_path(tmp_path)

        broker.revive_process(42)

        queue = PersistentQueue(tmp_path / 'storage' / 'tasks')
        pending = queue.get_all_pending()
        assert len(pending) == 1

        _, task_data = pending[0]
        assert task_data['no_reply'] is True
        # plumpy.create_continue_body shape: {'task': 'continue', 'args': {'pid': 42, 'nowait': True, 'tag': None}}
        assert task_data['body']['args']['pid'] == 42
        assert task_data['body']['args']['nowait'] is True

    def test_revive_process_multiple_pids(self, tmp_path):
        """Reviving multiple PIDs should produce one task per PID with unique task ids."""
        broker = _create_broker_with_base_path(tmp_path)

        for pid in (1, 2, 3):
            broker.revive_process(pid)

        queue = PersistentQueue(tmp_path / 'storage' / 'tasks')
        pending = queue.get_all_pending()
        assert len(pending) == 3
        assert len({task_id for task_id, _ in pending}) == 3
        assert {task_data['body']['args']['pid'] for _, task_data in pending} == {1, 2, 3}

    def test_revive_then_iterate_round_trip(self, tmp_path):
        """A revived task must be visible to ``iterate_tasks`` (producer/consumer schema check)."""
        broker = _create_broker_with_base_path(tmp_path)

        broker.revive_process(7)

        tasks = list(broker.iterate_tasks())
        assert len(tasks) == 1
        body = tasks[0].body
        assert body is not None
        assert body['args']['pid'] == 7


class TestZmqIncomingTask:
    """Tests for ZmqIncomingTask."""

    def test_processing_context_manager(self, tmp_path):
        """Test ZmqIncomingTask.processing context manager."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'body': 'test_body'})

        task = ZmqIncomingTask('t1', {'body': 'test_body'}, queue)
        assert task.body == 'test_body'

        with task.processing() as outcome:
            outcome.set_result('done')

        # Task should be removed from pending
        assert queue.remove_pending('t1') is False


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
