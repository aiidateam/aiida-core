"""."""
import abc

from aiida.manage.configuration.profile import Profile

__all__ = ('Broker',)


class Broker:
    """."""

    def __init__(self, profile: Profile) -> None:
        """."""
        self._profile = profile

    @abc.abstractmethod
    def get_communicator(self):
        """Return an instance of :class:`kiwipy.Communicator`."""

    @abc.abstractmethod
    def iterate_tasks(self):
        """Return an iterator over the tasks in the launch queue."""

    @abc.abstractmethod
    def close(self):
        """Close the broker."""
