# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi storage`."""
import pytest

from aiida import get_profile
from aiida.cmdline.commands import cmd_storage
from aiida.common import exceptions


def tests_storage_version(run_cli_command):
    """Test the ``verdi storage version`` command."""
    result = run_cli_command(cmd_storage.storage_version)
    version = get_profile().storage_cls.version_profile(get_profile())
    assert version in result.output


def tests_storage_info(aiida_localhost, run_cli_command):
    """Test the ``verdi storage info`` command with the ``--detailed`` option."""
    from aiida import orm
    node = orm.Dict().store()

    result = run_cli_command(cmd_storage.storage_info, parameters=['--detailed'])

    assert aiida_localhost.label in result.output
    assert node.node_type in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def tests_storage_migrate_force(run_cli_command):
    """Test the ``verdi storage migrate`` command (with force option)."""
    result = run_cli_command(cmd_storage.storage_migrate, parameters=['--force'])
    assert 'Migrating to the head of the main branch' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def tests_storage_migrate_interactive(run_cli_command):
    """Test the ``verdi storage migrate`` command (with interactive prompt)."""
    from aiida.manage import get_manager
    profile = get_manager().get_profile()

    result = run_cli_command(cmd_storage.storage_migrate, user_input='MIGRATE NOW')

    assert 'warning' in result.output.lower()
    assert profile.name in result.output
    assert 'migrate now' in result.output.lower()
    assert 'migration completed' in result.output.lower()


@pytest.mark.usefixtures('started_daemon_client')
def tests_storage_migrate_running_daemon(run_cli_command):
    """Test that ``verdi storage migrate`` raises if the daemon is running."""
    result = run_cli_command(cmd_storage.storage_migrate, raises=True)

    assert 'daemon' in result.output.lower()
    assert 'running' in result.output.lower()


@pytest.mark.usefixtures('stopped_daemon_client')
def tests_storage_migrate_cancel_prompt(run_cli_command, monkeypatch):
    """Test that ``verdi storage migrate`` detects the cancelling of the interactive prompt."""
    import click

    monkeypatch.setattr(click, 'prompt', lambda text, **kwargs: exec('import click\nraise click.Abort()'))  # pylint: disable=exec-used
    result = run_cli_command(cmd_storage.storage_migrate, raises=True, use_subprocess=False)

    assert 'aborted' in result.output.lower()


@pytest.mark.parametrize('raise_type', [
    exceptions.ConfigurationError,
    exceptions.StorageMigrationError,
])
@pytest.mark.parametrize(
    'call_kwargs', [
        {
            'raises': True,
            'user_input': 'MIGRATE NOW'
        },
        {
            'raises': True,
            'parameters': ['--force']
        },
    ]
)
@pytest.mark.usefixtures('stopped_daemon_client')
def tests_storage_migrate_raises(run_cli_command, raise_type, call_kwargs, monkeypatch):
    """Test that ``verdi storage migrate`` detects errors while migrating.

    Note: it is not enough to monkeypatch the backend object returned by  the method
    `manager.get_backend` because the CLI function `storage_migrate` will first call
    `manager._load_backend`, whichforces the re-instantiation of this object.
    Instead, the class of the object needs to be patched so that all further created
    objects will have the modified method.
    """
    from aiida.manage import get_manager
    manager = get_manager()

    def mocked_migrate(self):
        raise raise_type('passed error message')

    monkeypatch.setattr(manager.get_profile_storage().__class__, 'migrate', mocked_migrate)
    result = run_cli_command(cmd_storage.storage_migrate, **call_kwargs, use_subprocess=False)

    assert result.exc_info[0] is SystemExit
    assert 'Critical:' in result.output
    assert 'passed error message' in result.output


def tests_storage_maintain_logging(run_cli_command, monkeypatch):
    """Test all the information and cases of the storage maintain command."""
    from aiida.common.log import AIIDA_LOGGER
    from aiida.manage import get_manager
    storage = get_manager().get_profile_storage()

    def mock_maintain(*args, **kwargs):
        """Mocks for `maintain` method of `storage`, logging the inputs passed."""
        log_message = ''

        log_message += 'Provided args:\n'
        for arg in args:
            log_message += f' > {arg}\n'

        log_message += 'Provided kwargs:\n'
        for key, val in kwargs.items():
            log_message += f' > {key}: {val}\n'

        AIIDA_LOGGER.report(log_message)

    monkeypatch.setattr(storage, 'maintain', mock_maintain)

    # Not passing user input should cause the command to exit without executing `storage.mantain` and so the last
    # message should be the prompt to continue or not.
    result = run_cli_command(cmd_storage.storage_maintain, use_subprocess=False)
    message_list = result.output_lines
    assert message_list[-1] == 'Are you sure you want continue in this mode? [y/N]: '

    # Test `storage.mantain` with `--force`
    result = run_cli_command(cmd_storage.storage_maintain, parameters=['--force', '--compress'], use_subprocess=False)
    message_list = result.output_lines
    assert ' > full: False' in message_list
    assert ' > dry_run: False' in message_list
    assert ' > compress: True' in message_list

    # Test `storage.mantain` with user input Y
    result = run_cli_command(cmd_storage.storage_maintain, user_input='Y', use_subprocess=False)
    message_list = result.output_lines
    assert ' > full: False' in message_list
    assert ' > dry_run: False' in message_list
    assert ' > compress: False' in message_list

    # Test `storage.mantain` with `--dry-run`
    result = run_cli_command(cmd_storage.storage_maintain, parameters=['--dry-run'], use_subprocess=False)
    message_list = result.output_lines
    assert ' > full: False' in message_list
    assert ' > dry_run: True' in message_list

    # Test `storage.mantain` with `--full`
    result = run_cli_command(cmd_storage.storage_maintain, parameters=['--full'], user_input='Y', use_subprocess=False)
    message_list = result.output_lines
    assert ' > full: True' in message_list
    assert ' > dry_run: False' in message_list

    # Test `storage.mantain` with `--full` and `--no-repack`
    result = run_cli_command(
        cmd_storage.storage_maintain, parameters=['--full', '--no-repack'], user_input='Y', use_subprocess=False
    )
    message_list = result.output_lines
    assert ' > full: True' in message_list
    assert ' > do_repack: False' in message_list
    assert ' > dry_run: False' in message_list
