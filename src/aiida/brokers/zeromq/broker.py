"""ZeroMQ Broker - AiiDA Broker wrapper for ZeroMQ communicator."""

from __future__ import annotations

import json
import time
import typing as t
from contextlib import contextmanager
from pathlib import Path

import psutil

from aiida.brokers.broker import Broker, BrokerConfigField, BrokerServiceStatus
from aiida.common.exceptions import ConfigurationError
from aiida.common.log import AIIDA_LOGGER

from .communicator import ZeromqCommunicator
from .defaults import BROKER_READY_TIMEOUT
from .queue import PersistentQueue
from .service import PID_SENTINEL, ZeromqBrokerService

if t.TYPE_CHECKING:
    from aiida.manage.configuration.profile import Profile

__all__ = ('ZeromqBroker',)

LOGGER = AIIDA_LOGGER.getChild('broker.zeromq')


class ZeromqBroker(Broker):
    """AiiDA Broker implementation using ZeroMQ.

    Connects to a ZeromqBrokerService for messaging and reads PID/status/socket
    files written by the service to discover endpoints and query status.
    """

    # Class attribute for type discovery
    Communicator = ZeromqCommunicator

    _config_fields = (
        BrokerConfigField(
            name='supervised_by_daemon',
            prompt='Managed by daemon',
            help='Whether the lifecycle of the broker service is managed by the daemon.',
            default=True,
            param_type='bool',
            # Regular profiles always let the daemon supervise the service, so the setting is not exposed on the CLI and
            # is stored with its default. Running the service outside of the daemon is used by the pytest fixtures,
            # which set this to ``False`` and manage the service lifecycle themselves.
            expose_cli=False,
        ),
    )

    def __init__(self, profile: Profile) -> None:
        super().__init__(profile)

        if profile.process_control_backend != 'core.zeromq':
            msg = (
                'the profile process control backend should be `core.zeromq` for the `ZeromqBroker`, '
                f'got: {profile.process_control_backend}'
            )
            raise ConfigurationError(msg)

        self._communicator: ZeromqCommunicator | None = None

        from aiida.manage.configuration import get_config

        zmq_broker_service_dir = get_config().filepaths(profile)['broker_service']['dir']
        zmq_broker_service_log_path = get_config().filepaths(profile)['broker_service']['log']
        layout = ZeromqBrokerService.FilepathLayout(zmq_broker_service_dir, zmq_broker_service_log_path)
        self._service_dir = layout.service_dir
        self._service_pid_file = layout.pid_file
        self._service_status_file = layout.status_file
        self._service_sockets_file = layout.sockets_file
        self._storage_path = layout.storage_path

    def __str__(self) -> str:
        if self.check_service_reachable():
            status = self.probe_service_status()
            pid = status.get('pid', '?') if status else '?'
            return f'ZeroMQ Broker (PID {pid}) @ {self._service_dir}'
        return f'ZeroMQ Broker @ {self._service_dir} <not running>'

    # --- Status queries (read PID/status/socket files) ---

    def _get_sockets_path(self) -> Path | None:
        if not self._service_sockets_file.exists():
            return None
        try:
            return Path(self._service_sockets_file.read_text().strip())
        except OSError:
            return None

    @property
    def _router_endpoint(self) -> str | None:
        sockets_path = self._get_sockets_path()
        if sockets_path is None:
            return None
        return f'ipc://{sockets_path}/router.sock'

    # protects from global overwrites
    _PID_SENTINEL = PID_SENTINEL

    def _get_service_pid(self) -> int | None:
        """Read the ZeromqBrokerService PID from its PID file.

        The PID file contains ``aiida-zeromq-broker <pid>`` as a sentinel so we
        can validate ownership without fragile command-line string matching.
        """
        if not self._service_pid_file.exists():
            return None
        try:
            content = self._service_pid_file.read_text().strip()
            if content.startswith(self._PID_SENTINEL):
                return int(content.split()[-1])
            # Fallback: bare PID (old format)
            return int(content)
        except (ValueError, OSError):
            return None

    def check_service_reachable(self) -> bool:
        """Check if the ZeromqBrokerService process is running."""
        pid = self._get_service_pid()
        if pid is None:
            return False
        try:
            proc = psutil.Process(pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def probe_service_status(self) -> BrokerServiceStatus:
        """Read the ZeromqBrokerService status from its status file."""
        connected = self.check_service_reachable()

        if not self._service_status_file.exists():
            error = f'Status file `{self._service_status_file}` does not exist.'
            LOGGER.warning('Failed to probe broker status: %s', error)
            return {'connected': connected, 'error': error}

        try:
            loaded_status = json.loads(self._service_status_file.read_text())
            if not isinstance(loaded_status, dict):
                msg = f'Invalid ZeroMQ service status file found: {loaded_status}'
                LOGGER.warning('Failed to probe broker status: %s', msg)
                status: BrokerServiceStatus = {'error': msg}
            else:
                status = t.cast(BrokerServiceStatus, loaded_status)
                status['error'] = None
        except (json.JSONDecodeError, OSError) as exception:
            error = f'{type(exception).__name__}: {exception}'
            LOGGER.warning('Failed to probe broker status: %s', error)
            return {'connected': connected, 'error': error}

        status['connected'] = connected
        return status

    # --- Communicator ---

    def get_communicator(self) -> ZeromqCommunicator:
        """Get or create a communicator connected to the broker."""
        if self._communicator is None:
            router_endpoint = self._router_endpoint

            if router_endpoint is None:
                # Broker may still be starting — poll until endpoint appears.
                deadline = time.monotonic() + BROKER_READY_TIMEOUT
                warning_deadline = deadline - (BROKER_READY_TIMEOUT - 5.0)
                warning_issued = False
                while time.monotonic() < deadline:
                    time.sleep(0.2)
                    router_endpoint = self._router_endpoint
                    if router_endpoint is not None:
                        break
                    if not warning_issued and time.monotonic() > warning_deadline:
                        LOGGER.warning('Still waiting for broker to become ready...')
                        warning_issued = True
                else:
                    msg = f'Broker did not become ready within {BROKER_READY_TIMEOUT}s: {self}'
                    raise ConnectionError(msg)

            from aiida.manage.configuration import get_config_option

            self._communicator = ZeromqCommunicator(
                router_endpoint=router_endpoint,
                task_timeout=get_config_option('broker.task_timeout'),
            )
            self._communicator.start()

        return self._communicator

    def iterate_tasks(self) -> t.Iterator[t.Any]:
        queue_path = self._storage_path / 'tasks'
        if not queue_path.exists():
            return

        queue = PersistentQueue(queue_path)
        for task_id, task_data in queue.get_all_pending():
            yield ZeromqIncomingTask(task_id, task_data, queue)

    def close(self) -> None:
        if self._communicator is not None:
            self._communicator.close()
            self._communicator = None

    def __enter__(self) -> ZeromqBroker:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: t.Any) -> None:
        self.close()


class ZeromqIncomingTask:
    """Wrapper providing an interface compatible with RabbitMQ incoming tasks."""

    def __init__(self, task_id: str, task_data: dict[str, t.Any], queue: PersistentQueue) -> None:
        self._task_id = task_id
        self._task_data = task_data
        self._queue = queue

        self.body = task_data.get('body')

    @contextmanager
    def processing(self) -> t.Iterator[t.Any]:
        class _Outcome:
            def set_result(self, result: t.Any) -> None:
                pass

        yield _Outcome()
        self._queue.remove_pending(self._task_id)
