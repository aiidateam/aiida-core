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
from plumpy.process_comms import RemoteProcessThreadController

from aiida.cmdline.commands import cmd_rabbitmq
from aiida.engine import ProcessState, submit
from aiida.engine.processes import control
from aiida.orm import Int


@pytest.mark.requires_rmq
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
    monkeypatch.setattr(control, 'get_process_tasks', lambda *args: [1, 2, 3])

    result = run_cli_command(cmd_rabbitmq.cmd_tasks_list, use_subprocess=False)
    assert result.output == '1\n2\n3\n'


@pytest.mark.usefixtures('started_daemon_client')
def test_tasks_analyze_running_daemon(run_cli_command):
    """Test the ``tasks analyze`` command excepts when the daemon is running.

    This is a copy of the test for the equivalent ``verdi process repair`` since it just forwards to that command.
    """
    result = run_cli_command(cmd_rabbitmq.cmd_tasks_analyze, raises=True, use_subprocess=False)
    assert 'The daemon needs to be stopped before running this command.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_tasks_analyze_consistent(monkeypatch, run_cli_command):
    """Test the ``tasks analyze`` command when everything is consistent.

    This is a copy of the test for the equivalent ``verdi process repair`` since it just forwards to that command.
    """
    monkeypatch.setattr(control, 'get_active_processes', lambda *args, **kwargs: [1, 2, 3])
    monkeypatch.setattr(control, 'get_process_tasks', lambda *args: [1, 2, 3])

    result = run_cli_command(cmd_rabbitmq.cmd_tasks_analyze, use_subprocess=False)
    assert 'No inconsistencies detected between database and RabbitMQ.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_tasks_revive_without_daemon(run_cli_command):
    """Test that ``tasks revive`` fails if no daemon is running."""
    assert run_cli_command(cmd_rabbitmq.cmd_tasks_revive, raises=True)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_revive(run_cli_command, monkeypatch, aiida_code_installed, submit_and_await):
    """Test ``tasks revive``."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder = code.get_builder()
    builder.x = Int(1)
    builder.y = Int(1)
    builder.metadata.options.resources = {'num_machines': 1}

    # Temporarily patch the ``RemoteProcessThreadController.continue_process`` method to do nothing and just return a
    # completed future. This ensures that the submission creates a process node in the database but no task is sent to
    # RabbitMQ and so the daemon will not start running it.
    with monkeypatch.context() as context:
        context.setattr(RemoteProcessThreadController, 'continue_process', lambda *args, **kwargs: None)
        node = submit(builder)

    # The node should now be created in the database but "stuck"
    assert node.process_state == ProcessState.CREATED

    # Time to revive it by recreating the task and send it to RabbitMQ
    run_cli_command(cmd_rabbitmq.cmd_tasks_revive, [str(node.pk), '--force'], use_subprocess=False)

    # Wait for the process to be picked up by the daemon and completed. If there is a problem with the code, this call
    # should timeout and raise an exception
    submit_and_await(node)
    assert node.is_finished_ok
