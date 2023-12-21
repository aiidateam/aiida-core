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


@pytest.mark.requires_rmq
@pytest.mark.asyncio
async def test_shutdown_worker(manager):
    """Test the ``shutdown_worker`` method."""
    runner = manager.get_runner()
    await shutdown_worker(runner)

    try:
        assert runner.is_closed()
    finally:
        # Reset the runner of the manager, because once closed it cannot be reused by other tests.
        manager._runner = None
