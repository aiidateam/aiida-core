import threading

from plum.wait import WaitOnEvent, Unsavable, Interrupted
from aiida.common.lang import override
from aiida.transport import get_transport_queue


class WaitForTransport(WaitOnEvent, Unsavable):
    """
    Wait for transport.  When the wait on is constructed it will wait to get a
    transport and will be done as soon as it has it.  From this moment on it
    retains the transport until release_transport() is called.  This must be
    called to let others have the transport so don't forget!
    """

    def __init__(self, authinfo, transport_queue=None):
        """
        :param transport_queue: :class:`aiida.transport.queue.TransportQueue`
        """
        super(WaitForTransport, self).__init__()
        self._authinfo = authinfo
        self._transport = None
        # Used to block the transport until the user calls release_transport
        self._transport_lock = threading.Event()
        if transport_queue is None:
            transport_queue = get_transport_queue()
        self._transport_queue = transport_queue
        self._transfer_lock = threading.Lock()
        self._transport_wait = threading.Lock()

    def __str__(self):
        return "transport {} on {}".format(
            self._authinfo.aiidauser.email,
            self._authinfo.dbcomputer.name
        )

    @override
    def wait(self, timeout=None):
        assert self.transport is None, "Forgot to call release_transport() before waiting again"

        interrupted = False
        self.release_transport()
        try:

            with self._transport_wait:
                self._transport_queue.call_me_with_transport(self._authinfo, self._got_transport)
                try:
                    super(WaitForTransport, self).wait(timeout)
                except Interrupted:
                    interrupted = True

        finally:
            with self._transfer_lock:
                if self._transport is not None:
                    return True
                else:
                    self._transport_queue.cancel_callback(self._authinfo, self._got_transport)
                    self.release_transport()
                    if interrupted:
                        raise Interrupted()
                    else:
                        return False

    @property
    def transport(self):
        return self._transport

    def release_transport(self):
        self._transport_lock.set()

    def _got_transport(self, authinfo, transport):
        with self._transfer_lock:
            if self._waiting_for_transport():
                # Hand over the transport
                self._transport = transport
                self._transport_lock.clear()
                self.set()

        # Check if we needed the transport after all
        if self._transport is not None:
            self._transport_lock.wait()
            self._transport = None

    def _waiting_for_transport(self):
        if self._transport_wait.acquire(False):
            # We managed to acquire, so not waiting
            self._transport_wait.release()
            return False
        else:
            return True
