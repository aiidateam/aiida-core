"""Interface for a message broker that facilitates communication with and between process runners."""

import abc
import enum
import typing as t

if t.TYPE_CHECKING:
    from aiida.manage.configuration.profile import Profile

__all__ = ('Broker', 'QueueType', 'TaskQueue')


@t.runtime_checkable
class TaskQueue(t.Protocol):
    """Protocol for task queues that can send tasks and manage subscribers.

    TODO: Remove this once kiwipy exposes ``kiwipy.TaskQueue`` and the dependency is updated.
    """

    def task_send(self, task: t.Any, no_reply: bool = False, nowait: bool = False) -> t.Any:
        """Send a task to the queue."""
        ...

    def add_task_subscriber(self, subscriber: t.Callable[..., t.Any]) -> t.Any:
        """Add a task subscriber."""
        ...

    def remove_task_subscriber(self, identifier: t.Any) -> None:
        """Remove a task subscriber."""
        ...


class QueueType(enum.Enum):
    """Queue types for task routing."""

    ROOT_WORKCHAIN = 'root-workchain'
    NESTED_WORKCHAIN = 'nested-workchain'
    CALCJOB = 'calcjob'


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

    @abc.abstractmethod
    def get_full_queue_name(self, user_queue: str, queue_type: QueueType) -> str:
        """Get the full queue name for routing.

        :param user_queue: The user-defined queue name (e.g., 'default').
        :param queue_type: The queue type.
        :return: The full queue name for routing.
        """

    @abc.abstractmethod
    def get_queue_types(self) -> 'list[QueueType]':
        """Get the list of queue types.

        :return: List of queue types.
        """

    @abc.abstractmethod
    def get_task_queue(self, queue_type: QueueType, user_queue: str) -> TaskQueue:
        """Get a task queue by type and user queue name.

        :param queue_type: The queue type.
        :param user_queue: The user-defined queue name.
        :return: The task queue instance.
        """
