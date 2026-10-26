###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for :mod:`aiida.brokers.rabbitmq.messages` without a broker."""

import asyncio
from unittest.mock import MagicMock

import pytest

from aiida.brokers.rabbitmq.messages import BasePublisherWithReplyQueue


def test_response_decode_failure_completes_future():
    """A malformed response completes its waiting future with the decode error."""

    async def run() -> None:
        publisher = BasePublisherWithReplyQueue.__new__(BasePublisherWithReplyQueue)
        response_future: asyncio.Future[object] = asyncio.Future()
        publisher._awaiting_response = {'correlation-id': response_future}
        publisher._response_decode = MagicMock(side_effect=ValueError('invalid response'))
        message = MagicMock(correlation_id='correlation-id', body=b'invalid')

        await publisher._on_response(message)

        assert 'correlation-id' not in publisher._awaiting_response
        with pytest.raises(ValueError, match='invalid response'):
            response_future.result()

    asyncio.run(run())
