"""Tests for the :mod:`aiida.tools.pytest_fixtures.daemon` module."""

from aiida.engine.daemon.client import DaemonTimeoutException

# This is needed when we run this file in isolation using
# the `--noconftest` pytest option in the 'test-pytest-fixtures' CI job.
pytest_plugins = ['aiida.tools.pytest_fixtures']


def test_daemon_client(stopped_daemon_client):
    """Test that the ``daemon_client`` fixture can start and stop the daemon."""
    stopped_daemon_client.start_daemon()
    stopped_daemon_client._await_condition(
        lambda: stopped_daemon_client.is_daemon_running,
        DaemonTimeoutException('The daemon failed to start.'),
    )

    stopped_daemon_client.stop_daemon(wait=True)
    stopped_daemon_client._await_condition(
        lambda: not stopped_daemon_client.is_daemon_running,
        DaemonTimeoutException('The daemon failed to stop.'),
    )


def test_started_daemon_client(started_daemon_client):
    """Test that the ``started_daemon_client`` fixture starts the daemon."""
    started_daemon_client._await_condition(
        lambda: started_daemon_client.is_daemon_running,
        DaemonTimeoutException('The daemon failed to start.'),
    )


def test_stopped_daemon_client(stopped_daemon_client):
    """Test that the ``stopped_daemon_client`` fixture stops the daemon."""
    stopped_daemon_client._await_condition(
        lambda: not stopped_daemon_client.is_daemon_running,
        DaemonTimeoutException('The daemon failed to stop.'),
    )
