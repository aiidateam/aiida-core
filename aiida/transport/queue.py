from collections import namedtuple
import threading
from concurrent.futures import ThreadPoolExecutor


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
        self._executor = ThreadPoolExecutor(max_workers=4)

    def call_me_with_transport(self, authinfo, callback):
        with self._entries_lock:
            authinfo_entry = self._entries.get(authinfo.id)
            if authinfo_entry is None:
                authinfo_entry = self._create_entry(authinfo)

                # Check if the transport is happy to be opened with any frequency
                if authinfo_entry.transport.get_safe_open_interval() == 0.:
                    authinfo_entry.callbacks.append(callback)
                    self._executor.submit(self._do_callback, authinfo_entry)
                    return

                self._entries[authinfo.id] = authinfo_entry
            authinfo_entry.callbacks.append(callback)

        if self._timer is None:
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
                    self._timer.cancel()

    def get_num_waiting(self):
        total = 0
        for entry in self._entries.itervalues():
            total += len(entry.callbacks)
        return total

    def _do_callbacks(self):
        with self._entries_lock:
            for entry in self._entries.itervalues():
                self._do_callback(entry)

            self._entries.clear()
            self._timer = None

    def _create_entry(self, authinfo):
        return self.AuthinfoEntry(authinfo, authinfo.get_transport(), [])

    def _do_callback(self, entry):
        with entry.transport:
            for fn in entry.callbacks:
                fn(entry.authinfo, entry.transport)
