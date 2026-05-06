"""Interface for a message broker that facilitates communication with and between process runners."""

from __future__ import annotations

import abc
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

    def revive_process(self, pid: int) -> None:
        """Re-enqueue a continuation task for an active process that has no task in the broker.

        Used by ``verdi process repair`` to recover zombie processes (active in the database but
        without a corresponding task on the broker). The required state depends on the
        implementation: a broker whose lifecycle is managed by the daemon needs the daemon
        stopped, while a broker that runs as an independent service only needs to be reachable.

        Implementations are optional. The default raises :class:`NotImplementedError` so that
        third-party brokers remain instantiable; they can opt in by overriding this method.

        :param pid: The pk of the process to revive.
        :raises NotImplementedError: If the broker does not support process revival.
        """
        msg = f'`{type(self).__name__}` does not implement `revive_process` (cannot revive process `{pid}`)'
        raise NotImplementedError(msg)

    @abc.abstractmethod
    def close(self) -> None:
        """Close the broker."""
