"""Interface for a message broker that facilitates communication with and between process runners."""

import abc
import typing as t

if t.TYPE_CHECKING:
    from aiida.manage.configuration.profile import Profile

__all__ = ('Broker',)


class Broker:
    """Interface for a message broker that facilitates communication with and between process runners."""

    def __init__(self, profile: 'Profile') -> None:
        """Construct a new instance.

        :param profile: The profile.
        """
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
