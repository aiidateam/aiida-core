import threading

from plum.wait import WaitOnEvent, Unsavable
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
        self._transport_lock = threading.Event()
        if transport_queue is None:
            transport_queue = get_transport_queue()
        self._transport_queue = transport_queue

    def __str__(self):
        return "transport {} on {}".format(
            self._authinfo.aiidauser.email,
            self._authinfo.dbcomputer.name
        )

    @override
    def wait(self, timeout=None):
        assert self.transport is None, "Forgot to call release_transport() before waiting again"

        succeeded = False
        try:
            self._transport_lock.clear()
            self._transport_queue.call_me_with_transport(self._authinfo, self._got_transport)
            succeeded = super(WaitForTransport, self).wait(timeout)
        finally:
            if not succeeded:
                self._transport_queue.cancel_callback(self._authinfo, self._got_transport)
                self.release_transport()

    @property
    def transport(self):
        return self._transport

    def release_transport(self):
        self._transport_lock.set()

    def _got_transport(self, authinfo, transport):
        self._transport = transport
        self.set()
        self._transport_lock.wait()
        self._transport = None
