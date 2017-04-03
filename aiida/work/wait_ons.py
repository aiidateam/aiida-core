import threading

from aiida.utils import timezone
from plum.wait import WaitOn, Unsavable
from aiida.common.lang import override
from aiida.transport import get_transport_queue
from aiida.work.globals import get_event_emitter


class WaitOnCalc(WaitOn, Unsavable):
    @override
    def __init__(self, pid):
        super(WaitOnCalc, self).__init__()
        event_emitter = get_event_emitter()

        event_emitter.start_listening(
            self._proc_terminated, "calc.{}.stopped".format(pid))
        event_emitter.start_listening(
            self._proc_terminated, "calc.{}.failed".format(pid))

    def _proc_terminated(self, emitter, evt):
        self.done()
        get_event_emitter().stop_listening(self._proc_terminated)


class WaitForTransport(WaitOn, Unsavable):
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

        self._transport_queue.call_me_with_transport(authinfo, self._got_transport)

    def __str__(self):
        return "transport {} on {}".format(
            self._authinfo.aiidauser.email,
            self._authinfo.dbcomputer.name
        )

    @property
    def transport(self):
        return self._transport

    def release_transport(self):
        self._transport = None
        self._transport_lock.set()

    @override
    def interrupt(self):
        self._transport_queue.cancel_callback(self._authinfo, self._got_transport)
        super(WaitForTransport, self).interrupt()

    def _got_transport(self, authinfo, transport):
        self._transport = transport
        self.done()
        self._transport_lock.wait()


class Timepoint(WaitOn):
    """
    Wait for a particular point in time.
    """
    END_TIME = "end_time"

    @classmethod
    def from_now(cls, dt):
        return cls(end_time=timezone.now() + dt)

    def __init__(self, *args, **kwargs):
        super(Timepoint, self).__init__(*args, **kwargs)
        self._timer = None

    @override
    def init(self, end_time):
        """
        Create a timer with an end time

        :param end_time: The time at which the timer expires
        :type end_time: :class:`datetime.datetime`
        """
        super(Timepoint, self).init()
        self._end_time = end_time

        dt = (self._end_time - timezone.now()).total_seconds()
        if dt > 0:
            self._timer = threading.Timer(dt, self.done)
            self._timer.start()
        else:
            self.done()

    @override
    def load_instance_state(self, bundle):
        super(Timepoint, self).load_instance_state(bundle)
        self._end_time = bundle[self.END_TIME]

    @override
    def interrupt(self):
        super(Timepoint, self).interrupt()
        try:
            self._timer.cancel()
        except AttributeError:
            pass
