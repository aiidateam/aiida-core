"""ZMQ Broker - AiiDA Broker wrapper for ZMQ communicator."""

from __future__ import annotations

import typing as t
from pathlib import Path

from aiida.brokers.broker import Broker
from aiida.common.log import AIIDA_LOGGER

from .communicator import ZmqCommunicator
from .controller import ZmqBrokerController
from .queue import PersistentQueue

if t.TYPE_CHECKING:
    from aiida.manage.configuration.profile import Profile

__all__ = ('ZmqBroker',)

LOGGER = AIIDA_LOGGER.getChild('broker.zmq')


class ZmqBroker(Broker):
    """AiiDA Broker implementation using ZeroMQ.

    This broker connects to a ZmqBrokerService to handle messaging.
    The broker service must be started separately.

    Configuration paths (derived from profile):
    - storage_path: {config_dir}/broker/{profile_uuid}/storage/
    - sockets_path: {temp_dir}/ (created by broker service, path stored in broker.sockets file)
    - router_endpoint: ipc://{sockets_path}/router.sock
    - pub_endpoint: ipc://{sockets_path}/pub.sock

    Note: Socket files are stored in a temporary directory to avoid Unix domain
    socket path length limits (~107 bytes).
    """

    # Class attribute for type discovery
    Communicator = ZmqCommunicator

    def __init__(self, profile: 'Profile') -> None:
        """Construct a new ZMQ broker instance.

        :param profile: The AiiDA profile
        """
        super().__init__(profile)

        self._communicator: ZmqCommunicator | None = None

        # Derive paths from profile
        from aiida.manage.configuration import get_config_path

        config_dir = Path(get_config_path()).parent
        broker_dir = config_dir / 'broker' / profile.uuid

        # Storage path is in the AiiDA config directory
        self._storage_path = broker_dir / 'storage'
        self._broker_dir = broker_dir

        # Controller for managing the broker service
        self._controller = ZmqBrokerController(broker_dir)

        LOGGER.debug('ZMQ Broker initialized for profile: %s', profile.name)
        LOGGER.debug('Broker directory: %s', broker_dir)
        LOGGER.debug('Storage path: %s', self._storage_path)

    def __str__(self) -> str:
        """Return string representation with broker status."""
        if self._controller.is_running():
            status = self._controller.get_status()
            pid = status.get('pid', '?') if status else '?'
            return f'ZMQ Broker (PID {pid}) @ {self._broker_dir}'
        return f'ZMQ Broker @ {self._broker_dir} <not running>'

    @property
    def storage_path(self) -> Path:
        """Return the path for task queue storage."""
        return self._storage_path

    @property
    def router_endpoint(self) -> str | None:
        """Return the ROUTER socket endpoint.

        :return: Endpoint string, or None if broker is not running
        """
        return self._controller.router_endpoint

    @property
    def pub_endpoint(self) -> str | None:
        """Return the PUB socket endpoint.

        :return: Endpoint string, or None if broker is not running
        """
        return self._controller.pub_endpoint

    @property
    def controller(self) -> ZmqBrokerController:
        """Return the broker controller for managing the broker service."""
        return self._controller

    def get_communicator(self) -> ZmqCommunicator:
        """Return a ZMQ communicator instance.

        Creates and starts the communicator if not already created.

        :return: The ZMQ communicator
        :raises ConnectionError: If broker service is not running
        """
        if self._communicator is None:
            router_endpoint = self.router_endpoint
            pub_endpoint = self.pub_endpoint

            if router_endpoint is None or pub_endpoint is None:
                raise ConnectionError(f'{self}')

            self._communicator = ZmqCommunicator(
                router_endpoint=router_endpoint,
                pub_endpoint=pub_endpoint,
            )
            self._communicator.start()
            LOGGER.info('ZMQ Communicator started')

        return self._communicator

    def iterate_tasks(self) -> t.Iterator[dict]:
        """Iterate over pending tasks in the queue.

        This provides direct access to the task queue for inspection.

        :yield: Task data dictionaries
        """
        queue_path = self._storage_path / 'tasks'
        if not queue_path.exists():
            return

        queue = PersistentQueue(queue_path)
        for task_id, task_data in queue.get_all_pending():
            yield task_data

    def close(self) -> None:
        """Close the broker and release resources."""
        if self._communicator is not None:
            self._communicator.close()
            self._communicator = None
            LOGGER.info('ZMQ Broker closed')

    def __enter__(self) -> 'ZmqBroker':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


def get_broker_base_path(profile: 'Profile') -> Path:
    """Get the base path for broker data for a profile.

    :param profile: The AiiDA profile
    :return: Base path for broker data
    """
    from aiida.manage.configuration import get_config_path

    config_dir = Path(get_config_path()).parent
    return config_dir / 'broker' / profile.uuid
