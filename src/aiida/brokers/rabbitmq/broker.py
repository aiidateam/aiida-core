"""Implementation of the message broker interface using RabbitMQ through ``kiwipy``."""

from __future__ import annotations

import functools
import sys
import typing as t
from collections.abc import Iterator

from aiida.brokers.broker import Broker, BrokerConfigField
from aiida.brokers.rabbitmq import defaults
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration import get_config_option

from .utils import get_launch_queue_name, get_message_exchange_name, get_task_exchange_name

if t.TYPE_CHECKING:
    from kiwipy.rmq import RmqThreadCommunicator
    from packaging.version import Version

    from aiida.manage.configuration.profile import Profile

LOGGER = AIIDA_LOGGER.getChild('broker.rabbitmq')

__all__ = ('RabbitmqBroker',)


class RabbitmqBroker(Broker):
    """Implementation of the message broker interface using RabbitMQ through ``kiwipy``."""

    _config_fields = (
        BrokerConfigField(
            name='broker_protocol',
            prompt='Broker protocol',
            help='Protocol to use for the message broker.',
            default=defaults.BROKER_DEFAULTS.protocol,
            param_type='choice',
            choices=('amqp', 'amqps'),
        ),
        BrokerConfigField(
            name='broker_username',
            prompt='Broker username',
            help='Username to use for authentication with the message broker.',
            default=defaults.BROKER_DEFAULTS.username,
            param_type='non_empty_string',
        ),
        BrokerConfigField(
            name='broker_password',
            prompt='Broker password',
            help='Password to use for authentication with the message broker.',
            default=defaults.BROKER_DEFAULTS.password,
            param_type='non_empty_string',
            hide_input=True,
        ),
        BrokerConfigField(
            name='broker_host',
            prompt='Broker host',
            help='Hostname for the message broker.',
            default=defaults.BROKER_DEFAULTS.host,
            param_type='hostname',
        ),
        BrokerConfigField(
            name='broker_port',
            prompt='Broker port',
            help='Port for the message broker.',
            default=defaults.BROKER_DEFAULTS.port,
            param_type='int',
        ),
        BrokerConfigField(
            name='broker_virtual_host',
            prompt='Broker virtual host',
            help='Name of the virtual host for the message broker without leading forward slash.',
            default=defaults.BROKER_DEFAULTS.virtual_host,
            param_type='string',
        ),
    )

    @classmethod
    def get_detected_config(cls, get_value: t.Callable[[str], t.Any]) -> dict[str, t.Any]:
        """Return detected RabbitMQ configuration values for CLI defaults."""
        connection_params = {field.name.removeprefix('broker_'): get_value(field.name) for field in cls._config_fields}
        return defaults.detect_rabbitmq_config(**connection_params)

    def __init__(self, profile: Profile) -> None:
        """Construct a new instance.

        :param profile: The profile.
        """
        self._profile = profile
        self._communicator: 'RmqThreadCommunicator' | None = None
        self._prefix = f'aiida-{self._profile.uuid}'

    def __str__(self) -> str:
        url = self.get_url(safe=True)

        try:
            return f'RabbitMQ v{self.get_rabbitmq_version()} @ {url}'
        except ConnectionError:
            return f'RabbitMQ @ {url} <Connection failed>'

    def close(self) -> None:
        """Close the broker."""
        if self._communicator is not None:
            self._communicator.close()
            self._communicator = None

    def __del__(self) -> None:
        if self._communicator is not None:
            LOGGER.warning(f'RabbitmqBroker {self!r} was not closed explicitly.')
            if not sys.is_finalizing():
                self.close()

    def iterate_tasks(self) -> Iterator[t.Any]:
        """Return an iterator over the tasks in the launch queue."""
        for task in self.get_communicator().task_queue(get_launch_queue_name(self._prefix)):
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

        self._communicator = RmqThreadCommunicator.connect(
            connection_params={'url': self.get_url()},
            message_exchange=get_message_exchange_name(self._prefix),
            encoder=functools.partial(serialize.serialize, encoding='utf-8'),
            decoder=serialize.deserialize_unsafe,
            task_exchange=get_task_exchange_name(self._prefix),
            task_queue=get_launch_queue_name(self._prefix),
            task_prefetch_count=get_config_option('daemon.worker_process_slots'),
            async_task_timeout=get_config_option('broker.task_timeout'),
            # This is needed because the verdi commands will call this function and when called in unit tests the
            # testing_mode cannot be set.
            testing_mode=self._profile.is_test_profile,
        )

        return self._communicator

    def check_rabbitmq_version(self) -> tuple[Version, bool]:
        """Check the version of RabbitMQ that is being connected to and emit warning if it is not compatible."""
        show_warning = get_config_option('warnings.rabbitmq_version')
        version = self.get_rabbitmq_version()

        if show_warning and not self.is_rabbitmq_version_supported():
            LOGGER.warning(f'RabbitMQ v{version} is not supported and will cause unexpected problems!')
            LOGGER.warning('It can cause long-running workflows to crash and jobs to be submitted multiple times.')
            LOGGER.warning('See https://github.com/aiidateam/aiida-core/wiki/RabbitMQ-version-to-use for details.')
            return version, False

        return version, True

    def get_url(self, safe: bool = False) -> str:
        """Return the RMQ url for this profile.

        :param safe: If ``True``, redact embedded credentials in the returned URL.
        """
        from urllib.parse import urlsplit, urlunsplit

        from .utils import get_rmq_url

        kwargs = {
            key[7:]: val for key, val in self._profile.process_control_config.items() if key.startswith('broker_')
        }
        additional_kwargs = kwargs.pop('parameters', {})
        url = get_rmq_url(**kwargs, **additional_kwargs)

        if not safe:
            return url

        parsed = urlsplit(url)

        if parsed.hostname is None:
            return url

        netloc = parsed.hostname

        if parsed.username is not None:
            netloc = f'{parsed.username}:***@{netloc}'

        if parsed.port is not None:
            netloc = f'{netloc}:{parsed.port}'

        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))

    def is_rabbitmq_version_supported(self) -> bool:
        """Return whether the version of RabbitMQ configured for the current profile is supported.

        Versions 3.5 and below are not supported at all, whereas versions 3.8.15 and above are not compatible with a
        default configuration of the RabbitMQ server.

        :return: boolean whether the current RabbitMQ version is supported.
        """
        from packaging.version import parse

        return parse('3.6.0') <= self.get_rabbitmq_version() < parse('3.8.15')

    def get_rabbitmq_version(self) -> Version:
        """Return the version of the RabbitMQ server that the current profile connects to.

        :return: :class:`packaging.version.Version`
        """
        from packaging.version import parse

        return parse(self.get_communicator().server_properties['version'])
