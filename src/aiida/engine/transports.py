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
from datetime import datetime
from typing import TYPE_CHECKING, Awaitable, Dict, Hashable, Iterator, Optional

from aiida.common import timezone
from aiida.orm import AuthInfo

if TYPE_CHECKING:
    from aiida.transports import Transport

_LOGGER = logging.getLogger(__name__)

# Open and append to the log file at different points

# Open and append to the log file, prepending the current time
## def log_to_file(message):
# datetime.now()
# current_time = datetime.now().strftime("%H:%M:%S")
# with open("/home/geiger_j/aiida_projects/aiida-dev/ssh-alive-testing/transport-log.txt", "a") as f:
#     f.write(f"{current_time}: {message} (transports.py)\n")


class TransportRequest:
    """Information kept about request for a transport object"""

    def __init__(self):
        super().__init__()
        self.future: asyncio.Future = asyncio.Future()
        self.count = 0
        self.transport_closer = None


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
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._transport_requests: Dict[Hashable, TransportRequest] = {}
        self._last_open_time = None
        # self._last_submission_time = None
        self._last_close_time = None
        # self._last_transport_request: Dict[Hashable, str] = {}
        # self._was_last_request_special: bool = False

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
        close_callback_handle = None
        transport_request = self._transport_requests.get(authinfo.pk, None)
        # ## log_to_file(f'EventLoop: {asyncio.all_tasks(self.loop)}')

        # ## log_to_file(f'transport_request: {transport_request}')

        if transport_request is None:
            # There is no existing request for this transport (i.e. on this authinfo)
            transport_request = TransportRequest()
            self._transport_requests[authinfo.pk] = transport_request

            transport = authinfo.get_transport()
            # safe_open_interval = transport.get_safe_open_interval()
            safe_open_interval = 15

            # Check here if last_open_time > safe_interval, one could immediately open the transport
            # This should be the very first request, after a while
            ## log_to_file(f'OPEN_CALLBACK_HANDLE BEFORE DO_OPEN: {open_callback_handle}')
            def do_open():
                """Actually open the transport"""
                if transport_request.count > 0:
                    # The user still wants the transport so open it
                    _LOGGER.debug('Transport request opening transport for %s', authinfo)
                    try:
                        transport.open()
                        self._last_open_time = datetime.now()
                        ## log_to_file(f'LAST_OPEN_TIME: {self._last_open_time}')
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

            # Pseudocode
            # get_metadata from authinfo
            # see if there is a last_close, if not None, compute seconds from then to now
            # if < safe_interval, wait for difference
            # if larger, call call_later, open call_later but with 0
            metadata = authinfo.get_metadata()
            last_close_time = metadata.get('last_close_time')

            log_file_path = '/home/geiger_j/aiida_projects/thor-dev/transport-log.txt'

            debug_info = '\nDEBUG START\n'

            # if last_close_time is None:
            #     # Submit immediately -> This is not ever being triggered
            #     open_callback_handle = self._loop.call_later(1, do_open, context=contextvars.Context())

            #     debug_info += (
            #         f"LAST_CLOSE_TIME_NONE: submit immediately\n"
            #         f"LAST_CLOSE_TIME: {last_close_time}\n"
            #         f"LAST_REQUEST_SPECIAL: {self._was_last_request_special}\n"
            #     )

            last_close_time = datetime.strptime(last_close_time, '%Y-%m-%dT%H:%M:%S.%f%z')
            timedelta_seconds = (timezone.localtime(timezone.now()) - last_close_time).total_seconds()

            if timedelta_seconds > safe_open_interval:
                debug_info += (
                    f'TIMEDELTA > SAFE_OPEN_INTERVAL: submit immediately\n' f'LAST_CLOSE_TIME: {last_close_time}\n'
                    # f"LAST_REQUEST_SPECIAL: {self._was_last_request_special}\n"
                )

                open_callback_handle = self._loop.call_later(0, do_open, context=contextvars.Context())
                # self._was_last_request_special = True

            else:
                # If the last one was a special request, wait the safe_open_interval
                debug_info += (
                    f'TIMEDELTA < SAFE_OPEN_INTERVAL and last request special: submit after safe_open_interval\n'
                    f'LAST_CLOSE_TIME: {last_close_time}\n'
                    # f"LAST_REQUEST_SPECIAL: {self._was_last_request_special}\n"
                )

                open_callback_handle = self._loop.call_later(safe_open_interval, do_open, context=contextvars.Context())

                # if self._was_last_request_special:

                #     # If the last one was a special request, wait the safe_open_interval
                #     debug_info += (
                #         f"TIMEDELTA < SAFE_OPEN_INTERVAL and last request special: submit after safe_open_interval\n"
                #         f"LAST_CLOSE_TIME: {last_close_time}\n"
                #         f"LAST_REQUEST_SPECIAL: {self._was_last_request_special}\n"
                #     )

                #     open_callback_handle = self._loop.call_later(safe_open_interval, do_open, context=contextvars.Context())
                #     self._was_last_request_special = False

                # else:

                #     # This is also a special request
                #     # Or, should it be? Could also remove the if/else, and just wait the safe_open_interval, as is the default
                #     debug_info += (
                #         f"TIMEDELTA < SAFE_OPEN_INTERVAL and last request not special: submit after timedelta\n"
                #         f"LAST_CLOSE_TIME: {last_close_time}\n"
                #         f"LAST_REQUEST_SPECIAL: {self._was_last_request_special}\n"
                #         f"TIMEDELTA: {timedelta_seconds}\n"
                #     )

                #     open_callback_handle = self._loop.call_later(timedelta_seconds, do_open, context=contextvars.Context())
                #     self._was_last_request_special = True
                # open_callback_handle = self._loop.call_later(5, do_open, context=contextvars.Context())

            # open_callback_handle = self._loop.call_later(safe_open_interval, do_open, context=contextvars.Context())

            with open(log_file_path, 'a') as log_file:
                log_file.write(debug_info)

        try:
            transport_request.count += 1
            self._last_submission_time = datetime.now()
            ## log_to_file(f'LAST_SUBMISSION_TIME: {self._last_submission_time}')
            ## log_to_file(f'TRANSPORT_REQUEST_COUNT: {transport_request.count}')
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
            ## log_to_file(f'FINALLY BLOCK - TRANSPORT_REQUEST.COUNT: {transport_request.count}')
            transport_request.count -= 1
            assert transport_request.count >= 0, 'Transport request count dropped below 0!'
            # Check if there are no longer any users that want the transport
            if transport_request.count == 0:
                ## log_to_file(f'TRANSPORT_REQUEST.FUTURE.DONE(): {transport_request.future.done()}')
                if transport_request.future.done():
                    ## log_to_file(f'DATETIME: {(datetime.now() - self._last_open_time).total_seconds() > 5}')

                    if (datetime.now() - self._last_open_time).total_seconds() > 5:

                        def close_transport():
                            transport_request.future.result().close()
                            """Close the transport if conditions are met."""
                            ## log_to_file("CLOSE_TRANSPORT")
                            ## log_to_file(f"LAST_CLOSE_TIME: {self._last_close_time}")

                        close_callback_handle = self._loop.call_later(5, close_transport, context=contextvars.Context())
                        transport_request.transport_closer = close_callback_handle
                        # transport_request.transport_closer = None
                        # else:
                        # If not yet time to close, schedule again
                        # close_callback_handle = self._loop.call_later(
                        #     5, close_transport, context=contextvars.Context())
                        # transport_request.transport_closer = close_callback_handle

                    # ## log_to_file(f"TRANSPORT_REQUEST.TRANSPORT_CLOSER: {transport_request.transport_closer}")
                    # if transport_request.transport_closer is None:
                    #     ## log_to_file("INSIDE")
                    #     self._last_close_time = datetime.now()
                    # else:
                    #     return

                    # This should be replaced with the call_later close_callback_handle invocation
                    # ## log_to_file(f"TRANSPORT_REQUEST.TRANSPORT_CLOSER: {transport_request.transport_closer}")

                    transport_request.future.result().close()

                    # Get old metadata from authinfo, and set variable last_close_time to datetime now in isoformat
                    # Need to convert to str, otherwise not json-serializable when setting authinfo metadata
                    # if self._was_last_request_special is True:
                    last_close_time = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M:%S.%f%z')
                    authinfo.set_metadata({'last_close_time': last_close_time})
                    # else:
                    #     # asyncio.sleep(5)
                    #     transport_request.count += 1
                    #     self._was_last_request_special = True
                    #     yield transport_request.future

                elif open_callback_handle is not None:
                    open_callback_handle.cancel()

                self._transport_requests.pop(authinfo.pk, None)


# Should wait first time 0, then always ~30
# Try out with manual waiting times in between
