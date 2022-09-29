# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi devel``."""
from plumpy.process_comms import RemoteProcessThreadController
from plumpy.process_states import ProcessState
import pytest

from aiida.cmdline.commands import cmd_devel
from aiida.engine import submit
from aiida.orm import Int, Node


def test_run_sql(run_cli_command):
    """Test ``verdi devel run-sql``."""
    options = ['SELECT COUNT(*) FROM db_dbnode;']
    result = run_cli_command(cmd_devel.devel_run_sql, options)
    assert str(Node.collection.count()) in result.output, result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_revive_without_daemon(run_cli_command):
    """Test that ``verdi devel revive`` fails if no daemon is running."""
    assert run_cli_command(cmd_devel.devel_revive, raises=True)


@pytest.mark.usefixtures('aiida_profile', 'started_daemon_client')
def test_revive(run_cli_command, monkeypatch, aiida_local_code_factory, submit_and_await):
    """Test ``verdi devel revive``."""
    code = aiida_local_code_factory('core.arithmetic.add', '/bin/bash')
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
    run_cli_command(cmd_devel.devel_revive, [str(node.pk), '--force'])

    # Wait for the process to be picked up by the daemon and completed. If there is a problem with the code, this call
    # should timeout and raise an exception
    submit_and_await(node, ProcessState.FINISHED)
    assert node.is_finished_ok
