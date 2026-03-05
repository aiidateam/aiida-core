"""Implementation of the message broker interface using RabbitMQ through ``kiwipy``."""

from __future__ import annotations

import functools
import typing as t

from aiida.brokers.broker import Broker, QueueType
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration import get_config_option
from .utils import get_message_exchange_name, get_queue_name, get_task_exchange_name

if t.TYPE_CHECKING:
    from kiwipy.rmq import RmqThreadCommunicator, RmqThreadTaskQueue

    from aiida.manage.configuration.profile import Profile

LOGGER = AIIDA_LOGGER.getChild('broker.rabbitmq')

__all__ = ('RabbitmqBroker',)


class RabbitmqBroker(Broker):
    """Implementation of the message broker interface using RabbitMQ through ``kiwipy``."""

    def __init__(self, profile: Profile) -> None:
        """Construct a new instance.

        :param profile: The profile.
        """
        self._profile = profile
        self._communicator: 'RmqThreadCommunicator' | None = None
        self._task_queues: dict[str, 'RmqThreadTaskQueue'] = {}
        self._prefix = f'aiida-{self._profile.uuid}'

    def __str__(self):
        try:
            return f'RabbitMQ v{self.get_rabbitmq_version()} @ {self.get_url()}'
        except ConnectionError:
            return f'RabbitMQ @ {self.get_url()} <Connection failed>'

    def close(self):
        """Close the broker."""
        if self._communicator is not None:
            self._communicator.close()
            self._communicator = None

    def iterate_tasks(self):
        """Return an iterator over the tasks in all cached process queues."""
        for task_queue in self._task_queues.values():
            for task in task_queue:
                yield task

    def get_communicator(self) -> 'RmqThreadCommunicator':
        if self._communicator is None:
            self._communicator = self._create_communicator()
            # Check whether a compatible version of RabbitMQ is being used.
            self.check_rabbitmq_version()

        return self._communicator

    def _create_communicator(self) -> 'RmqThreadCommunicator':
        """Return an instance of :class:`kiwipy.Communicator`."""
        from kiwipy.rmq import RmqThreadCommunicator

        from aiida.orm.utils import serialize

        from .defaults import DEFAULT_USER_QUEUE

        # Use calcjob queue as the default task queue for the communicator
        default_task_queue = get_queue_name(self._prefix, DEFAULT_USER_QUEUE, QueueType.CALCJOB.value)

        self._communicator = RmqThreadCommunicator.connect(
            connection_params={'url': self.get_url()},
            message_exchange=get_message_exchange_name(self._prefix),
            encoder=functools.partial(serialize.serialize, encoding='utf-8'),
            decoder=serialize.deserialize_unsafe,
            task_exchange=get_task_exchange_name(self._prefix),
            task_queue=default_task_queue,
            task_prefetch_count=get_config_option('daemon.worker_process_slots'),
            async_task_timeout=get_config_option('rmq.task_timeout'),
            # This is needed because the verdi commands will call this function and when called in unit tests the
            # testing_mode cannot be set.
            testing_mode=self._profile.is_test_profile,
        )

        return self._communicator

    def check_rabbitmq_version(self):
        """Check the version of RabbitMQ that is being connected to and emit warning if it is not compatible."""
        show_warning = get_config_option('warnings.rabbitmq_version')
        version = self.get_rabbitmq_version()

        if show_warning and not self.is_rabbitmq_version_supported():
            LOGGER.warning(f'RabbitMQ v{version} is not supported and will cause unexpected problems!')
            LOGGER.warning('It can cause long-running workflows to crash and jobs to be submitted multiple times.')
            LOGGER.warning('See https://github.com/aiidateam/aiida-core/wiki/RabbitMQ-version-to-use for details.')
            return version, False

        return version, True

    def get_url(self) -> str:
        """Return the RMQ url for this profile."""
        from .utils import get_rmq_url

        kwargs = {
            key[7:]: val for key, val in self._profile.process_control_config.items() if key.startswith('broker_')
        }
        additional_kwargs = kwargs.pop('parameters', {})
        return get_rmq_url(**kwargs, **additional_kwargs)

    def is_rabbitmq_version_supported(self) -> bool:
        """Return whether the version of RabbitMQ configured for the current profile is supported.

        Versions 3.5 and below are not supported at all, whereas versions 3.8.15 and above are not compatible with a
        default configuration of the RabbitMQ server.

        :return: boolean whether the current RabbitMQ version is supported.
        """
        from packaging.version import parse

        return parse('3.6.0') <= self.get_rabbitmq_version() < parse('3.8.15')

    def get_rabbitmq_version(self):
        """Return the version of the RabbitMQ server that the current profile connects to.

        :return: :class:`packaging.version.Version`
        """
        from packaging.version import parse

        return parse(self.get_communicator().server_properties['version'])

    def get_task_queue(self, queue_type: QueueType, user_queue_name: str) -> 'RmqThreadTaskQueue':
        """Get a task queue by type and user queue name.

        :param queue_type: The queue type.
        :param user_queue_name: The user-defined queue name.
        :return: The task queue instance.
        """
        cache_key = f'{user_queue_name}.{queue_type.value}'
        if cache_key in self._task_queues:
            return self._task_queues[cache_key]

        rmq_queue_name = get_queue_name(self._prefix, user_queue_name, queue_type.value)
        prefetch_count = self._profile.get_prefetch_count(queue_type, user_queue_name)

        task_queue = self.get_communicator().task_queue(rmq_queue_name, prefetch_count=prefetch_count)
        self._task_queues[cache_key] = task_queue
        return task_queue

    def get_full_queue_name(self, user_queue_name: str, queue_type: QueueType) -> str:
        """Get the full RabbitMQ queue name for routing.

        This returns the complete queue name including the profile prefix,
        which is needed when sending tasks to specific queues.

        :param user_queue_name: The user-defined queue name (e.g., 'default').
        :param queue_type: The queue type.
        :return: The full queue name (e.g., 'aiida-{uuid}.default.calcjob.queue').
        """
        return get_queue_name(self._prefix, user_queue_name, queue_type.value)
