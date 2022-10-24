# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi devel rabbitmq``."""
import pytest

from aiida.cmdline.commands import cmd_rabbitmq


def test_queues_list(run_cli_command):
    """Test the ``queues list``"""
    result = run_cli_command(cmd_rabbitmq.cmd_queues_list)
    assert result.output


@pytest.mark.usefixtures('started_daemon_client')
def test_tasks_list_running_daemon(run_cli_command):
    """Test the ``tasks list`` command excepts when the daemon is running."""
    result = run_cli_command(cmd_rabbitmq.cmd_tasks_list, raises=True)
    assert 'The daemon needs to be stopped before running this command.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_tasks_list(monkeypatch, run_cli_command):
    """Test the ``tasks list`` command when everything is consistent."""
    monkeypatch.setattr(cmd_rabbitmq, 'get_process_tasks', lambda *args: [1, 2, 3])

    result = run_cli_command(cmd_rabbitmq.cmd_tasks_list)
    assert result.output == '1\n2\n3\n'


@pytest.mark.usefixtures('started_daemon_client')
def test_tasks_analyze_running_daemon(run_cli_command):
    """Test the ``tasks analyze`` command excepts when the daemon is running."""
    result = run_cli_command(cmd_rabbitmq.cmd_tasks_analyze, raises=True)
    assert 'The daemon needs to be stopped before running this command.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_tasks_analyze_consistent(monkeypatch, run_cli_command):
    """Test the ``tasks analyze`` command when everything is consistent."""
    monkeypatch.setattr(cmd_rabbitmq, 'get_active_processes', lambda *args: [1, 2, 3])
    monkeypatch.setattr(cmd_rabbitmq, 'get_process_tasks', lambda *args: [1, 2, 3])

    result = run_cli_command(cmd_rabbitmq.cmd_tasks_analyze)
    assert 'No inconsistencies detected between database and RabbitMQ.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_tasks_analyze_duplicate_tasks(monkeypatch, run_cli_command):
    """Test the ``tasks analyze`` command when there are duplicate tasks."""
    monkeypatch.setattr(cmd_rabbitmq, 'get_active_processes', lambda *args: [1, 2])
    monkeypatch.setattr(cmd_rabbitmq, 'get_process_tasks', lambda *args: [1, 2, 2])

    result = run_cli_command(cmd_rabbitmq.cmd_tasks_analyze, raises=True)
    assert 'There are duplicates process tasks:' in result.output
    assert 'Inconsistencies detected between database and RabbitMQ.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_tasks_analyze_additional_tasks(monkeypatch, run_cli_command):
    """Test the ``tasks analyze`` command when there are additional tasks."""
    monkeypatch.setattr(cmd_rabbitmq, 'get_active_processes', lambda *args: [1, 2])
    monkeypatch.setattr(cmd_rabbitmq, 'get_process_tasks', lambda *args: [1, 2, 3])

    result = run_cli_command(cmd_rabbitmq.cmd_tasks_analyze, raises=True)
    assert 'There are process tasks for terminated processes:' in result.output
    assert 'Inconsistencies detected between database and RabbitMQ.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_tasks_analyze_missing_tasks(monkeypatch, run_cli_command):
    """Test the ``tasks analyze`` command when there are missing tasks."""
    monkeypatch.setattr(cmd_rabbitmq, 'get_active_processes', lambda *args: [1, 2, 3])
    monkeypatch.setattr(cmd_rabbitmq, 'get_process_tasks', lambda *args: [1, 2])

    result = run_cli_command(cmd_rabbitmq.cmd_tasks_analyze, raises=True)
    assert 'There are active processes without process task:' in result.output
    assert 'Inconsistencies detected between database and RabbitMQ.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_tasks_analyze_verbosity(monkeypatch, run_cli_command):
    """Test the ``tasks analyze`` command with ``-v INFO```."""
    monkeypatch.setattr(cmd_rabbitmq, 'get_active_processes', lambda *args: [1, 2, 3, 4])
    monkeypatch.setattr(cmd_rabbitmq, 'get_process_tasks', lambda *args: [1, 2])

    result = run_cli_command(cmd_rabbitmq.cmd_tasks_analyze, ['-v', 'INFO'], raises=True)
    assert 'Active processes: [1, 2, 3, 4]' in result.output
    assert 'Process tasks: [1, 2]' in result.output
