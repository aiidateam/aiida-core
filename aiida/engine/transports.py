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
import asyncio
import contextlib
import contextvars
import logging
import traceback
from typing import Awaitable, Dict, Hashable, Iterator, Optional

from aiida.client import ClientProtocol
from aiida.orm import AuthInfo

_LOGGER = logging.getLogger(__name__)


class ClientRequest:
    """ Information kept about request for a transport object """

    def __init__(self):
        super().__init__()
        self.future: asyncio.Future = asyncio.Future()
        self.count = 0


class ClientQueue:
    """
    A queue to get transport objects from authinfo.
    This class allows one to register an interest in a client object,
    which will be provided at some point in the future.

    Internally the class will wait for a specific interval at the end of which
    it will open the client and give it to everyone that asked for it up to that point.
    This way opening of clients (sometimes a costly operation) can be minimised.
    """

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """
        :param loop: An asyncio event, will use `asyncio.get_event_loop()` if not supplied
        """
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._client_requests: Dict[Hashable, ClientRequest] = {}

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """ Get the loop being used by this transport queue """
        return self._loop

    @contextlib.contextmanager
    def request_client(self, authinfo: AuthInfo) -> Iterator[Awaitable[ClientProtocol]]:
        """
        Request a client from an authinfo.
        Because a client is not allowed to be requested immediately,
        they will instead be given back a future that can be awaited to get the transport::

            async def client_task(client_queue, authinfo):
                with client_queue.request_client(authinfo) as request:
                    client = await request
                    # Do some work with the client

        :param authinfo: The authinfo to be used to get client
        :return: A future that can be yielded to give the client
        """
        open_callback_handle = None
        client_request = self._client_requests.get(authinfo.pk, None)

        if client_request is None:
            # There is no existing request for this transport (i.e. on this authinfo)
            client_request = ClientRequest()
            self._client_requests[authinfo.pk] = client_request

            client = authinfo.get_client()
            safe_open_interval = client.get_safe_open_interval()

            def do_open():
                """ Actually open the transport """
                if client_request and client_request.count > 0:
                    # The user still wants the transport so open it
                    _LOGGER.debug('Transport request opening transport for %s', authinfo)
                    try:
                        client.open()
                    except Exception as exception:  # pylint: disable=broad-except
                        _LOGGER.error('exception occurred while trying to open transport:\n %s', exception)
                        client_request.future.set_exception(exception)

                        # Cleanup of the stale ClientRequest with the excepted transport future
                        self._client_requests.pop(authinfo.pk, None)
                    else:
                        client_request.future.set_result(client)

            # Save the handle so that we can cancel the callback if the user no longer wants it
            # Note: Don't pass the Process context, since (a) it is not needed by `do_open` and (b) the transport is
            # passed around to many places, including outside aiida-core (e.g. paramiko). Anyone keeping a reference
            # to this handle would otherwise keep the Process context (and thus the process itself) in memory.
            # See https://github.com/aiidateam/aiida-core/issues/4698
            open_callback_handle = self._loop.call_later(
                safe_open_interval, do_open, context=contextvars.Context()
            )  #  type: ignore[call-arg]

        try:
            client_request.count += 1
            yield client_request.future
        except asyncio.CancelledError:  # pylint: disable=try-except-raise
            # note this is only required in python<=3.7,
            # where asyncio.CancelledError inherits from Exception
            _LOGGER.debug('Transport task cancelled')
            raise
        except Exception:
            _LOGGER.error('Exception whilst using transport:\n%s', traceback.format_exc())
            raise
        finally:
            client_request.count -= 1
            assert client_request.count >= 0, 'Transport request count dropped below 0!'
            # Check if there are no longer any users that want the transport
            if client_request.count == 0:
                if client_request.future.done():
                    _LOGGER.debug('Transport request closing transport for %s', authinfo)
                    client_request.future.result().close()
                elif open_callback_handle is not None:
                    open_callback_handle.cancel()

                self._client_requests.pop(authinfo.pk, None)
