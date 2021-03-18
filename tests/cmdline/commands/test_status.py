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
    assert 'Database schema version is incompatible with the code: run `verdi database migrate`.' in result.output
    assert result.exit_code is ExitCode.CRITICAL
