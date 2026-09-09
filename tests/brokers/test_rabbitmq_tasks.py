###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for :mod:`aiida.brokers.rabbitmq.tasks` without a broker."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from aiida.brokers.rabbitmq import tasks as rmq_tasks


def test_task_done_cancelled_requeues():
    """A cancelled outcome must requeue (nack) instead of dropping the message."""
    loop = asyncio.new_event_loop()
    try:
        subscriber = MagicMock()
        subscriber._decode.return_value = ({'task': 'dummy'}, False)
        subscriber.loop.return_value = loop
        message = AsyncMock()
        message.body = b'body'
        incoming = rmq_tasks.RmqIncomingTask(subscriber, message)
        outcome = loop.create_future()
        outcome.cancel()
        assert outcome.done()

        loop.run_until_complete(incoming._task_done(outcome))

        message.ack.assert_not_called()
        message.nack.assert_called_once_with(requeue=True)
        assert incoming.state == rmq_tasks.TASK_REQUEUED
    finally:
        loop.close()
