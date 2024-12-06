###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test process futures."""

import asyncio

import pytest

from aiida.engine import processes, run
from aiida.manage import get_manager
from tests.utils import processes as test_processes


@pytest.mark.requires_rmq
class TestWf:
    """Test process futures."""

    TIMEOUT = 5.0  # seconds

    def test_calculation_future_broadcasts(self):
        """Test calculation future broadcasts."""
        manager = get_manager()
        runner = manager.get_runner()
        process = test_processes.DummyProcess()

        # No polling
        future = processes.futures.ProcessFuture(
            pk=process.pid, loop=runner.loop, communicator=manager.get_communicator()
        )

        run(process)
        calc_node = runner.run_until_complete(asyncio.wait_for(future, self.TIMEOUT))

        assert process.node.pk == calc_node.pk

    def test_calculation_future_polling(self):
        """Test calculation future polling."""
        runner = get_manager().get_runner()
        process = test_processes.DummyProcess()

        # No communicator
        future = processes.futures.ProcessFuture(pk=process.pid, loop=runner.loop, poll_interval=0)

        runner.run(process)
        calc_node = runner.run_until_complete(asyncio.wait_for(future, self.TIMEOUT))

        assert process.node.pk == calc_node.pk
