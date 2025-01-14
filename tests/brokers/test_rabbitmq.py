###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `aiida.brokers.rabbitmq` module."""

import pathlib
import uuid

import pytest
import requests
from kiwipy.rmq import RmqThreadCommunicator
from packaging.version import parse

from aiida.brokers.rabbitmq import client, utils
from aiida.engine.processes import ProcessState, control
from aiida.orm import Int

pytestmark = pytest.mark.requires_rmq


def test_str_method(monkeypatch, manager):
    """Test the `__str__` method of the `RabbitmqBroker`."""

    def raise_connection_error():
        raise ConnectionError

    broker = manager.get_broker()
    assert 'RabbitMQ v' in str(broker)

    monkeypatch.setattr(broker, 'get_communicator', raise_connection_error)
    assert 'RabbitMQ @' in str(broker)


@pytest.mark.parametrize(
    ('version', 'supported'),
    (
        ('3.5', False),
        ('3.6', True),
        ('3.6.0', True),
        ('3.6.1', True),
        ('3.8', True),
        ('3.8.14', True),
        ('3.8.15', False),
        ('3.9.0', False),
        ('3.9', False),
    ),
)
def test_is_rabbitmq_version_supported(monkeypatch, version, supported, manager):
    """Test the :meth:`aiida.brokers.rabbitmq.RabbitmqBroker.is_rabbitmq_version_supported`."""
    broker = manager.get_broker()
    monkeypatch.setattr(broker, 'get_rabbitmq_version', lambda: parse(version))
    assert broker.is_rabbitmq_version_supported() is supported


@pytest.mark.parametrize(
    ('args', 'kwargs', 'expected'),
    (
        ((), {}, 'amqp://guest:guest@127.0.0.1:5672?'),
        ((), {'heartbeat': 1}, 'amqp://guest:guest@127.0.0.1:5672?'),
        ((), {'cafile': 'file', 'cadata': 'ab'}, 'amqp://guest:guest@127.0.0.1:5672?'),
        (('amqps', 'jojo', 'rabbit', '192.168.0.1', 6783), {}, 'amqps://jojo:rabbit@192.168.0.1:6783?'),
    ),
)
def test_get_rmq_url(args, kwargs, expected):
    """Test the `get_rmq_url` method.

    It is not possible to use a complete hardcoded URL to compare to the return value of `get_rmq_url` because the order
    of the query parameters are arbitrary. Therefore, we just compare the rest of the URL and make sure that all query
    parameters are present in the expected form separately.
    """
    if isinstance(expected, str):
        url = utils.get_rmq_url(*args, **kwargs)
        assert url.startswith(expected)
        for key, value in kwargs.items():
            assert f'{key}={value}' in url
    else:
        with pytest.raises(expected):
            utils.get_rmq_url(*args, **kwargs)


@pytest.mark.parametrize('url', ('amqp://guest:guest@127.0.0.1:5672',))
def test_communicator(url):
    """Test the instantiation of a ``kiwipy.rmq.RmqThreadCommunicator``.

    This class is used by all runners to communicate with the RabbitMQ server.
    """
    RmqThreadCommunicator.connect(connection_params={'url': url})


def test_add_rpc_subscriber(communicator):
    """Test ``add_rpc_subscriber``."""
    communicator.add_rpc_subscriber(None)


def test_add_broadcast_subscriber(communicator):
    """Test ``add_broadcast_subscriber``."""
    communicator.add_broadcast_subscriber(None)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_duplicate_subscriber_identifier(aiida_code_installed, started_daemon_client, submit_and_await):
    """Test that a ``DuplicateSubscriberError`` in ``ProcessLauncher._continue`` does not except the process.

    It is possible that when a daemon worker tries to continue a process, that a ``kiwipy.DuplicateSubscriberError`` is
    raised, which means that it already subscribed itself to be running that process.
    This can occur for at least two reasons:

        * The user manually recreated the process task, mistakenly thinking it had been lost
        * RabbitMQ requeues the task because the daemon worker lost its connection or did not respond to the
          heartbeat in time, and the task is sent to the same worker once it regains connection.

    In both cases, the actual task is still actually being run and we should not let this exception except the entire
    process. Unfortunately, these duplicate tasks still happen quite a lot when the daemon workers are under heavy load
    and we don't want a bunch of processes to be excepted because of this.

    In most cases, just ignoring the task wil be the best solution. In the end, the original task is likely to complete.
    If it turns out that the task actually got lost and the process is stuck, the user can find this error message in
    the logs and manually recreate the task, using for example ``verdi devel revive``.

    Note that this exception is only raised within a single worker, i.e., if another worker subscribes to the same
    process, that should not incur this inception and that is not what we are testing here. This test should therefore
    be ran with a single daemon worker.
    """
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')

    builder = code.get_builder()
    builder.x = Int(1)
    builder.y = Int(1)
    builder.metadata.options.sleep = 2  # Add a sleep to give time to send duplicate task before it finishing

    # Submit the process to the daemon and wait for it to be picked up (signalled by it going in waiting state).
    node = submit_and_await(builder, ProcessState.WAITING)

    # Recreate process task causing the daemon to pick it up again and incurring the ``DuplicateSubscriberError``
    control.revive_processes([node], wait=True)

    # Wait for the original node to be finished
    submit_and_await(node, ProcessState.FINISHED)

    # The original node should now have finished normally and not excepted
    assert node.is_finished_ok, (node.process_state, node.exit_status)

    # Verify that the receiving of the duplicate task was logged by the daemon
    daemon_log = pathlib.Path(started_daemon_client.daemon_log_file).read_text(encoding='utf-8')
    assert f'A subscriber with the process id<{node.pk}> already exists' in daemon_log


@pytest.fixture
def rabbitmq_client(aiida_profile):
    yield client.RabbitmqManagementClient(
        username=aiida_profile.process_control_config['broker_username'],
        password=aiida_profile.process_control_config['broker_password'],
        hostname=aiida_profile.process_control_config['broker_host'],
        virtual_host=aiida_profile.process_control_config['broker_virtual_host'],
    )


class TestRabbitmqManagementClient:
    """Tests for the :class:`aiida.brokers.rabbitmq.client.RabbitmqManagementClient`."""

    def test_is_connected(self, rabbitmq_client):
        """Test the :meth:`aiida.brokers.rabbitmq.client.RabbitmqManagementClient.is_connected`."""
        assert rabbitmq_client.is_connected

    def test_not_is_connected(self, rabbitmq_client, monkeypatch):
        """Test the :meth:`aiida.brokers.rabbitmq.client.RabbitmqManagementClient.is_connected` if not connected."""

        def raise_connection_error(*_):
            raise client.ManagementApiConnectionError

        monkeypatch.setattr(rabbitmq_client, 'request', raise_connection_error)
        assert not rabbitmq_client.is_connected

    def test_request(self, rabbitmq_client):
        """Test the :meth:`aiida.brokers.rabbitmq.client.RabbitmqManagementClient.request`."""
        response = rabbitmq_client.request('cluster-name')
        assert isinstance(response, requests.Response)
        assert response.ok

    def test_request_url_params(self, rabbitmq_client):
        """Test the :meth:`aiida.brokers.rabbitmq.client.RabbitmqManagementClient.request` with ``url_params``.

        Create a queue and delete it again.
        """
        name = f'test-queue-{uuid.uuid4()}'

        response = rabbitmq_client.request('queues/{virtual_host}/{name}', {'name': name}, method='PUT')
        assert isinstance(response, requests.Response)
        assert response.ok
        assert response.status_code == 201

        response = rabbitmq_client.request('queues/{virtual_host}/{name}', {'name': name}, method='DELETE')
        assert isinstance(response, requests.Response)
        assert response.ok
        assert response.status_code == 204
