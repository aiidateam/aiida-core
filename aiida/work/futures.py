import aiida.orm
import kiwipy
import plum

from .processes import ProcessState

Future = plum.Future


class CalculationFuture(Future):
    _filtered = None

    def __init__(self, pk, loop, poll_interval, communicator=None):
        super(CalculationFuture, self).__init__()

        calc_node = aiida.orm.load_node(pk=pk)
        if calc_node.has_finished():
            self.set_result(calc_node)
        else:
            self._loop = loop
            self._poll_interval = poll_interval
            self._communicator = communicator
            self.add_done_callback(self.cleanup)

            # Try setting up a filtered broadcast subscriber
            if self._communicator is not None:
                self._filtered = kiwipy.BroadcastFilter(
                    lambda **unused_msg: self.set_result(calc_node), sender=pk)
                for state in [ProcessState.FINISHED,
                              ProcessState.CANCELLED,
                              ProcessState.FAILED]:
                    self._filtered.add_subject_filter("state_changed.*.{}".format(state.value))
                self._communicator.add_broadcast_subscriber(self._filtered)

            # Start polling
            # self._loop.call_later(self._poll_interval, self._poll_calculation, calc_node)

    def cleanup(self, unused_future):
        assert unused_future is self

        if self._communicator is not None:
            self._communicator.remove_broadcast_subscriber(self._filtered)
            self._filtered = None
            self._communicator = None
        self._loop = None

    def _poll_calculation(self, calc_node):
        if calc_node.has_finished():
            self.set_result(calc_node)
        else:
            self._loop.call_later(self._poll_interval, self._poll_calculation, calc_node)
