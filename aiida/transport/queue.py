from collections import namedtuple
import logging
import threading
import traceback

_LOGGER = logging.getLogger(__name__)


class _TransportCaller(threading.Thread):
    def __init__(self, queue):
        super(_TransportCaller, self).__init__()
        self.daemon = True
        self._queue = queue
        self._waiting = threading.Condition(threading.RLock())
        self._state_lock = threading.Lock()
        self._transport_infos = []

    def run(self):
        while True:
            with self._state_lock:
                to_do = self._transport_infos
                self._transport_infos = []

            for entry in to_do:
                self._queue._do_callback(entry)

    def do_call(self, transport_entry):
        with self._state_lock:
            self._transport_infos.append(transport_entry)


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
    DEFAULT_INTERVAL = 30.0
    AuthinfoEntry = namedtuple("AuthinfoEntry", ['authinfo', 'transport', 'callbacks'])

    def __init__(self, interval=DEFAULT_INTERVAL):
        self._entries = {}
        self._interval = interval
        self._timer = None
        self._entries_lock = threading.Lock()
        # A thread pool used for the special case of local transport
        # self._executor = ThreadPoolExecutor(max_workers=4)
        self._transport_caller = _TransportCaller(self)

    def call_me_with_transport(self, authinfo, callback):
        _LOGGER.debug("Got request for transport with callback '{}'".format(callback))

        authinfo_entry = self._entries.get(authinfo.id)
        if authinfo_entry is None:
            authinfo_entry = self._create_entry(authinfo)

        # DISABLED below for now, doesn't work
        # # Check if the transport is happy to be opened with any frequency
        # if authinfo_entry.transport.get_safe_open_interval() == 0.:
        #     authinfo_entry.callbacks.append(callback)
        #     # self._executor.submit(self._do_callback, authinfo_entry)
        #     if not self._transport_caller.is_alive():
        #         self._transport_caller.start()
        #     self._transport_caller.do_call(authinfo_entry)
        # else:
        # Ok, we have to queue it
        with self._entries_lock:
            # The entry may have changed since the beginning of this function so
            # try getting it and if it doesn't exist, use ours from above
            authinfo_entry = self._entries.setdefault(authinfo.id, authinfo_entry)
            authinfo_entry.callbacks.append(callback)

            if self._timer is None:
                _LOGGER.debug("Starting callback timer {}".format(self._interval))
                self._timer = threading.Timer(self._interval, self._do_callbacks)
                self._timer.start()

    def cancel_callback(self, authinfo, callback):
        with self._entries_lock:
            try:
                callbacks = self._entries[authinfo.id].callbacks
                callbacks.remove(callback)
                if len(callbacks) == 0:
                    del self._entries[authinfo.id]
            except (KeyError, ValueError):
                pass
            else:
                if self.get_num_waiting() == 0 and self._timer is not None:
                    _LOGGER.debug("Stopping callback timer")
                    self._timer.cancel()
                    self._timer = None

    def get_num_waiting(self):
        total = 0
        for entry in self._entries.itervalues():
            total += len(entry.callbacks)
        return total

    def _do_callbacks(self):
        with self._entries_lock:
            # Copy over entries and release the lock so others can register
            # for the next round of callbacks
            entries = self._entries
            self._entries = {}
            self._timer = None

        for entry in entries.itervalues():
            self._do_callback(entry)

    def _create_entry(self, authinfo):
        return self.AuthinfoEntry(authinfo, authinfo.get_transport(), [])

    def _do_callback(self, entry):
        with entry.transport:
            for fn in entry.callbacks:
                _LOGGER.debug("Passing transport to {}...".format(fn))

                try:
                    fn(entry.authinfo, entry.transport)
                except BaseException:
                    _LOGGER.error(
                        "Callback '{}' raised exception when passed transport:\n{}".format(
                            fn, traceback.format_exc())
                    )

                _LOGGER.debug("...callback finished")
