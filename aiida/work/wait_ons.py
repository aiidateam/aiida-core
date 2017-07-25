import threading
import logging

from plum.wait import WaitOnEvent, Unsavable, Interrupted
from aiida.common.lang import override
from aiida.transport import get_transport_queue


_LOGGER = logging.getLogger(__name__)


class WaitForTransport(WaitOnEvent, Unsavable):
    """
    Wait for transport.
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
        self._interrupted = False
        self._want_transport = False
        self._waiting = threading.Condition()

    def __str__(self):
        return "transport {} on {}".format(
            self._authinfo.aiidauser.email,
            self._authinfo.dbcomputer.name
        )

    def wait(self, timeout=None):
        with self._waiting:
            self._transport_queue.call_me_with_transport(self._authinfo, self._got_transport)
            self._want_transport = True
            self._interrupted = False
            self._waiting.wait(timeout)
            self._want_transport = False

            if self._transport is not None:
                return True
            else:
                self._transport_queue.cancel_callback(self._authinfo, self._got_transport)
                if self._interrupted:
                    raise Interrupted()
                else:
                    # Timed-out
                    return False

    def interrupt(self):
        with self._waiting:
            self._interrupted = True
            self._waiting.notify_all()

    @property
    def transport(self):
        return self._transport

    def release_transport(self):
        self._transport_lock.set()

    def _got_transport(self, authinfo, transport):
        with self._waiting:
            if not self._want_transport:
                return

            # Hand over the transport
            self._transport = transport
            self._waiting.notify_all()

        _LOGGER.debug("Locking transport...")
        self._transport_lock.wait()
        self._transport = None
        _LOGGER.debug("... released transport")

