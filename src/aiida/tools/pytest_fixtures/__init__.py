"""Fixtures to simplify writing unit tests for AiiDA with ``pytest``."""
# AUTO-GENERATED

# fmt: off

from aiida.tools.pytest_fixtures.broker import run_aiida_broker_service, run_aiida_broker_service_for_profile
from aiida.tools.pytest_fixtures.configuration import (
    aiida_config,
    aiida_config_factory,
    aiida_config_tmp,
    aiida_profile,
    aiida_profile_clean,
    aiida_profile_clean_class,
    aiida_profile_factory,
    aiida_profile_tmp,
)
from aiida.tools.pytest_fixtures.daemon import (
    daemon_client,
    started_daemon_client,
    stopped_daemon_client,
    submit_and_await,
)
from aiida.tools.pytest_fixtures.entry_points import entry_points
from aiida.tools.pytest_fixtures.globals import aiida_manager
from aiida.tools.pytest_fixtures.orm import (
    aiida_code,
    aiida_code_installed,
    aiida_computer,
    aiida_computer_local,
    aiida_computer_ssh,
    aiida_computer_ssh_async,
    aiida_localhost,
    ssh_key,
)
from aiida.tools.pytest_fixtures.storage import config_psql_dos, config_sqlite_dos, postgres_cluster

__all__ = (
    'aiida_code',
    'aiida_code_installed',
    'aiida_computer',
    'aiida_computer_local',
    'aiida_computer_ssh',
    'aiida_computer_ssh_async',
    'aiida_config',
    'aiida_config_factory',
    'aiida_config_tmp',
    'aiida_localhost',
    'aiida_manager',
    'aiida_profile',
    'aiida_profile_clean',
    'aiida_profile_clean_class',
    'aiida_profile_factory',
    'aiida_profile_tmp',
    'config_psql_dos',
    'config_sqlite_dos',
    'daemon_client',
    'entry_points',
    'postgres_cluster',
    'run_aiida_broker_service',
    'run_aiida_broker_service_for_profile',
    'ssh_key',
    'started_daemon_client',
    'stopped_daemon_client',
    'submit_and_await',
)


# fmt: on
