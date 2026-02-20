###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the :mod:`aiida.engine.daemon.worker` module."""

import pytest

from aiida.engine.daemon.worker import shutdown_worker
from aiida.orm import Log
from aiida.workflows.arithmetic.multiply_add import MultiplyAddWorkChain


@pytest.mark.requires_rmq
def test_shutdown_worker(manager):
    """Test the ``shutdown_worker`` method."""
    runner = manager.get_runner()
    loop = runner.loop
    loop.run_until_complete(shutdown_worker(runner))

    try:
        assert runner.is_closed()
    finally:
        # Reset the runner of the manager, because once closed it cannot be reused by other tests.
        manager._runner = None
        # ``shutdown_worker`` calls ``runner.close()`` which calls ``loop.stop()`` while the loop
        # is running inside ``run_until_complete``. This leaves a stale ``_run_until_complete_cb``
        # in the loop's callback queue that would prematurely stop the next ``run_until_complete``
        # call. Close the loop so ``get_or_create_event_loop`` creates a fresh one for other tests.
        if not loop.is_closed():
            loop.close()


@pytest.mark.usefixtures('aiida_profile_clean', 'started_daemon_client')
def test_logging_configuration(aiida_code_installed, submit_and_await):
    """Integration test to verify that the daemon has the logging properly configured including the ``DbLogHandler``.

    This is a regression test to make sure that the ``DbLogHandler`` is properly configured for daemon workers, which
    ensures that log messages are written to the log table in the database for the corresponding node.
    """
    code = aiida_code_installed('add')
    node = submit_and_await(MultiplyAddWorkChain, x=1, y=2, z=3, code=code)
    logs = Log.collection.get_logs_for(node)
    assert len(logs) == 1
    assert 'Submitted the `ArithmeticAddCalculation`' in next(log.message for log in logs)
