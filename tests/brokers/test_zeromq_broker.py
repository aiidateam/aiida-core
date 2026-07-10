###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``aiida.brokers.zeromq.broker.ZeromqBroker`` and ``ZeromqIncomingTask``."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aiida.brokers.zeromq import ZeromqBroker
from aiida.brokers.zeromq.broker import ZeromqIncomingTask
from aiida.brokers.zeromq.communicator import ZeromqCommunicator
from aiida.brokers.zeromq.queue import PersistentQueue
from tests.conftest import start_zeromq_broker, stop_zeromq_broker


def _create_broker_with_base_path(base_path: Path) -> ZeromqBroker:
    with patch('aiida.brokers.zeromq.broker.get_broker_base_path', return_value=base_path):
        return ZeromqBroker(MagicMock())


class TestZeromqBrokerStatusQueries:
    """Tests for ZeromqBroker status queries (file-based)."""

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
        start_zeromq_broker(broker)

        try:
            assert broker.is_running
            assert broker.get_service_pid() is not None
            assert broker.router_endpoint is not None
        finally:
            stop_zeromq_broker(broker)

        assert not broker.is_running

    def test_start_already_running(self, tmp_path):
        """Test starting when already running is idempotent."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zeromq_broker(broker)

        try:
            start_zeromq_broker(broker)  # idempotent
            assert broker.is_running
        finally:
            stop_zeromq_broker(broker)

    def test_stop_not_running(self, tmp_path):
        """Test stopping when not running is a no-op."""
        broker = _create_broker_with_base_path(tmp_path)
        stop_zeromq_broker(broker)  # Should not raise

    def test_restart(self, tmp_path):
        """Test restarting the broker service."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zeromq_broker(broker)

        try:
            old_pid = broker.get_service_pid()
            stop_zeromq_broker(broker)
            start_zeromq_broker(broker)
            assert broker.is_running

            new_pid = broker.get_service_pid()
            assert new_pid != old_pid
        finally:
            stop_zeromq_broker(broker)

    def test_str_running(self, tmp_path):
        """Test __str__ when running."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zeromq_broker(broker)
        try:
            s = str(broker)
            assert 'ZeroMQ Broker' in s
            assert 'PID' in s
        finally:
            stop_zeromq_broker(broker)

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
        pid_file.write_text('aiida-zeromq-broker 12345')
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
        pid_file.write_text('aiida-zeromq-broker 999999')  # Non-existent PID
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

        (tmp_path / 'broker.pid').write_text('aiida-zeromq-broker 1')
        (tmp_path / 'broker.status').write_text('{}')
        sockets_dir = tmp_path / 'test_sockets'
        sockets_dir.mkdir()
        (tmp_path / 'broker.sockets').write_text(str(sockets_dir))

        broker._cleanup_stale_service_files()

        assert not (tmp_path / 'broker.pid').exists()
        assert not (tmp_path / 'broker.status').exists()
        assert not (tmp_path / 'broker.sockets').exists()
        assert not sockets_dir.exists()


class TestZeromqBrokerCommunicator:
    """Tests for ZeromqBroker communicator management."""

    def test_get_communicator_and_close(self, tmp_path):
        """Test get_communicator and close."""
        broker = _create_broker_with_base_path(tmp_path)
        start_zeromq_broker(broker)

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
            stop_zeromq_broker(broker)

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


class TestZeromqBrokerTasks:
    """Tests for ZeromqBroker task iteration."""

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
        assert all(isinstance(t, ZeromqIncomingTask) for t in tasks)


class TestZeromqIncomingTask:
    """Tests for ZeromqIncomingTask."""

    def test_processing_context_manager(self, tmp_path):
        """Test ZeromqIncomingTask.processing context manager."""
        queue = PersistentQueue(tmp_path)
        queue.push('t1', {'body': 'test_body'})

        task = ZeromqIncomingTask('t1', {'body': 'test_body'}, queue)
        assert task.body == 'test_body'

        with task.processing() as outcome:
            outcome.set_result('done')

        # Task should be removed from pending
        assert queue.remove_pending('t1') is False


class TestZeromqBrokerIntegration:
    """Integration tests for the ZeroMQ broker with AiiDA."""

    @pytest.fixture
    def zeromq_broker(self, tmp_path):
        """Create a ZeroMQ broker for testing."""
        broker_dir = tmp_path / 'broker' / 'test-uuid'
        broker = _create_broker_with_base_path(broker_dir)
        start_zeromq_broker(broker)

        yield broker

        stop_zeromq_broker(broker)

    def test_broker_lifecycle(self, zeromq_broker):
        """Test the broker lifecycle."""
        assert zeromq_broker.is_running

        status = zeromq_broker.get_service_status()
        assert status is not None
        assert 'pid' in status

    def test_communicator_connection(self, zeromq_broker):
        """Test connecting a communicator to the broker."""
        communicator = ZeromqCommunicator(
            router_endpoint=zeromq_broker.router_endpoint,
        )
        communicator.start()

        try:
            assert not communicator.is_closed()
        finally:
            communicator.close()
