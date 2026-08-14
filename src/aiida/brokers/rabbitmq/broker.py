"""Implementation of the message broker interface using RabbitMQ through ``kiwipy``."""

from __future__ import annotations

import functools
import typing as t
import weakref
from collections.abc import Iterator

from aiida.brokers.broker import Broker, BrokerConfigField, BrokerServiceStatus, JsonValue
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


class _BrokerResources:
    """Resources owned by a :class:`RabbitmqBroker`."""

    def __init__(self) -> None:
        self.communicator: RmqThreadCommunicator | None = None

    def release(self) -> None:
        """Release the resources."""
        if self.communicator is not None:
            self.communicator.close()
            self.communicator = None

    @property
    def has_pending_release(self) -> bool:
        return self.communicator is not None


def _finalize_broker(resources: _BrokerResources, broker_repr: str) -> None:
    """Close resources held by a broker that was not closed explicitly."""
    if resources.has_pending_release:
        LOGGER.warning(f'RabbitmqBroker {broker_repr} was not closed explicitly.')
        resources.release()


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
        self._resources = _BrokerResources()
        self._finalizer = weakref.finalize(self, _finalize_broker, self._resources, repr(self))
        self._prefix = f'aiida-{self._profile.uuid}'

    def __str__(self) -> str:
        url = self.get_url(redact_credentials=True)

        try:
            return f'RabbitMQ v{self.get_rabbitmq_version()} @ {url}'
        except ConnectionError:
            return f'RabbitMQ @ {url} <Connection failed>'

    def probe_service_status(self) -> BrokerServiceStatus:
        """Return status information reported by the RabbitMQ server."""
        had_communicator = self._resources.communicator is not None

        try:
            properties = self.get_communicator().server_properties
            status: BrokerServiceStatus = {'connected': True}
            status.update(
                {
                    key: t.cast(JsonValue, value.decode('utf-8') if isinstance(value, bytes) else value)
                    for key, value in properties.items()
                }
            )
            return status
        except Exception as exception:
            error = f'{type(exception).__name__}: {exception}'
            LOGGER.error('Failed to probe broker status: %s', error)
            return {'connected': False, 'error': error}
        finally:
            if not had_communicator:
                self.close()

    def check_service_reachable(self) -> bool:
        """Return whether the RabbitMQ service is reachable."""
        had_communicator = self._resources.communicator is not None

        try:
            self.get_communicator()
        except Exception:
            return False
        finally:
            if not had_communicator:
                self.close()

        return True

    def close(self) -> None:
        """Close the broker."""
        self._resources.release()

    def iterate_tasks(self) -> Iterator[t.Any]:
        """Return an iterator over the tasks in the launch queue."""
        yield from self.get_communicator().task_queue(get_launch_queue_name(self._prefix))

    def get_communicator(self) -> RmqThreadCommunicator:
        if self._resources.communicator is None:
            self._resources.communicator = self._create_communicator()
            # Check whether a compatible version of RabbitMQ is being used.
            self.check_rabbitmq_version()

        return self._resources.communicator

    def _create_communicator(self) -> RmqThreadCommunicator:
        """Return an instance of :class:`kiwipy.Communicator`."""
        from kiwipy.rmq import RmqThreadCommunicator

        from aiida.orm.utils import serialize

        communicator = RmqThreadCommunicator.connect(
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

        return communicator

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

    def get_url(self, redact_credentials: bool = False) -> str:
        """Return the RMQ url for this profile.

        :param redact_credentials: If ``True``, redact embedded credentials in the returned URL.
        """
        from urllib.parse import urlsplit, urlunsplit

        from .utils import get_rmq_url

        kwargs = {
            key[7:]: val for key, val in self._profile.process_control_config.items() if key.startswith('broker_')
        }
        additional_kwargs = kwargs.pop('parameters', {})
        url = get_rmq_url(**kwargs, **additional_kwargs)

        if not redact_credentials:
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
