"""Fixtures to simplify writing unit tests for AiiDA with ``pytest``."""
# AUTO-GENERATED

# fmt: off

from .configuration import (
    aiida_config,
    aiida_config_factory,
    aiida_config_tmp,
    aiida_profile,
    aiida_profile_clean,
    aiida_profile_clean_class,
    aiida_profile_factory,
    aiida_profile_tmp,
)
from .daemon import daemon_client, started_daemon_client, stopped_daemon_client, submit_and_await
from .entry_points import entry_points
from .globals import aiida_manager
from .orm import (
    aiida_code,
    aiida_code_installed,
    aiida_computer,
    aiida_computer_local,
    aiida_computer_ssh,
    aiida_computer_ssh_async,
    aiida_localhost,
    ssh_key,
)
from .storage import config_psql_dos, config_sqlite_dos, postgres_cluster

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
    'ssh_key',
    'started_daemon_client',
    'stopped_daemon_client',
    'submit_and_await',
)


# fmt: on
