# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi status`."""
import pytest

from aiida import __version__
from aiida.cmdline.commands import cmd_status
from aiida.cmdline.utils.echo import ExitCode


@pytest.mark.requires_rmq
def test_status(run_cli_command):
    """Test `verdi status`."""
    options = []
    result = run_cli_command(cmd_status.verdi_status, options)

    # Even though the daemon should not be running, the return value should still be 0 corresponding to success
    assert 'The daemon is not running' in result.output
    assert result.exit_code is ExitCode.SUCCESS

    for string in ['config', 'profile', 'postgres', 'rabbitmq', 'daemon']:
        assert string in result.output

    assert __version__ in result.output


@pytest.mark.usefixtures('empty_config')
def test_status_no_profile(run_cli_command):
    """Test `verdi status` when there is no profile."""
    options = []
    result = run_cli_command(cmd_status.verdi_status, options)
    assert 'no profile configured yet' in result.output


def test_status_no_rmq(run_cli_command):
    """Test `verdi status` without a check for RabbitMQ."""
    options = ['--no-rmq']
    result = run_cli_command(cmd_status.verdi_status, options)

    assert 'rabbitmq' not in result.output
    assert result.exit_code is ExitCode.SUCCESS

    for string in ['config', 'profile', 'postgres', 'daemon']:
        assert string in result.output


def test_database_incompatible(run_cli_command, monkeypatch):
    """Test `verdi status` when database schema version is incompatible with that of the code."""
    from aiida.manage.manager import get_manager

    def get_backend():
        from aiida.common.exceptions import IncompatibleDatabaseSchema
        raise IncompatibleDatabaseSchema()

    monkeypatch.setattr(get_manager(), 'get_backend', get_backend)

    result = run_cli_command(cmd_status.verdi_status, raises=True)
    assert 'Database schema' in result.output
    assert 'is incompatible with the code.' in result.output
    assert '`verdi storage migrate`' in result.output
    assert result.exit_code is ExitCode.CRITICAL


def test_database_unable_to_connect(run_cli_command, monkeypatch):
    """Test `verdi status` when there is an unknown error while connecting to the database."""
    from aiida.manage.manager import get_manager

    profile = get_manager().get_profile()

    def get_backend():
        raise RuntimeError()

    monkeypatch.setattr(get_manager(), 'get_backend', get_backend)

    result = run_cli_command(cmd_status.verdi_status, raises=True)
    assert 'Unable to connect to database' in result.output
    assert profile.storage_config['database_name'] in result.output
    assert profile.storage_config['database_username'] in result.output
    assert profile.storage_config['database_hostname'] in result.output
    assert str(profile.storage_config['database_port']) in result.output
    assert result.exit_code is ExitCode.CRITICAL


@pytest.mark.usefixtures('aiida_profile')
def tests_database_version(run_cli_command, manager):
    """Test the ``verdi database version`` command."""
    backend_manager = manager.get_backend_manager()
    db_gen = backend_manager.get_schema_generation_database()
    db_ver = backend_manager.get_schema_version_backend()

    result = run_cli_command(cmd_status.verdi_status)
    assert f'{db_gen} / {db_ver}' in result.output
