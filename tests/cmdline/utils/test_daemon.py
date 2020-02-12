# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for daemon command line utilities."""
from unittest.mock import patch

from aiida.cmdline.utils.daemon import get_daemon_status
from aiida.engine.daemon.client import DaemonClient, get_daemon_client


def format_local_time(timestamp, format_str='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object or UNIX timestamp in a human readable format

    Mocked version of :func:`aiida.cmdline.utils.common.format_local_time` that does not consider the local timezone as
    that will mess up the tests.

    :param timestamp: a datetime object or a float representing a UNIX timestamp
    :param format_str: optional string format to pass to strftime
    """
    from datetime import datetime
    return datetime.utcfromtimestamp(timestamp).strftime(format_str)


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
        'id': 'a1c0d76c94304d62adfb36e30d335dd0'
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
        'id': '4e1d768a522a44b59f85039806f9af14'
    }


def get_worker_info_broken(_):
    """Mock replacement of :meth:`aiida.engine.daemon.client.DaemonClient.get_worker_info`.

    This response simulations the event where the circus daemon cannot get the stats from one of the workers.
    """
    return {
        'status': 'ok',
        'time': 1576585659.221961,
        'name': 'aiida-production',
        'info': {
            '4990': 'No such process (stopped?)'
        },
        'id': '4e1d768a522a44b59f85039806f9af14'
    }


def compare_string_literals(left, right):
    """Assert that two multiline strings are equal.

    The strings are split on newlines and the lines are compared with leading and trailing whitespace stripped.

    :param left: first multiline string
    :param right: seconds multiline string
    :raises AssertionError: if strings are different excluding leading and trailing whitespace in lines
    """
    lines_left = [line.strip() for line in left.split('\n') if line.strip()]
    lines_right = [line.strip() for line in right.split('\n') if line.strip()]
    assert len(lines_left) == len(lines_right)
    for line_left, line_right in zip(lines_left, lines_right):
        assert line_left == line_right


def test_daemon_not_running():
    """Test `get_daemon_status` output when the daemon is not running."""
    client = get_daemon_client()
    assert 'The daemon is not running' in get_daemon_status(client)
    assert not client.is_daemon_running


@patch.object(DaemonClient, 'is_daemon_running', lambda: True)
def test_circus_timeout():
    """Test `get_daemon_status` output when the circus daemon process cannot be reached."""
    client = get_daemon_client()
    assert 'Call to the circus controller timed out' in get_daemon_status(client)


@patch.object(DaemonClient, 'is_daemon_running', lambda: True)
@patch.object(DaemonClient, 'get_daemon_info', get_daemon_info)
@patch.object(DaemonClient, 'get_worker_info', get_worker_info)
@patch('aiida.cmdline.utils.common.format_local_time', format_local_time)
def test_daemon_working():
    """Test `get_daemon_status` output if everything is working normally with a single worker."""
    client = get_daemon_client()
    literal = """\
Daemon is running as PID 111015 since 2019-12-17 11:42:18
Active workers [1]:
  PID    MEM %    CPU %  started
-----  -------  -------  -------------------
 4990    0.231        0  2019-12-17 12:27:38
Use verdi daemon [incr | decr] [num] to increase / decrease the amount of workers"""
    assert get_daemon_status(client) == literal
    assert client.is_daemon_running


@patch.object(DaemonClient, 'is_daemon_running', lambda: True)
@patch.object(DaemonClient, 'get_daemon_info', get_daemon_info)
@patch.object(DaemonClient, 'get_worker_info', get_worker_info_broken)
@patch('aiida.cmdline.utils.common.format_local_time', format_local_time)
def test_daemon_worker_timeout():
    """Test `get_daemon_status` output if a daemon worker cannot be reached by the circus daemon."""
    client = get_daemon_client()
    literal = """\
Daemon is running as PID 111015 since 2019-12-17 11:42:18
Active workers [1]:
  PID  MEM %    CPU %    started
-----  -------  -------  ---------
 4990  -        -        -
Use verdi daemon [incr | decr] [num] to increase / decrease the amount of workers"""
    compare_string_literals(get_daemon_status(client), literal)
