###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A transport queue to batch process multiple tasks that require a Transport."""

import asyncio
import contextlib
import contextvars
import logging
import traceback
from typing import TYPE_CHECKING, Awaitable, Dict, Hashable, Iterator, Optional

from aiida.orm import AuthInfo

if TYPE_CHECKING:
    from aiida.transports import Transport

_LOGGER = logging.getLogger(__name__)


class TransportRequest:
    """Information kept about request for a transport object"""

    def __init__(self):
        super().__init__()
        self.future: asyncio.Future = asyncio.Future()
        self.count = 0


class TransportQueue:
    """A queue to get transport objects from authinfo.  This class allows clients
    to register their interest in a transport object which will be provided at
    some point in the future.

    Internally the class will wait for a specific interval at the end of which
    it will open the transport and give it to all the clients that asked for it
    up to that point.  This way opening of transports (a costly operation) can
    be minimised.
    """

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """:param loop: An asyncio event, will use `asyncio.get_event_loop()` if not supplied"""

        if loop is not None:
            self._loop = loop
        else:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
        self._transport_requests: Dict[Hashable, TransportRequest] = {}

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get the loop being used by this transport queue"""
        return self._loop

    @contextlib.contextmanager
    def request_transport(self, authinfo: AuthInfo) -> Iterator[Awaitable['Transport']]:
        """Request a transport from an authinfo.  Because the client is not allowed to
        request a transport immediately they will instead be given back a future
        that can be awaited to get the transport::

            async def transport_task(transport_queue, authinfo):
                with transport_queue.request_transport(authinfo) as request:
                    transport = await request
                    # Do some work with the transport

        :param authinfo: The authinfo to be used to get transport
        :return: A future that can be yielded to give the transport
        """
        open_callback_handle = None
        transport_request = self._transport_requests.get(authinfo.pk, None)

        if transport_request is None:
            # There is no existing request for this transport (i.e. on this authinfo)
            transport_request = TransportRequest()
            self._transport_requests[authinfo.pk] = transport_request

            transport = authinfo.get_transport()
            safe_open_interval = transport.get_safe_open_interval()

            def do_open():
                """Actually open the transport"""
                if transport_request.count > 0:
                    # The user still wants the transport so open it
                    _LOGGER.debug('Transport request opening transport for %s', authinfo)
                    try:
                        transport.open()
                    except Exception as exception:
                        _LOGGER.error('exception occurred while trying to open transport:\n %s', exception)
                        transport_request.future.set_exception(exception)

                        # Cleanup of the stale TransportRequest with the excepted transport future
                        self._transport_requests.pop(authinfo.pk, None)
                    else:
                        transport_request.future.set_result(transport)

            # Save the handle so that we can cancel the callback if the user no longer wants it
            # Note: Don't pass the Process context, since (a) it is not needed by `do_open` and (b) the transport is
            # passed around to many places, including outside aiida-core (e.g. paramiko). Anyone keeping a reference
            # to this handle would otherwise keep the Process context (and thus the process itself) in memory.
            # See https://github.com/aiidateam/aiida-core/issues/4698
            open_callback_handle = self._loop.call_later(safe_open_interval, do_open, context=contextvars.Context())

        try:
            transport_request.count += 1
            yield transport_request.future
        except asyncio.CancelledError:
            # note this is only required in python<=3.7,
            # where asyncio.CancelledError inherits from Exception
            _LOGGER.debug('Transport task cancelled')
            raise
        except Exception:
            _LOGGER.error('Exception whilst using transport:\n%s', traceback.format_exc())
            raise
        finally:
            transport_request.count -= 1
            assert transport_request.count >= 0, 'Transport request count dropped below 0!'
            # Check if there are no longer any users that want the transport
            if transport_request.count == 0:
                # IMPORTANT: Pop from _transport_requests BEFORE closing the transport.
                # This prevents a race condition with async transports where:
                # 1. close() is called, which for AsyncTransport uses run_until_complete(close_async)
                # 2. With nest_asyncio (used by plumpy), this call yields back to the event loop
                # 3. The event loop schedules close_async, then continues running another tasks
                #   - for example one that requests the transport which is scheduled to be closed
                # 4. The task now using the transport to do some operation awaits,
                #   next the close_async task closes the transport while still in use -> error
                # By poping first, new tasks will create a fresh transport request.
                self._transport_requests.pop(authinfo.pk, None)

                if transport_request.future.done():
                    _LOGGER.debug('Transport request closing transport for %s', authinfo)
                    transport_request.future.result().close()
                elif open_callback_handle is not None:
                    open_callback_handle.cancel()
