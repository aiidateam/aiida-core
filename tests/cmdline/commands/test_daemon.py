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

from aiida.cmdline.commands import cmd_daemon


def test_daemon_start(run_cli_command, daemon_client):
    """Test ``verdi daemon start``."""
    run_cli_command(cmd_daemon.start)

    daemon_response = daemon_client.get_daemon_info()
    worker_response = daemon_client.get_worker_info()

    assert 'status' in daemon_response
    assert daemon_response['status'] == 'ok'

    assert 'info' in worker_response
    assert len(worker_response['info']) == 1


def test_daemon_restart(run_cli_command, daemon_client):
    """Test ``verdi daemon restart`` both with and without ``--reset`` flag."""
    run_cli_command(cmd_daemon.start, [])
    run_cli_command(cmd_daemon.restart, [])
    run_cli_command(cmd_daemon.restart, ['--reset'])

    daemon_response = daemon_client.get_daemon_info()
    worker_response = daemon_client.get_worker_info()

    assert 'status' in daemon_response
    assert daemon_response['status'] == 'ok'

    assert 'info' in worker_response
    assert len(worker_response['info']) == 1


def test_daemon_start_number(run_cli_command, daemon_client):
    """Test ``verdi daemon start`` with a specific number of workers."""
    number = 4
    run_cli_command(cmd_daemon.start, [str(number)])

    daemon_response = daemon_client.get_daemon_info()
    worker_response = daemon_client.get_worker_info()

    assert 'status' in daemon_response
    assert daemon_response['status'] == 'ok'

    assert 'info' in worker_response
    assert len(worker_response['info']) == number


def test_daemon_start_number_config(run_cli_command, daemon_client, isolated_config):
    """Test ``verdi daemon start`` with ``daemon.default_workers`` config option being set."""
    number = 3
    isolated_config.set_option('daemon.default_workers', number, scope=isolated_config.current_profile.name)
    isolated_config.store()

    run_cli_command(cmd_daemon.start)

    daemon_response = daemon_client.get_daemon_info()
    worker_response = daemon_client.get_worker_info()

    assert 'status' in daemon_response
    assert daemon_response['status'] == 'ok'

    assert 'info' in worker_response
    assert len(worker_response['info']) == number


@pytest.mark.usefixtures('daemon_client')
def test_foreground_multiple_workers(run_cli_command):
    """Test `verdi daemon start` in foreground with more than one worker will fail."""
    run_cli_command(cmd_daemon.start, ['--foreground', str(4)], raises=True)


@pytest.mark.usefixtures('daemon_client')
def test_daemon_status(run_cli_command, isolated_config):
    """Test ``verdi daemon status``."""
    run_cli_command(cmd_daemon.start)
    result = run_cli_command(cmd_daemon.status)
    last_line = result.output_lines[-1]

    assert f'Profile: {isolated_config.current_profile.name}' in result.output
    assert last_line == 'Use verdi daemon [incr | decr] [num] to increase / decrease the amount of workers'
