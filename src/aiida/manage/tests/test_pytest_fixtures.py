pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


def test_fixtures(aiida_profile_clean, daemon_client):
    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)
    daemon_client.start_daemon()
    daemon_client.stop_daemon(wait=True)
