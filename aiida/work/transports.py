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
from collections import namedtuple
import logging
import threading
import traceback

from aiida.utils import DEFAULT_TRANSPORT_INTERVAL

_LOGGER = logging.getLogger(__name__)


class TransportQueue(object):
    """
    A queue to get transport objects from authinfo.  This class allows clients
    to register their interest in a transport object which will be provided at
    some point in the future using a callback.

    Internally the class will wait for a specific interval at the end of which
    it will open the transport and give it to all the clients that asked for it
    up to that point.  This way opening of transports (a costly operation) can
    be minimised.
    """
    AuthInfoEntry = namedtuple('AuthInfoEntry', ['authinfo', 'transport', 'callbacks', 'callback_handle'])

    def __init__(self, loop=None, interval=DEFAULT_TRANSPORT_INTERVAL):
        """
        :param loop: The io loop
        :param interval: The callback interval in seconds
        """
        self._loop = loop
        self._entries = {}
        self._interval = interval
        self._entries_lock = threading.Lock()
        self._callback_handle = None

    def call_me_with_transport(self, authinfo, callback):
        """
        Add a callback to the queue

        :param authinfo: the AuthInfo that the callback should use for the Transport
        :param callback: the function to be called with Transport
        """
        _LOGGER.debug("Got request for transport with callback '%s'", callback)

        with self._entries_lock:
            self._get_or_create_entry(authinfo).callbacks.append(callback)

    def _get_or_create_entry(self, authinfo):
        """
        Create a callback entry for the given authinfo from which the appropriate Transport will be retrieved

        :param authinfo: the AuthInfo from which the Transport is to be retrieved
        :returns: the constructed AuthInfoEntry
        """
        if authinfo.id in self._entries:
            return self._entries[authinfo.id]

        transport = authinfo.get_transport()

        # Check if the transport is happy to be opened with any frequency
        # I put <= 0 to avoid that if the user, by mistake, puts a negative
        # number, we get errors. Negative errors will be considered as zero.
        safe_open_interval = transport.get_safe_open_interval()
        if safe_open_interval <= 0.:
            callback_handle = self._loop.add_callback(self._do_callback, authinfo.id)
        else:
            # Ok, we have to use a delay
            callback_handle = self._loop.call_later(safe_open_interval, self._do_callback, authinfo.id)

        entry = self.AuthInfoEntry(authinfo, transport, [], callback_handle)
        self._entries[authinfo.id] = entry

        return entry

    def _do_callback(self, authinfo_id):
        """Perform the callback for the given AuthInfoEntry id."""
        entry = self._entries.pop(authinfo_id)
        with entry.transport:
            for callback in entry.callbacks:
                _LOGGER.debug('Passing transport to %s..', callback)
                try:
                    callback(entry.authinfo, entry.transport)
                except BaseException:
                    _LOGGER.error("Callback '%s' raised exception when passed transport:\n%s", callback,
                                  traceback.format_exc())
                _LOGGER.debug('...callback finished')
