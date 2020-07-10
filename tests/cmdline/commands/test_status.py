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


def test_status(run_cli_command):
    """Test `verdi status`."""
    options = []
    result = run_cli_command(cmd_status.verdi_status, options)

    # Even though the daemon should not be running, the return value should still be 0 corresponding to success
    assert 'The daemon is not running' in result.output
    assert result.exit_code is ExitCode.SUCCESS

    for string in ['config', 'profile', 'postgres', 'rabbitmq', 'daemon']:
        assert string in result.output


@pytest.mark.usefixtures('create_empty_config_instance')
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
