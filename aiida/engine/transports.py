# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A transport queue to batch process multiple tasks that require a Transport."""
import contextlib
import logging
import traceback
from typing import Awaitable, Dict, Hashable, Iterator, Optional
import asyncio

from aiida.orm import AuthInfo
from aiida.transports import Transport

_LOGGER = logging.getLogger(__name__)


class TransportRequest:
    """ Information kept about request for a transport object """

    def __init__(self, authinfo: AuthInfo):
        super().__init__()
        self.future: asyncio.Future = asyncio.Future()
        self.count = 0

        self._callback_handle: Optional[asyncio.TimerHandle] = None
        self._authinfo = authinfo
        self._transport = authinfo.get_transport()

    def do_open(self):
        """ Actually open the transport

        Sets self.future to the open transport, if successful, or to an exception.
        """
        if self.count > 0:

            # The user still wants the transport so open it
            _LOGGER.debug('Transport request opening transport for %s', self._authinfo)
            try:
                self._transport.open()
            except Exception as exception:  # pylint: disable=broad-except
                _LOGGER.error('exception occurred while trying to open transport:\n %s', exception)
                self.future.set_exception(exception)

                # Cleanup of the stale TransportRequest with the excepted transport future
                # self._transport_requests.pop(authinfo.id, None)
            else:
                self.future.set_result(self._transport)

    def open_later(self, loop: asyncio.AbstractEventLoop):
        # Save the handle so that we can cancel the callback if the user no longer wants it
        self._callback_handle = loop.call_later(self._transport.get_safe_open_interval(), self.do_open)

    def cleanup(self):
        """Close transport, cancel callback"""
        if self.future.done():
            _LOGGER.debug('Transport request closing transport for %s', self._authinfo)
            self.future.result().close()

        if self._callback_handle is not None:
            self._callback_handle.cancel()  # has no effect if already cancelled


class TransportQueue:
    """
    A queue to get transport objects from authinfo.  This class allows clients
    to register their interest in a transport object which will be provided at
    some point in the future.

    Internally the class will wait for a specific interval at the end of which
    it will open the transport and give it to all the clients that asked for it
    up to that point.  This way opening of transports (a costly operation) can
    be minimised.
    """

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """
        :param loop: An asyncio event, will use `asyncio.get_event_loop()` if not supplied
        """
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._transport_requests: Dict[Hashable, TransportRequest] = {}
        self._callback_handles: Dict[Hashable, asyncio.TimerHandle] = {}

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """ Get the loop being used by this transport queue """
        return self._loop

    @contextlib.contextmanager
    def request_transport(self, authinfo: AuthInfo) -> Iterator[Awaitable[Transport]]:
        """
        Request a transport from an authinfo. Returns a future that can be awaited to get the transport::

            async def transport_task(transport_queue, authinfo):
                with transport_queue.request_transport(authinfo) as request:
                    transport = await request
                    # Do some work with the transport

        All context managers entered during the safe_open_interval get access to the same transport instance.
        The last context manager to finish takes care of cleaning up.

        :param authinfo: The authinfo to be used to get transport
        :return: A future that can be yielded to give the transport
        """
        transport_request = self._transport_requests.get(authinfo.id, None)

        if transport_request is None:
            # There is no existing request for this transport (i.e. on this authinfo)
            transport_request = TransportRequest(authinfo)
            transport_request.open_later(loop=self._loop)
            self._transport_requests[authinfo.id] = transport_request

        try:
            transport_request.count += 1
            yield transport_request.future
        except Exception:
            _LOGGER.error('Exception whilst using transport:\n%s', traceback.format_exc())
            raise
        finally:
            transport_request.count -= 1
            assert transport_request.count >= 0, 'Transport request count dropped below 0!'
            # Check if there are no longer any users that want the transport
            if transport_request.count == 0:
                transport_request.cleanup()
                self._transport_requests.pop(authinfo.id, None)
