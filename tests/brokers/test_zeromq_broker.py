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
from unittest.mock import MagicMock, patch

import pytest

from aiida.brokers.zeromq.broker import ZeromqBroker, ZeromqIncomingTask
from aiida.brokers.zeromq.communicator import ZeromqCommunicator
from aiida.brokers.zeromq.queue import PersistentQueue


def test_get_default_config():
    """Test that the default broker settings declare the service as managed by the daemon."""
    assert ZeromqBroker.get_default_config() == {'supervised_by_daemon': True}


def test_not_supervised_by_daemon_raises():
    """Test that broker construction fails when the service is not managed by the daemon."""
    from aiida.common.exceptions import ConfigurationError

    profile = MagicMock()
    profile.process_control_config = {'supervised_by_daemon': False}

    with pytest.raises(ConfigurationError, match='not managed by the daemon'):
        ZeromqBroker(profile)


class TestZeromqBrokerStatusQueries:
    """Tests for ZeromqBroker status queries (file-based)."""

    def test_is_running_no_pid_file(self, zeromq_broker):
        """Test is_running returns False when no PID file exists."""
        assert not zeromq_broker.is_running

    def test_get_service_pid_no_file(self, zeromq_broker):
        """Test get_service_pid returns None when no PID file exists."""
        assert zeromq_broker.get_service_pid() is None

    def test_get_service_status_no_file(self, zeromq_broker):
        """Test get_service_status returns None when no status file exists."""
        assert zeromq_broker.get_service_status() is None

    def test_endpoints_no_sockets_file(self, zeromq_broker):
        """Test endpoints return None when sockets file doesn't exist."""
        assert zeromq_broker.router_endpoint is None

    def test_str_running(self, zeromq_broker_server):
        """Test __str__ when running."""
        s = str(zeromq_broker_server)
        assert 'ZeroMQ Broker' in s
        assert 'PID' in s

    def test_str_not_running(self, zeromq_broker):
        """Test __str__ when not running."""
        s = str(zeromq_broker)
        assert 'not running' in s

    def test_storage_path(self, zeromq_broker, tmp_path):
        """Test storage_path property."""
        assert zeromq_broker.storage_path == tmp_path / 'storage'

    def test_service_dir(self, zeromq_broker, tmp_path):
        """Test service_dir property."""
        assert zeromq_broker.service_dir == tmp_path

    def test_get_sockets_path_no_file(self, zeromq_broker):
        """Test _get_sockets_path when file missing."""
        assert zeromq_broker._get_sockets_path() is None

    def test_get_sockets_path_os_error(self, zeromq_broker):
        """Test _get_sockets_path when read fails."""
        sockets_file = zeromq_broker.service_dir / 'broker.sockets'
        sockets_file.mkdir()  # directory instead of file => OSError on read_text
        assert zeromq_broker._get_sockets_path() is None

    def test_get_service_pid_sentinel_format(self, zeromq_broker):
        """Test PID file with sentinel format."""
        pid_file = zeromq_broker.service_dir / 'broker.pid'
        pid_file.write_text('aiida-zeromq-broker 12345')
        assert zeromq_broker.get_service_pid() == 12345

    def test_get_service_pid_bare_format(self, zeromq_broker):
        """Test PID file with bare PID fallback."""
        pid_file = zeromq_broker.service_dir / 'broker.pid'
        pid_file.write_text('54321')
        assert zeromq_broker.get_service_pid() == 54321

    def test_get_service_pid_invalid(self, zeromq_broker):
        """Test PID file with invalid content."""
        pid_file = zeromq_broker.service_dir / 'broker.pid'
        pid_file.write_text('garbage text')
        assert zeromq_broker.get_service_pid() is None

    def test_is_running_stale_pid(self, zeromq_broker):
        """Test is_running with stale PID."""
        pid_file = zeromq_broker.service_dir / 'broker.pid'
        pid_file.write_text('aiida-zeromq-broker 999999')  # Non-existent PID
        assert not zeromq_broker.is_running

    def test_get_service_status_valid(self, zeromq_broker):
        """Test get_service_status with valid JSON."""
        status_file = zeromq_broker.service_dir / 'broker.status'
        status_file.write_text(json.dumps({'pid': 123, 'running': True}))
        status = zeromq_broker.get_service_status()
        assert status is not None
        assert status['pid'] == 123

    def test_get_service_status_invalid_json(self, zeromq_broker):
        """Test get_service_status with invalid JSON."""
        status_file = zeromq_broker.service_dir / 'broker.status'
        status_file.write_text('{INVALID JSON')
        assert zeromq_broker.get_service_status() is None


class TestZeromqBrokerCommunicator:
    """Tests for ZeromqBroker communicator management."""

    def test_get_communicator_and_close(self, zeromq_broker_server):
        """Test get_communicator and close."""
        try:
            with patch('aiida.manage.configuration.get_config_option', return_value=None):
                comm = zeromq_broker_server.get_communicator(wait_for_broker=5.0)
                assert comm is not None
                assert not comm.is_closed()

                # Second call returns cached instance
                comm2 = zeromq_broker_server.get_communicator()
                assert comm2 is comm
        finally:
            zeromq_broker_server.close()

    def test_get_communicator_timeout(self, zeromq_broker):
        """Test get_communicator raises on timeout when zeromq_broker not running."""
        with pytest.raises(ConnectionError, match='did not become ready'):
            zeromq_broker.get_communicator(wait_for_broker=0.5)

    def test_context_manager(self, zeromq_broker):
        """Test __enter__ / __exit__."""
        with zeromq_broker as instance:
            assert instance is zeromq_broker


class TestZeromqBrokerTasks:
    """Tests for ZeromqBroker task iteration."""

    def test_iterate_tasks_no_queue(self, zeromq_broker):
        """Test iterate_tasks when queue path doesn't exist."""
        tasks = list(zeromq_broker.iterate_tasks())
        assert tasks == []

    def test_iterate_tasks_with_data(self, zeromq_broker):
        """Test iterate_tasks with pending tasks."""
        queue_path = zeromq_broker.storage_path / 'tasks'
        queue = PersistentQueue(queue_path)
        queue.push('task-1', {'body': 'hello'})
        queue.push('task-2', {'body': 'world'})

        tasks = list(zeromq_broker.iterate_tasks())
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
    """Integration tests for the ZeroMQ zeromq_broker with AiiDA."""

    def test_broker_lifecycle(self, zeromq_broker_server):
        """Test the zeromq_broker lifecycle."""
        assert zeromq_broker_server.is_running

        status = zeromq_broker_server.get_service_status()
        assert status is not None
        assert 'pid' in status

    def test_communicator_connection(self, zeromq_broker_server):
        """Test connecting a communicator to the zeromq_broker."""
        communicator = ZeromqCommunicator(
            router_endpoint=zeromq_broker_server.router_endpoint,
        )
        communicator.start()

        try:
            assert not communicator.is_closed()
        finally:
            communicator.close()
