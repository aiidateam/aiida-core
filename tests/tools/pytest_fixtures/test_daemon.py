"""Tests for the :mod:`aiida.manage.tests.pytest_fixtures` module."""

import pytest

# This is needed when we run this file in isolation using
# the `--noconftest` pytest option in the 'test-pytest-fixtures' CI job.
pytest_plugins = ['aiida.tools.pytest_fixtures']


@pytest.fixture
def aiida_profile_with_rmq(aiida_config, aiida_profile_factory, config_sqlite_dos):
    """Create and load a profile with ``core.psql_dos`` as a storage backend and RabbitMQ as the broker."""
    with aiida_profile_factory(
        aiida_config,
        storage_backend='core.sqlite_dos',
        storage_config=config_sqlite_dos(),
        broker_backend='core.rabbitmq',
    ) as profile:
        yield profile


def test_deamon_client(aiida_profile_with_rmq, daemon_client):
    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)
    daemon_client.start_daemon()
    daemon_client.stop_daemon(wait=True)


def test_started_daemon_client(aiida_profile_with_rmq, started_daemon_client):
    assert started_daemon_client.is_daemon_running


def test_stopped_daemon_client(aiida_profile_with_rmq, stopped_daemon_client):
    assert not stopped_daemon_client.is_daemon_running
