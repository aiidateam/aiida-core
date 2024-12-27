"""Interface for a message broker that facilitates communication with and between process runners."""

import abc
import typing as t

from plumpy.controller import ProcessController

if t.TYPE_CHECKING:
    from plumpy.coordinator import Coordinator

    from aiida.manage.configuration.profile import Profile

__all__ = ('Broker',)


# FIXME: make me a protocol
class Broker:
    """Interface for a message broker that facilitates communication with and between process runners."""

    # def __init__(self, profile: 'Profile') -> None:
    #     """Construct a new instance.
    #
    #     :param profile: The profile.
    #     """
    #     self._profile = profile

    @abc.abstractmethod
    # FIXME: make me a property
    def get_coordinator(self) -> 'Coordinator':
        """Return an instance of coordinator."""

    @abc.abstractmethod
    def get_controller(self) -> ProcessController:
        """Return the process controller"""
        ...

    @abc.abstractmethod
    def iterate_tasks(self):
        """Return an iterator over the tasks in the launch queue."""

    @abc.abstractmethod
    def close(self):
        """Close the broker."""
