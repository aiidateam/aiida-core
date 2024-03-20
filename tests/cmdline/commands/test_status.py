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
from aiida import __version__, get_profile
from aiida.cmdline.commands import cmd_status
from aiida.cmdline.utils.echo import ExitCode
from aiida.storage.psql_dos import migrator


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('stopped_daemon_client')
def test_status(run_cli_command):
    """Test `verdi status`."""
    options = []
    result = run_cli_command(cmd_status.verdi_status, options)

    # Even though the daemon should not be running, the return value should still be 0 corresponding to success
    assert 'The daemon is not running' in result.output
    assert result.exit_code is ExitCode.SUCCESS.value

    for string in ['config', 'profile', 'postgres', 'broker', 'daemon']:
        assert string in result.output

    assert __version__ in result.output


@pytest.mark.usefixtures('empty_config')
def test_status_no_profile(run_cli_command):
    """Test `verdi status` when there is no profile."""
    options = []
    result = run_cli_command(cmd_status.verdi_status, options, use_subprocess=False)
    assert 'no profile configured yet' in result.output


def test_status_no_rmq(run_cli_command):
    """Test `verdi status` without a check for RabbitMQ."""
    options = ['--no-rmq']
    result = run_cli_command(cmd_status.verdi_status, options)

    assert 'rabbitmq' not in result.output
    assert result.exit_code is ExitCode.SUCCESS.value

    for string in ['config', 'profile', 'postgres', 'daemon']:
        assert string in result.output


def test_storage_unable_to_connect(run_cli_command):
    """Test `verdi status` when there is an unknown error while connecting to the storage."""
    profile = get_profile()

    old_port = profile._attributes['storage']['config']['database_port']
    profile._attributes['storage']['config']['database_port'] = 123

    try:
        result = run_cli_command(cmd_status.verdi_status, raises=True, use_subprocess=False)
        assert "Unable to connect to profile's storage" in result.output
        assert result.exit_code is ExitCode.CRITICAL
    finally:
        profile._attributes['storage']['config']['database_port'] = old_port


def test_storage_incompatible(run_cli_command, monkeypatch):
    """Test `verdi status` when storage schema version is incompatible with that of the code."""

    def storage_cls(*args, **kwargs):
        from aiida.common.exceptions import IncompatibleStorageSchema

        raise IncompatibleStorageSchema()

    monkeypatch.setattr(migrator.PsqlDosMigrator, 'validate_storage', storage_cls)

    result = run_cli_command(cmd_status.verdi_status, raises=True, use_subprocess=False)
    assert 'verdi storage migrate' in result.output
    assert result.exit_code is ExitCode.CRITICAL


def test_storage_corrupted(run_cli_command, monkeypatch):
    """Test `verdi status` when the storage is found to be corrupt (e.g. non-matching repository UUIDs)."""

    def storage_cls(*args, **kwargs):
        from aiida.common.exceptions import CorruptStorage

        raise CorruptStorage()

    monkeypatch.setattr(migrator.PsqlDosMigrator, 'validate_storage', storage_cls)

    result = run_cli_command(cmd_status.verdi_status, raises=True, use_subprocess=False)
    assert 'Storage is corrupted' in result.output
    assert result.exit_code is ExitCode.CRITICAL
