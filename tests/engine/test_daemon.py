###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test daemon module."""

import asyncio

import pytest
from plumpy.process_states import ProcessState

from aiida.manage import get_manager
from tests.utils import processes as test_processes


async def reach_waiting_state(process):
    while process.state != ProcessState.WAITING:
        await asyncio.sleep(0.1)


def test_cancel_process_task():
    """This test is designed to replicate how processes are cancelled in the current `shutdown_runner` callback.

    The `CancelledError` should bubble up to the caller, and not be caught and transition the process to excepted.
    """
    runner = get_manager().get_runner()
    # create the process and start it running
    process = runner.instantiate_process(test_processes.WaitProcess)
    task = runner.loop.create_task(process.step_until_terminated())
    # wait for the process to reach a WAITING state
    runner.loop.run_until_complete(asyncio.wait_for(reach_waiting_state(process), 5.0))
    # cancel the task and wait for the cancellation
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        runner.loop.run_until_complete(asyncio.wait_for(task, 5.0))
    # the node should still record a waiting state, not excepted
    assert process.node.process_state == ProcessState.WAITING
