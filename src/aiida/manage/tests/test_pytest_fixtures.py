"""Tests for the :mod:`aiida.manage.tests.pytest_fixtures` module."""

pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


def test_deamon_client(daemon_client):
    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)
    daemon_client.start_daemon()
    daemon_client.stop_daemon(wait=True)


def test_started_daemon_client(started_daemon_client):
    assert started_daemon_client.is_daemon_running


def test_stopped_daemon_client(stopped_daemon_client):
    assert not stopped_daemon_client.is_daemon_running
