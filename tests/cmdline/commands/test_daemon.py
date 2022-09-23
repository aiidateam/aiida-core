# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for ``verdi daemon``."""
import pytest

from aiida import get_profile
from aiida.cmdline.commands import cmd_daemon


def test_daemon_start(run_cli_command, stopped_daemon_client):
    """Test ``verdi daemon start``."""
    run_cli_command(cmd_daemon.start)

    daemon_response = stopped_daemon_client.get_daemon_info()
    worker_response = stopped_daemon_client.get_worker_info()

    assert 'status' in daemon_response
    assert daemon_response['status'] == 'ok'

    assert 'info' in worker_response
    assert len(worker_response['info']) == 1


@pytest.mark.parametrize('options', ([], ['--reset']))
def test_daemon_restart(run_cli_command, started_daemon_client, options):
    """Test ``verdi daemon restart`` both with and without ``--reset`` flag."""
    run_cli_command(cmd_daemon.restart, options)

    daemon_response = started_daemon_client.get_daemon_info()
    worker_response = started_daemon_client.get_worker_info()

    assert 'status' in daemon_response
    assert daemon_response['status'] == 'ok'

    assert 'info' in worker_response
    assert len(worker_response['info']) == 1


def test_daemon_start_number(run_cli_command, stopped_daemon_client):
    """Test ``verdi daemon start`` with a specific number of workers."""
    number = 4
    run_cli_command(cmd_daemon.start, [str(number)])

    daemon_response = stopped_daemon_client.get_daemon_info()
    worker_response = stopped_daemon_client.get_worker_info()

    assert 'status' in daemon_response
    assert daemon_response['status'] == 'ok'

    assert 'info' in worker_response
    assert len(worker_response['info']) == number


def test_daemon_start_number_config(run_cli_command, stopped_daemon_client, isolated_config):
    """Test ``verdi daemon start`` with ``daemon.default_workers`` config option being set."""
    number = 3
    isolated_config.set_option('daemon.default_workers', number, scope=get_profile().name)
    isolated_config.store()

    run_cli_command(cmd_daemon.start)

    daemon_response = stopped_daemon_client.get_daemon_info()
    worker_response = stopped_daemon_client.get_worker_info()

    assert 'status' in daemon_response
    assert daemon_response['status'] == 'ok'

    assert 'info' in worker_response
    assert len(worker_response['info']) == number


def test_foreground_multiple_workers(run_cli_command):
    """Test `verdi daemon start` in foreground with more than one worker will fail."""
    run_cli_command(cmd_daemon.start, ['--foreground', str(4)], raises=True)


@pytest.mark.usefixtures('started_daemon_client', 'isolated_config')
def test_daemon_status(run_cli_command):
    """Test ``verdi daemon status``."""
    result = run_cli_command(cmd_daemon.status)
    last_line = result.output_lines[-1]

    assert f'Profile: {get_profile().name}' in result.output
    assert last_line == 'Use verdi daemon [incr | decr] [num] to increase / decrease the amount of workers'
