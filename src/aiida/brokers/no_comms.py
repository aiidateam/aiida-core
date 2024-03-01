"""Implementation of the :class:`aiida.brokers.broker.Broker` interface that does not communicate.."""
from aiida.manage.configuration.profile import Profile

from . import Broker

__all__ = ('NoCommsBroker',)


class NoCommsBroker(Broker):
    """Implementation of the :class:`aiida.brokers.broker.Broker` interface that does not communicate.

    This is useful for working without AiiDA without a broker present. Everything will be run locally in the current
    Python interpreter.
    """

    def __init__(self, profile: Profile) -> None:
        """."""
        self._profile = profile

    def __str__(self):
        """."""
        return 'No broker is available for process communication'

    def get_communicator(self):
        """Return ``None`` always because this broker does not have a communicator."""
        return None

    def iterate_tasks(self):
        """Return an iterator over the tasks in the launch queue."""
        raise NotImplementedError('This broker implementation is a dummy and cannot communicate.')

    def close(self):
        """Close the broker.

        This is a no-op as there is no communications channel to close.
        """
