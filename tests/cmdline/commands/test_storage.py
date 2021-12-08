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
    result = run_cli_command(cmd_storage.storage_migrate, options=['--force'])
    assert result.output == ''


def tests_storage_migrate_interactive(run_cli_command):
    """Test the ``verdi storage migrate`` command (with interactive prompt)."""
    from aiida.manage.manager import get_manager
    profile = get_manager().get_profile()

    result = run_cli_command(cmd_storage.storage_migrate, user_input='MIGRATE NOW')

    assert 'warning' in result.output.lower()
    assert profile.name in result.output
    assert 'migrate now' in result.output.lower()
    assert 'migration completed' in result.output.lower()


def tests_storage_migrate_running_daemon(run_cli_command, monkeypatch):
    """Test that ``verdi storage migrate`` raises if the daemon is running."""
    from aiida.engine.daemon.client import DaemonClient

    monkeypatch.setattr(DaemonClient, 'is_daemon_running', lambda: True)
    result = run_cli_command(cmd_storage.storage_migrate, raises=True)

    assert 'daemon' in result.output.lower()
    assert 'running' in result.output.lower()


def tests_storage_migrate_cancel_prompt(run_cli_command, monkeypatch):
    """Test that ``verdi storage migrate`` detects the cancelling of the interactive prompt."""
    import click

    monkeypatch.setattr(click, 'prompt', lambda text, **kwargs: exec('import click\nraise click.Abort()'))  # pylint: disable=exec-used
    result = run_cli_command(cmd_storage.storage_migrate, raises=True)

    assert 'aborted' in result.output.lower()


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

    Note: it is not enough to monkeypatch the backend object returned by  the method
    `manager.get_backend` because the CLI function `storage_migrate` will first call
    `manager._load_backend`, whichforces the re-instantiation of this object.
    Instead, the class of the object needs to be patched so that all further created
    objects will have the modified method.
    """
    from aiida.manage.manager import get_manager
    manager = get_manager()

    def mocked_migrate(self):  # pylint: disable=no-self-use
        raise raise_type('passed error message')

    monkeypatch.setattr(manager.get_backend().__class__, 'migrate', mocked_migrate)
    result = run_cli_command(cmd_storage.storage_migrate, **call_kwargs)

    assert result.exc_info[0] is SystemExit
    assert 'Critical:' in result.output
    assert 'passed error message' in result.output


def tests_storage_maintain_logging(run_cli_command, monkeypatch, caplog):
    """Test all the information and cases of the storage maintain command."""
    import logging

    from aiida.backends import control

    def mock_maintain(**kwargs):
        logmsg = 'Provided kwargs:\n'
        for key, val in kwargs.items():
            logmsg += f' > {key}: {val}\n'
        logging.info(logmsg)

    monkeypatch.setattr(control, 'repository_maintain', mock_maintain)

    with caplog.at_level(logging.INFO):
        _ = run_cli_command(cmd_storage.storage_maintain, user_input='Y')

    message_list = caplog.records[0].msg.splitlines()
    assert ' > full: False' in message_list
    assert ' > dry_run: False' in message_list

    with caplog.at_level(logging.INFO):
        _ = run_cli_command(cmd_storage.storage_maintain, options=['--dry-run'])

    message_list = caplog.records[1].msg.splitlines()
    assert ' > full: False' in message_list
    assert ' > dry_run: True' in message_list

    with caplog.at_level(logging.INFO):
        run_cli_command(cmd_storage.storage_maintain, options=['--full'], user_input='Y')

    message_list = caplog.records[2].msg.splitlines()
    assert ' > full: True' in message_list
    assert ' > dry_run: False' in message_list
