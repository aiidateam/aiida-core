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

import copy
import json
from unittest.mock import MagicMock, PropertyMock, patch

import psutil
import pytest

from aiida.brokers.zeromq.broker import ZeromqBroker, ZeromqIncomingTask
from aiida.brokers.zeromq.queue import PersistentQueue
from aiida.manage.configuration import get_config


@pytest.fixture(scope='module')
def aiida_broker():
    """Returns the broker for the aiida_profile session fixture with a running service."""
    from aiida.manage import get_manager

    broker = get_manager().get_broker()

    if not isinstance(broker, ZeromqBroker):
        pytest.skip('Requires a profile with a ZeroMQ broker.')

    yield broker
    broker.close()


@pytest.fixture
def zeromq_broker(tmp_path):
    """Create a ZMQ broker instance rooted in ``tmp_path``."""
    profile = MagicMock()
    profile.name = 'test-profile'

    config = get_config()
    original_filepaths = config.filepaths

    def filepaths(current_profile):
        result = copy.deepcopy(original_filepaths(current_profile))

        if current_profile is profile:
            result['broker_service'] = {'dir': str(tmp_path), 'log': str(tmp_path / 'broker.log')}

        return result

    with patch.object(config, 'filepaths', side_effect=filepaths):
        yield ZeromqBroker(profile)


def test_get_default_config():
    """Test that the default broker settings declare the service as managed by the daemon."""
    assert ZeromqBroker.get_default_config() == {'supervised_by_daemon': True}


def test_entry_point():
    """Test the broker entry point is derived from the class."""
    assert ZeromqBroker.ENTRY_POINT == 'core.zeromq'


def test_init_invalid_backend():
    """Test the broker rejects profiles configured for a different backend."""
    profile = MagicMock()
    profile.process_control_backend = 'core.rabbitmq'

    with pytest.raises(ValueError, match=r'should be `core\.zeromq`'):
        ZeromqBroker(profile)


class TestZeromqBrokerStatusQueries:
    """Tests for ZeromqBroker status queries (file-based)."""

    def test_is_running_no_pid_file(self, zeromq_broker):
        """Test is_running returns False when no PID file exists."""
        assert not zeromq_broker.check_service_reachable()

    def test_probe_service_status_no_file(self, zeromq_broker):
        """Test probe_service_status captures a missing status file in the payload."""
        assert zeromq_broker.probe_service_status() == {
            'connected': False,
            'error': f'Status file `{zeromq_broker._service_dir / "broker.status"}` does not exist.',
        }

    def test_str_running(self, aiida_broker):
        """Test __str__ when running."""
        s = str(aiida_broker)
        assert 'ZeroMQ Broker' in s
        assert 'PID' in s

    def test_str_not_running(self, zeromq_broker):
        """Test __str__ when not running."""
        s = str(zeromq_broker)
        assert 'not running' in s

    def test__storage_path(self, zeromq_broker, tmp_path):
        """Test internal storage path."""
        assert zeromq_broker._storage_path == tmp_path / 'storage'

    def test__service_dir(self, zeromq_broker, tmp_path):
        """Test internal service directory."""
        assert zeromq_broker._service_dir == tmp_path

    def test_is_running_stale_pid(self, zeromq_broker):
        """Test is_running with stale PID."""
        pid_file = zeromq_broker._service_dir / 'broker.pid'
        pid_file.write_text('aiida-zeromq-broker 12345')

        with patch('aiida.brokers.zeromq.broker.psutil.Process', side_effect=psutil.NoSuchProcess(pid=12345)):
            assert not zeromq_broker.check_service_reachable()

    def test_probe_service_status_valid(self, zeromq_broker):
        """Test probe_service_status with valid JSON."""
        status_file = zeromq_broker._service_dir / 'broker.status'
        status_file.write_text(json.dumps({'pid': 123, 'running': True}))
        status = zeromq_broker.probe_service_status()
        assert status['connected'] is False
        assert status['pid'] == 123

    def test_probe_service_status_invalid_json(self, zeromq_broker):
        """Test probe_service_status captures invalid JSON in the payload."""
        status_file = zeromq_broker._service_dir / 'broker.status'
        status_file.write_text('{INVALID JSON')
        status = zeromq_broker.probe_service_status()
        assert status['connected'] is False
        assert 'JSONDecodeError:' in str(status['error'])

    def test_probe_service_status_invalid_payload_type(self, zeromq_broker, caplog):
        """Test probe_service_status captures valid JSON with an invalid top-level type."""
        status_file = zeromq_broker._service_dir / 'broker.status'
        status_file.write_text(json.dumps(['invalid']))

        status = zeromq_broker.probe_service_status()

        assert status == {'connected': False, 'error': "Invalid ZeroMQ service status file found: ['invalid']"}
        assert "Invalid ZeroMQ service status file found: ['invalid']" in caplog.text


class TestZeromqBrokerCommunicator:
    """Tests for ZeromqBroker communicator management."""

    def test_get_communicator_breaks_when_endpoint_becomes_available(self, zeromq_broker, monkeypatch):
        """Test get_communicator stops polling once the router endpoint appears."""
        endpoint = 'ipc:///tmp/router.sock'

        monkeypatch.setattr('aiida.brokers.zeromq.broker.BROKER_READY_TIMEOUT', 10.0)

        with (
            patch.object(ZeromqBroker, '_router_endpoint', new_callable=PropertyMock) as router_endpoint,
            patch('aiida.brokers.zeromq.broker.time.monotonic', side_effect=[100.0, 100.1]),
            patch('aiida.brokers.zeromq.broker.time.sleep') as sleep,
            patch('aiida.manage.configuration.get_config_option', return_value=None),
            patch('aiida.brokers.zeromq.broker.ZeromqCommunicator') as communicator_cls,
        ):
            router_endpoint.side_effect = [None, endpoint]
            communicator = communicator_cls.return_value

            result = zeromq_broker.get_communicator()

            assert result is communicator
            sleep.assert_called_once_with(0.2)
            communicator_cls.assert_called_once_with(router_endpoint=endpoint, task_timeout=None)
            communicator.start.assert_called_once()

    def test_get_communicator_warns_while_waiting_for_endpoint(self, zeromq_broker, monkeypatch):
        """Test get_communicator logs a warning after waiting for five seconds."""
        endpoint = 'ipc:///tmp/router.sock'

        monkeypatch.setattr('aiida.brokers.zeromq.broker.BROKER_READY_TIMEOUT', 10.0)

        with (
            patch.object(ZeromqBroker, '_router_endpoint', new_callable=PropertyMock) as router_endpoint,
            patch('aiida.brokers.zeromq.broker.time.monotonic', side_effect=[100.0, 100.1, 105.1, 105.2]),
            patch('aiida.brokers.zeromq.broker.time.sleep') as sleep,
            patch('aiida.brokers.zeromq.broker.AIIDA_LOGGER.warning') as warning,
            patch('aiida.manage.configuration.get_config_option', return_value=None),
            patch('aiida.brokers.zeromq.broker.ZeromqCommunicator') as communicator_cls,
        ):
            router_endpoint.side_effect = [None, None, endpoint]
            communicator = communicator_cls.return_value

            result = zeromq_broker.get_communicator()

            assert result is communicator
            assert sleep.call_count == 2
            warning.assert_called_once_with('Still waiting for broker to become ready...')
            communicator_cls.assert_called_once_with(router_endpoint=endpoint, task_timeout=None)
            communicator.start.assert_called_once()

    def test_get_communicator(self, aiida_broker, monkeypatch):
        """Test get_communicator."""
        monkeypatch.setattr('aiida.brokers.zeromq.broker.BROKER_READY_TIMEOUT', 0.5)
        comm = aiida_broker.get_communicator()
        assert comm is not None
        assert not comm.is_closed()

        # Second call returns cached instance
        comm2 = aiida_broker.get_communicator()
        assert comm2 is comm

    def test_get_communicator_timeout(self, zeromq_broker, monkeypatch):
        """Test get_communicator raises on timeout when zeromq_broker not running."""
        monkeypatch.setattr('aiida.brokers.zeromq.broker.BROKER_READY_TIMEOUT', 0.5)
        with pytest.raises(ConnectionError, match='did not become ready'):
            zeromq_broker.get_communicator()

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
        queue_path = zeromq_broker._storage_path / 'tasks'
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
    """Integration tests for the ZeroMQ broker with AiiDA."""

    def test_broker_lifecycle(self, aiida_broker):
        """Test the zeromq_broker lifecycle."""
        assert aiida_broker.check_service_reachable()

        status = aiida_broker.probe_service_status()
        assert status['connected'] is True
        assert 'pid' in status
