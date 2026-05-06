"""Interface for a message broker that facilitates communication with and between process runners."""

from __future__ import annotations

import abc
import pathlib
import typing as t

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from aiida.manage.configuration.profile import Profile

__all__ = ('Broker',)


class Broker(abc.ABC):
    """Interface for a message broker that facilitates communication with and between process runners."""

    def __init__(self, profile: 'Profile') -> None:
        """Construct a new instance.

        :param profile: The profile.
        """
        self._profile = profile

    @abc.abstractmethod
    def get_communicator(self) -> t.Any:
        """Return an instance of :class:`kiwipy.Communicator`."""

    @abc.abstractmethod
    def iterate_tasks(self) -> Iterator[t.Any]:
        """Return an iterator over the tasks in the launch queue."""

    def get_log_file(self) -> pathlib.Path | None:
        """Return the broker log file path, if available."""
        return None

    @abc.abstractmethod
    def close(self) -> None:
        """Close the broker."""
