import aiida.orm
import kiwipy
import plumpy
import tornado.gen


__all__ = ['Future', 'CalculationFuture']

Future = plumpy.Future


class CalculationFuture(Future):
    """
    A future that waits for a calculation to complete using both polling and
    listening for broadcast events if possible
    """
    _filtered = None

    def __init__(self, pk, loop=None, poll_interval=None, communicator=None):
        """
        Get a future for a calculation node being finished.  If a None poll_interval is
        supplied polling will not be used.  If a communicator is supplied it will be used
        to listen for broadcast messages.

        :param pk: The calculation pk
        :param loop: An event loop
        :param poll_interval: The polling interval.  Can be None in which case no polling.
        :param communicator: A communicator.   Can be None in which case no broadcast listens.
        """
        from .processes import ProcessState

        super(CalculationFuture, self).__init__()
        assert not (poll_interval is None and communicator is None), \
            "Must poll or have a communicator to use"

        calc_node = aiida.orm.load_node(pk=pk)
        if calc_node.is_terminated:
            self.set_result(calc_node)
        else:
            self._communicator = communicator
            self.add_done_callback(lambda _: self.cleanup())

            # Try setting up a filtered broadcast subscriber
            if self._communicator is not None:
                self._filtered = kiwipy.BroadcastFilter(
                    lambda *args, **kwargs: self.set_result(calc_node), sender=pk)
                for state in [ProcessState.FINISHED,
                              ProcessState.KILLED,
                              ProcessState.EXCEPTED]:
                    self._filtered.add_subject_filter("state_changed.*.{}".format(state.value))
                self._communicator.add_broadcast_subscriber(self._filtered)

            # Start polling
            if poll_interval is not None:
                loop.add_callback(self._poll_calculation, calc_node, poll_interval)

    def cleanup(self):
        if self._communicator is not None:
            self._communicator.remove_broadcast_subscriber(self._filtered)
            self._filtered = None
            self._communicator = None

    @tornado.gen.coroutine
    def _poll_calculation(self, calc_node, poll_interval):
        while not self.done() and not calc_node.is_terminated:
            yield tornado.gen.sleep(poll_interval)

        if not self.done():
            self.set_result(calc_node)
