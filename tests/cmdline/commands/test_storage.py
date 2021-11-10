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

from aiida.cmdline.commands import cmd_storage
from aiida.common import exceptions


@pytest.mark.usefixtures('clear_database_before_test')
def tests_storage_info(aiida_localhost, run_cli_command):
    """Test the ``verdi storage info`` command with the ``-statistics`` option."""
    from aiida import orm
    node = orm.Dict().store()

    result = run_cli_command(cmd_storage.storage_info, options=['--statistics'])

    assert aiida_localhost.label in result.output
    assert node.node_type in result.output


def tests_storage_migrate_force(run_cli_command):
    """Test the ``verdi storage migrate`` command (with force option)."""
    result = run_cli_command(cmd_storage.backend_migrate, options=['--force'])
    assert result.output == ''


def tests_storage_migrate_interactive(run_cli_command):
    """Test the ``verdi storage migrate`` command (with interactive prompt)."""
    from aiida.manage.manager import get_manager
    profile = get_manager().get_profile()

    result = run_cli_command(cmd_storage.backend_migrate, user_input='MIGRATE NOW')

    assert 'warning' in result.output.casefold()
    assert profile.name in result.output
    assert 'migrate now' in result.output.casefold()
    assert 'migration completed' in result.output.casefold()


def tests_storage_migrate_running_daemon(run_cli_command, monkeypatch):
    """Test that ``verdi storage migrate`` raises if the daemon is running."""
    from aiida.engine.daemon.client import DaemonClient

    def return_true():
        return True

    with monkeypatch.context() as mock_context:
        mock_context.setattr(DaemonClient, 'is_daemon_running', return_true)
        result = run_cli_command(cmd_storage.backend_migrate, raises=True)

    assert 'daemon' in result.output.casefold()
    assert 'running' in result.output.casefold()


def tests_storage_migrate_cancel_prompt(run_cli_command, monkeypatch):
    """Test that ``verdi storage migrate`` detects the cancelling of the interactive prompt."""
    import click

    def raise_click_abort(*args, **kwargs):
        raise click.Abort()

    with monkeypatch.context() as mock_context:
        mock_context.setattr(click, 'prompt', raise_click_abort)
        result = run_cli_command(cmd_storage.backend_migrate, raises=True)

    assert 'aborted' in result.output.casefold()


@pytest.mark.parametrize('raise_type', [
    exceptions.ConfigurationError,
    exceptions.DatabaseMigrationError,
])
@pytest.mark.parametrize(
    'call_kwargs', [
        {
            'raises': True,
            'user_input': 'MIGRATE NOW'
        },
        {
            'raises': True,
            'options': ['--force']
        },
    ]
)
def tests_storage_migrate_raises(run_cli_command, raise_type, call_kwargs, monkeypatch):
    """Test that ``verdi storage migrate`` detects errors while migrating.

    Note: I can't monkeypatch the result of `manager.get_backend` because the `backend_migrate`
    function actually calls `manager._load_backend` that will force the re-instantiation of
    the backend member of the manager, thus overwritting the patch. Instead I monkeypatched
    the `backend_migrate` directly so that it would return an object whose `migrate` method
    raises.
    """
    from aiida.manage.manager import get_manager
    manager = get_manager()

    def return_raiser(*args, **kwargs):

        class BackendRaiser():

            def migrate(self):  # pylint: disable=no-self-use
                raise raise_type('passed error message')

        return BackendRaiser()

    with monkeypatch.context() as mock_context:
        mock_context.setattr(manager, '_load_backend', return_raiser)
        result = run_cli_command(cmd_storage.backend_migrate, **call_kwargs)

    assert 'passed error message' in result.output
