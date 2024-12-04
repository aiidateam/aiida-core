###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi daemon``."""

import textwrap
from unittest.mock import patch

import pytest

from aiida import get_profile
from aiida.cmdline.commands import cmd_daemon
from aiida.engine.daemon.client import DaemonClient

pytestmark = pytest.mark.requires_rmq


def format_local_time(timestamp, format_str='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object or UNIX timestamp in a human readable format

    Mocked version of :func:`aiida.cmdline.utils.common.format_local_time` that does not consider the local timezone as
    that will mess up the tests.

    :param timestamp: a datetime object or a float representing a UNIX timestamp
    :param format_str: optional string format to pass to strftime
    """
    from datetime import datetime, timezone

    return datetime.fromtimestamp(timestamp, timezone.utc).strftime(format_str)


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

    run_cli_command(cmd_daemon.start, use_subprocess=False)

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
    assert last_line == 'Use `verdi daemon [incr | decr] [num]` to increase / decrease the number of workers'


@pytest.mark.usefixtures('empty_config')
def test_daemon_status_no_profile(run_cli_command):
    """Test ``verdi daemon status`` when no profiles are defined."""
    result = run_cli_command(cmd_daemon.status, raises=True)
    assert 'No profile loaded: make sure at least one profile is configured and a default is set.' in result.output


@pytest.mark.usefixtures('started_daemon_client', 'isolated_config')
def test_daemon_status_timeout(run_cli_command):
    """Test ``verdi daemon status`` with the ``--timeout`` option.

    This will just test the timeout is accepted and doesn't cause an exception. It is not testing whether the command
    will actually timeout if provided a small number, but that is difficult to make reproducible in a test environment.
    """
    result = run_cli_command(cmd_daemon.status, ['--timeout', '5'])
    last_line = result.output_lines[-1]

    assert f'Profile: {get_profile().name}' in result.output
    assert last_line == 'Use `verdi daemon [incr | decr] [num]` to increase / decrease the number of workers'


def get_daemon_info(_):
    """Mock replacement of :meth:`aiida.engine.daemon.client.DaemonClient.get_daemon_info`."""
    return {
        'status': 'ok',
        'time': 1576588772.459435,
        'info': {
            'cpu': 0.0,
            'mem': 0.028,
            'pid': 111015,
            'create_time': 1576582938.75,
        },
        'id': 'a1c0d76c94304d62adfb36e30d335dd0',
    }


def get_worker_info(_):
    """Mock replacement of :meth:`aiida.engine.daemon.client.DaemonClient.get_worker_info`."""
    return {
        'status': 'ok',
        'time': 1576585659.221961,
        'name': 'aiida-production',
        'info': {
            '4990': {
                'cpu': 0.0,
                'mem': 0.231,
                'pid': 4990,
                'create_time': 1576585658.730482,
            }
        },
        'id': '4e1d768a522a44b59f85039806f9af14',
    }


def get_worker_info_broken(_):
    """Mock replacement of :meth:`aiida.engine.daemon.client.DaemonClient.get_worker_info`.

    This response simulations the event where the circus daemon cannot get the stats from one of the workers.
    """
    return {
        'status': 'ok',
        'time': 1576585659.221961,
        'name': 'aiida-production',
        'info': {'4990': 'No such process (stopped?)'},
        'id': '4e1d768a522a44b59f85039806f9af14',
    }


@patch.object(DaemonClient, 'get_status', lambda *_, **__: {'status': 'running'})
@patch.object(DaemonClient, 'get_daemon_info', get_daemon_info)
@patch.object(DaemonClient, 'get_worker_info', get_worker_info)
@patch('aiida.cmdline.utils.common.format_local_time', format_local_time)
def test_daemon_status_worker_info(run_cli_command):
    """Test `get_status` output if everything is working normally with a single worker."""
    literal = textwrap.dedent(
        """\
        Daemon is running as PID 111015 since 2019-12-17 11:42:18
        Active workers [1]:
          PID    MEM %    CPU %  started
        -----  -------  -------  -------------------
         4990    0.231        0  2019-12-17 12:27:38
        Use `verdi daemon [incr | decr] [num]` to increase / decrease the number of workers"""
    )
    result = run_cli_command(cmd_daemon.status)
    assert literal in result.output


@patch.object(DaemonClient, 'get_status', lambda *_, **__: {'status': 'running'})
@patch.object(DaemonClient, 'get_daemon_info', get_daemon_info)
@patch.object(DaemonClient, 'get_worker_info', get_worker_info_broken)
@patch('aiida.cmdline.utils.common.format_local_time', format_local_time)
def test_daemon_status_worker_timeout(run_cli_command):
    """Test `get_status` output if a daemon worker cannot be reached by the circus daemon."""
    literal = textwrap.dedent(
        """\
        Daemon is running as PID 111015 since 2019-12-17 11:42:18
        Active workers [1]:
          PID  MEM %    CPU %    started
        -----  -------  -------  ---------
         4990  -        -        -
        Use `verdi daemon [incr | decr] [num]` to increase / decrease the number of workers"""
    )
    result = run_cli_command(cmd_daemon.status)
    assert literal in result.output
