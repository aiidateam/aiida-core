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


def test_task_subscriber_cancellation_stops_dispatch():
    """A cancelled subscriber must prevent subsequent subscribers from handling the task."""
    loop = asyncio.new_event_loop()
    try:
        subscriber = rmq_tasks.RmqTaskSubscriber.__new__(rmq_tasks.RmqTaskSubscriber)
        subscriber._decode = lambda body: ({'task': 'dummy'}, False)
        subscriber._loop = loop
        subscriber._subscribers = {}

        message = AsyncMock()
        message.body = b'body'
        handled = False

        async def cancelled_subscriber(_communicator, _task):
            raise asyncio.CancelledError

        async def subsequent_subscriber(_communicator, _task):
            nonlocal handled
            handled = True

        subscriber._subscribers = {'cancelled': cancelled_subscriber, 'subsequent': subsequent_subscriber}

        loop.run_until_complete(subscriber._on_task(message))

        assert not handled
        message.nack.assert_called_once_with(requeue=True)
    finally:
        loop.close()
