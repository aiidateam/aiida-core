"""Implementation of the message broker interface using RabbitMQ through ``kiwipy``."""

from __future__ import annotations

import asyncio
import functools
import typing as t

from plumpy import ProcessController
from plumpy.rmq import RemoteProcessThreadController

from aiida.brokers.broker import Broker
from aiida.brokers.rabbitmq.coordinator import RmqLoopCoordinator
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration import get_config_option

from .utils import get_launch_queue_name, get_message_exchange_name, get_task_exchange_name

if t.TYPE_CHECKING:
    from kiwipy.rmq import RmqThreadCommunicator

    from aiida.manage.configuration.profile import Profile

LOGGER = AIIDA_LOGGER.getChild('broker.rabbitmq')

__all__ = ('RabbitmqBroker',)


class RabbitmqBroker(Broker):
    """Implementation of the message broker interface using RabbitMQ through ``kiwipy``."""

    def __init__(self, profile: Profile, loop=None) -> None:
        """Construct a new instance.

        :param profile: The profile.
        """
        self._profile = profile
        self._communicator: 'RmqThreadCommunicator | None' = None
        self._prefix = f'aiida-{self._profile.uuid}'
        self._coordinator = None
        self._loop = loop or asyncio.get_event_loop()

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
        """Return an iterator over the tasks in the launch queue."""
        for task in self.get_coordinator().communicator.task_queue(get_launch_queue_name(self._prefix)):
            yield task

    def get_coordinator(self):
        if self._coordinator is not None:
            return self._coordinator

        return self.create_coordinator()

    def create_coordinator(self):
        if self._communicator is None:
            self._communicator = self._create_communicator()
            # Check whether a compatible version of RabbitMQ is being used.
            self.check_rabbitmq_version()

        coordinator = RmqLoopCoordinator(self._communicator, self._loop)

        return coordinator

    def get_controller(self) -> ProcessController:
        coordinator = self.get_coordinator()
        return RemoteProcessThreadController(coordinator)

    def _create_communicator(self) -> 'RmqThreadCommunicator':
        """Return an instance of :class:`kiwipy.Communicator`."""
        from kiwipy.rmq import RmqThreadCommunicator

        from aiida.orm.utils import serialize

        _communicator = RmqThreadCommunicator.connect(
            connection_params={'url': self.get_url()},
            message_exchange=get_message_exchange_name(self._prefix),
            encoder=functools.partial(serialize.serialize, encoding='utf-8'),
            decoder=serialize.deserialize_unsafe,
            task_exchange=get_task_exchange_name(self._prefix),
            task_queue=get_launch_queue_name(self._prefix),
            task_prefetch_count=get_config_option('daemon.worker_process_slots'),
            async_task_timeout=get_config_option('rmq.task_timeout'),
            # This is needed because the verdi commands will call this function and when called in unit tests the
            # testing_mode cannot be set.
            testing_mode=self._profile.is_test_profile,
        )

        return _communicator

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

        return parse(self.get_coordinator().communicator.server_properties['version'])
