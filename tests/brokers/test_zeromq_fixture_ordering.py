###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression tests for ZeroMQ broker service startup ordering with async tests.

Collaborators: ``tests.conftest.manager``/``event_loop`` fixtures and
``aiida.tools.pytest_fixtures.broker.run_aiida_broker_service``.
"""

import pytest

from aiida.manage import get_manager


@pytest.mark.asyncio
async def test_async_first_test_starts_broker_service(manager):
    """Async tests running first in a session must still have a running broker service.

    Regression test: session autouse ``run_aiida_broker_service`` was not reliably ordered before the
    function-scoped ``event_loop`` fixture for async tests that run first in a session. The broker service
    then never started and ``get_communicator`` timed out after 10s with ``Broker did not become ready``.
    The ``manager`` fixture now explicitly depends on the broker service fixture to enforce ordering.
    Run this test alone (no prior sync test in the session) to reproduce.
    """
    from aiida.brokers.zeromq.broker import ZeromqBroker

    broker = get_manager().get_broker()

    if not isinstance(broker, ZeromqBroker):
        pytest.skip('Requires a profile with a ZeroMQ broker.')

    assert broker.check_service_reachable()
    assert get_manager().get_communicator() is not None
