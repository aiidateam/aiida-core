"""ZMQ Broker Management Client - read-only query interface for ZmqBrokerService.

This module provides a read-only interface to query broker service status
via PID/status files. The broker lifecycle is managed by circus (production)
or test helpers (testing).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import psutil


class ZmqBrokerManagementClient:
    """Read-only management client for ZmqBrokerService.

    Provides:
    - Status queries (is_running, get_status, get_pid)
    - Endpoint discovery (router_endpoint, pub_endpoint)

    Interacts with the service via PID/status files, not direct IPC.
    """

    def __init__(self, base_path: Path | str):
        """Initialize the client.

        :param base_path: Base path for broker data (same as ZmqBrokerService)
        """
        self._base_path = Path(base_path)
        self._pid_file = self._base_path / 'broker.pid'
        self._status_file = self._base_path / 'broker.status'
        self._sockets_file = self._base_path / 'broker.sockets'

    @property
    def base_path(self) -> Path:
        """Return the base path for broker data."""
        return self._base_path

    @property
    def pid_file(self) -> Path:
        """Return the PID file path."""
        return self._pid_file

    @property
    def status_file(self) -> Path:
        """Return the status file path."""
        return self._status_file

    def _get_sockets_path(self) -> Path | None:
        """Read the socket directory path from file.

        :return: Path to socket directory, or None if not available
        """
        if not self._sockets_file.exists():
            return None
        try:
            return Path(self._sockets_file.read_text().strip())
        except OSError:
            return None

    @property
    def router_endpoint(self) -> str | None:
        """Return the ROUTER socket endpoint.

        :return: Endpoint string, or None if broker is not running
        """
        sockets_path = self._get_sockets_path()
        if sockets_path is None:
            return None
        return f'ipc://{sockets_path}/router.sock'

    @property
    def pub_endpoint(self) -> str | None:
        """Return the PUB socket endpoint.

        :return: Endpoint string, or None if broker is not running
        """
        sockets_path = self._get_sockets_path()
        if sockets_path is None:
            return None
        return f'ipc://{sockets_path}/pub.sock'

    def get_pid(self) -> int | None:
        """Get broker PID from file.

        :return: PID if file exists and is valid, None otherwise
        """
        if not self._pid_file.exists():
            return None

        try:
            pid_str = self._pid_file.read_text().strip()
            return int(pid_str)
        except (ValueError, OSError):
            return None

    def _validate_pid(self, pid: int) -> bool:
        """Validate that PID is a running broker process.

        :param pid: Process ID to validate
        :return: True if PID is valid and running
        """
        try:
            proc = psutil.Process(pid)
            if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                cmdline = proc.cmdline()
                return any('aiida.brokers.zmq' in arg for arg in cmdline)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

        return False

    def is_running(self) -> bool:
        """Check if broker service is running.

        :return: True if service is running
        """
        pid = self.get_pid()
        if pid is None:
            return False

        return self._validate_pid(pid)

    def get_status(self) -> dict[str, Any] | None:
        """Read status from file.

        :return: Status dictionary or None if not available
        """
        if not self._status_file.exists():
            return None

        try:
            return json.loads(self._status_file.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def _cleanup_stale_files(self) -> None:
        """Clean up stale PID, status, and socket files."""
        if self._pid_file.exists():
            self._pid_file.unlink(missing_ok=True)
        if self._status_file.exists():
            self._status_file.unlink(missing_ok=True)

        sockets_path = self._get_sockets_path()
        if sockets_path is not None and sockets_path.exists():
            try:
                shutil.rmtree(sockets_path)
            except OSError:
                pass
        if self._sockets_file.exists():
            self._sockets_file.unlink(missing_ok=True)
