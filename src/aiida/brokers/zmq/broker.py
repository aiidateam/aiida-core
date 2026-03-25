"""ZMQ Broker - AiiDA Broker wrapper for ZMQ communicator."""

from __future__ import annotations

import json
import shutil
import time
import typing as t
from contextlib import contextmanager
from pathlib import Path

import psutil

from aiida.brokers.broker import Broker
from aiida.common.log import AIIDA_LOGGER

from .communicator import ZmqCommunicator
from .queue import PersistentQueue

if t.TYPE_CHECKING:
    from aiida.manage.configuration.profile import Profile

__all__ = ('ZmqBroker',)

LOGGER = AIIDA_LOGGER.getChild('broker.zmq')


class ZmqBroker(Broker):
    """AiiDA Broker implementation using ZeroMQ.

    Connects to a ZmqBrokerService for messaging and reads PID/status/socket
    files written by the service to discover endpoints and query status.
    """

    # Class attribute for type discovery
    Communicator = ZmqCommunicator

    def __init__(self, profile: 'Profile') -> None:
        super().__init__(profile)
        self._init_paths(get_broker_base_path(profile))

    def _init_paths(self, broker_dir: Path) -> None:
        self._communicator: ZmqCommunicator | None = None
        self._broker_dir = broker_dir
        self._storage_path = broker_dir / 'storage'
        self._service_pid_file = broker_dir / 'broker.pid'
        self._service_status_file = broker_dir / 'broker.status'
        self._service_sockets_file = broker_dir / 'broker.sockets'

    @classmethod
    def from_base_path(cls, base_path: Path | str) -> 'ZmqBroker':
        """Create a broker from a base path without a profile (for testing)."""
        instance = cls.__new__(cls)
        instance._profile = None
        instance._init_paths(Path(base_path))
        return instance

    def __str__(self) -> str:
        if self.is_running():
            status = self.get_service_status()
            pid = status.get('pid', '?') if status else '?'
            return f'ZMQ Broker (PID {pid}) @ {self._broker_dir}'
        return f'ZMQ Broker @ {self._broker_dir} <not running>'

    @property
    def storage_path(self) -> Path:
        return self._storage_path

    @property
    def base_path(self) -> Path:
        return self._broker_dir

    # --- Status queries (read PID/status/socket files) ---

    def _get_sockets_path(self) -> Path | None:
        if not self._service_sockets_file.exists():
            return None
        try:
            return Path(self._service_sockets_file.read_text().strip())
        except OSError:
            return None

    @property
    def router_endpoint(self) -> str | None:
        sockets_path = self._get_sockets_path()
        if sockets_path is None:
            return None
        return f'ipc://{sockets_path}/router.sock'

    _PID_SENTINEL = 'aiida-zmq-broker'

    def get_service_pid(self) -> int | None:
        """Read the ZmqBrokerService PID from its PID file.

        The PID file contains ``aiida-zmq-broker <pid>`` as a sentinel so we
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

    def is_running(self) -> bool:
        """Check if the ZmqBrokerService process is running."""
        pid = self.get_service_pid()
        if pid is None:
            return False
        try:
            proc = psutil.Process(pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def get_service_status(self) -> dict[str, t.Any] | None:
        """Read the ZmqBrokerService status from its status file."""
        if not self._service_status_file.exists():
            return None
        try:
            return json.loads(self._service_status_file.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def _cleanup_stale_service_files(self) -> None:
        self._service_pid_file.unlink(missing_ok=True)
        self._service_status_file.unlink(missing_ok=True)
        sockets_path = self._get_sockets_path()
        if sockets_path is not None and sockets_path.exists():
            shutil.rmtree(sockets_path, ignore_errors=True)
        self._service_sockets_file.unlink(missing_ok=True)

    # --- Communicator ---

    def get_communicator(self, wait_for_broker: float = 30.0) -> ZmqCommunicator:
        """Get or create a communicator connected to the broker.

        :param wait_for_broker: Seconds to wait for the broker to become ready.
            When the broker and workers are started concurrently (e.g. by circus),
            the broker may not have written its socket files yet. This parameter
            controls how long to poll before giving up.
        """
        if self._communicator is None:
            router_endpoint = self.router_endpoint

            if router_endpoint is None:
                # Broker may still be starting — poll until endpoint appears.
                deadline = time.monotonic() + wait_for_broker
                while time.monotonic() < deadline:
                    time.sleep(0.2)
                    router_endpoint = self.router_endpoint
                    if router_endpoint is not None:
                        break
                else:
                    raise ConnectionError(
                        f'Broker did not become ready within {wait_for_broker}s: {self}'
                    )

            self._communicator = ZmqCommunicator(
                router_endpoint=router_endpoint,
            )
            self._communicator.start()

        return self._communicator

    def iterate_tasks(self) -> t.Iterator['ZmqIncomingTask']:
        queue_path = self._storage_path / 'tasks'
        if not queue_path.exists():
            return

        queue = PersistentQueue(queue_path)
        for task_id, task_data in queue.get_all_pending():
            yield ZmqIncomingTask(task_id, task_data, queue)

    def close(self) -> None:
        if self._communicator is not None:
            self._communicator.close()
            self._communicator = None

    def __enter__(self) -> 'ZmqBroker':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class ZmqIncomingTask:
    """Wrapper providing an interface compatible with RabbitMQ incoming tasks."""

    def __init__(self, task_id: str, task_data: dict, queue: PersistentQueue) -> None:
        self._task_id = task_id
        self._task_data = task_data
        self._queue = queue
        self.body = task_data.get('body')

    @contextmanager
    def processing(self):
        class _Outcome:
            def set_result(self, result):
                pass

        yield _Outcome()
        self._queue.remove_pending(self._task_id)


def get_broker_base_path(profile: 'Profile') -> Path:
    from aiida.manage.configuration import get_config_path

    config_dir = Path(get_config_path()).parent
    return config_dir / 'broker' / profile.uuid
