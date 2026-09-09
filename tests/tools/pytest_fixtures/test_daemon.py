"""Tests for the :mod:`aiida.tools.pytest_fixtures.daemon` module."""

# This is needed when we run this file in isolation using
# the `--noconftest` pytest option in the 'test-pytest-fixtures' CI job.
pytest_plugins = ['aiida.tools.pytest_fixtures']


def test_daemon_client(daemon_client):
    """Test that the ``daemon_client`` fixture can start and stop the daemon."""
    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)

    daemon_client.start_daemon()
    daemon_client.stop_daemon(wait=True)


def test_started_daemon_client(started_daemon_client):
    """Test that the ``started_daemon_client`` fixture starts the daemon."""
    assert started_daemon_client.is_daemon_running


def test_stopped_daemon_client(stopped_daemon_client):
    """Test that the ``stopped_daemon_client`` fixture stops the daemon."""
    assert not stopped_daemon_client.is_daemon_running
