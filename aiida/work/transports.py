# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A transport queue to batch process multiple tasks that require a Transport."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from collections import namedtuple
import contextlib
import logging
import traceback
from tornado import concurrent, gen, ioloop

_LOGGER = logging.getLogger(__name__)


class TransportRequest(object):
    """ Information kept about request for a transport object """

    # pylint: disable=too-few-public-methods,useless-object-inheritance
    def __init__(self):
        super(TransportRequest, self).__init__()
        self.future = concurrent.Future()
        self.count = 0


class TransportQueue(object):  # pylint: disable=useless-object-inheritance
    """
    A queue to get transport objects from authinfo.  This class allows clients
    to register their interest in a transport object which will be provided at
    some point in the future.

    Internally the class will wait for a specific interval at the end of which
    it will open the transport and give it to all the clients that asked for it
    up to that point.  This way opening of transports (a costly operation) can
    be minimised.
    """
    AuthInfoEntry = namedtuple('AuthInfoEntry', ['authinfo', 'transport', 'callbacks', 'callback_handle'])

    def __init__(self, loop=None):
        """
        :param loop: The event loop to use, will use `tornado.ioloop.IOLoop.current()` if not supplied
        :type loop: :class:`tornado.ioloop.IOLoop`
        """
        self._loop = loop if loop is not None else ioloop.IOLoop.current()
        self._transport_requests = {}

    def loop(self):
        """ Get the loop being used by this transport queue """
        return self._loop

    @contextlib.contextmanager
    def request_transport(self, authinfo):
        """
        Request a transport from an authinfo.  Because the client is not allowed to
        request a transport immediately they will instead be given back a future
        that can be yielded to get the transport::

            @tornado.gen.coroutine
            def transport_task(transport_queue, authinfo):
                with transport_queue.request_transport(authinfo) as request:
                    transport = yield request
                    # Do some work with the transport

        :param authinfo: The authinfo to be used to get transport
        :return: A future that can be yielded to give the transport
        """
        open_callback_handle = None
        transport_request = self._transport_requests.get(authinfo.id, None)

        if transport_request is None:
            # There is no existing request for this transport (i.e. on this authinfo)
            transport_request = TransportRequest()
            self._transport_requests[authinfo.id] = transport_request

            transport = authinfo.get_transport()
            safe_open_interval = transport.get_safe_open_interval()

            def do_open():
                """ Actually open the transport """
                if transport_request.count > 0:
                    # The user still wants the transport so open it
                    _LOGGER.debug('Transport request opening transport for %s', authinfo)
                    try:
                        transport.open()
                    except Exception as exception:  # pylint: disable=broad-except
                        _LOGGER.error('exception occurred while trying to open transport:\n %s', exception)
                        transport_request.future.set_exception(exception)

                        # Cleanup of the stale TransportRequest with the excepted transport future
                        self._transport_requests.pop(authinfo.id, None)
                    else:
                        transport_request.future.set_result(transport)

            # Save the handle so that we can cancel the callback if the user no longer wants it
            open_callback_handle = self._loop.call_later(safe_open_interval, do_open)

        try:
            transport_request.count += 1
            yield transport_request.future
        except gen.Return:
            # Have to have this special case so tornado returns are propagated up to the loop
            raise
        except Exception:
            _LOGGER.error("Exception whilst using transport:\n%s", traceback.format_exc())
            raise
        finally:
            transport_request.count -= 1
            assert transport_request.count >= 0, "Transport request count dropped below 0!"
            # Check if there are no longer any users that want the transport
            if transport_request.count == 0:
                if transport_request.future.done():
                    _LOGGER.debug('Transport request closing transport for %s', authinfo)
                    transport_request.future.result().close()
                elif open_callback_handle is not None:
                    self._loop.remove_timeout(open_callback_handle)

                self._transport_requests.pop(authinfo.id, None)
