###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for :mod:`aiida.brokers.rabbitmq.communicator` without a broker."""

import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from aiida.brokers.rabbitmq import communicator as rmq_communicator
from aiida.brokers.rabbitmq import utils as rmq_utils


def test_on_rpc_cancelled_sends_cancelled_response():
    """A directly cancelled RPC receiver must still send a cancelled response."""
    subscriber = rmq_communicator.RmqSubscriber.__new__(rmq_communicator.RmqSubscriber)
    subscriber._decode = lambda body: body
    sent: dict[str, object] = {}

    async def fake_send(reply_to, correlation_id, response):
        sent['response'] = response

    message = MagicMock()
    message.body = b'body'
    message.reply_to = 'reply'
    message.correlation_id = 'cid'
    message.ack = AsyncMock()

    @asynccontextmanager
    async def fake_process(ignore_processed=True):
        yield message

    message.process = fake_process

    async def cancelled_receiver(_comm, _msg):
        raise asyncio.CancelledError('stop')

    loop = asyncio.new_event_loop()
    try:
        with patch.object(subscriber, '_send_response', fake_send):
            loop.run_until_complete(subscriber._on_rpc(cancelled_receiver, message))
    finally:
        loop.close()

    assert rmq_utils.CANCELLED_KEY in sent['response']
