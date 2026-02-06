"""ZMQ Broker Controller - client-side control for ZmqBrokerService.

This module provides a client-side interface to interact with the broker service
by reading PID/status files. Similar to AiiDA's DaemonClient pattern.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class ZmqBrokerController:
    """Controller for ZmqBrokerService.

    Allows external code to:
    - Start/stop the broker service
    - Check if service is running
    - Get service status

    Interacts with the service via PID/status files, not direct IPC.
    """

    def __init__(self, base_path: Path | str):
        """Initialize the controller.

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

        The socket directory is created in a temp location by ZmqBrokerService
        to avoid Unix domain socket path length limits.

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
        if HAS_PSUTIL:
            try:
                proc = psutil.Process(pid)
                # Check if process is running and is a Python process
                if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                    # Verify it's our broker by checking command line
                    cmdline = proc.cmdline()
                    return any('aiida.brokers.zmq' in arg for arg in cmdline)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        else:
            # Fallback: just check if process exists
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

        return False

    def is_running(self) -> bool:
        """Check if broker service is running.

        Validates that:
        1. PID file exists
        2. PID in file corresponds to a running broker process

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

    def start(self, foreground: bool = False, wait: bool = True, timeout: float = 10.0) -> bool:
        """Start the broker service.

        :param foreground: If True, run in foreground (blocking); else daemonize
        :param wait: If True and not foreground, wait for service to start
        :param timeout: Timeout in seconds when waiting for service to start
        :return: True if service started successfully
        """
        if self.is_running():
            return True

        # Ensure base path exists
        self._base_path.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [
            sys.executable,
            '-m',
            'aiida.brokers.zmq.service',
            '--base-path',
            str(self._base_path),
        ]

        if foreground:
            # Run in foreground (blocking)
            subprocess.run(cmd, check=True)
            return True
        else:
            # Run as daemon (detached process)
            # Use subprocess with appropriate flags for daemon behavior
            if sys.platform == 'win32':
                # Windows: use CREATE_NEW_PROCESS_GROUP
                subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )
            else:
                # Unix: use start_new_session
                subprocess.Popen(
                    cmd,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                )

            if wait:
                return self._wait_for_start(timeout)

            return True

    def _wait_for_start(self, timeout: float) -> bool:
        """Wait for service to start.

        :param timeout: Timeout in seconds
        :return: True if service started within timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running():
                return True
            time.sleep(0.1)
        return False

    def stop(self, timeout: float = 5.0) -> bool:
        """Stop the broker service.

        Uses SIGINT for cross-platform graceful shutdown.
        Falls back to hard kill if timeout expires.

        :param timeout: Seconds to wait for graceful shutdown
        :return: True if stopped successfully
        """
        pid = self.get_pid()
        if pid is None:
            return True

        if not self._validate_pid(pid):
            # PID file exists but process is not running, clean up
            self._cleanup_stale_files()
            return True

        # Send SIGINT for graceful shutdown (works on all platforms)
        try:
            os.kill(pid, signal.SIGINT)
        except OSError:
            # Process already gone
            self._cleanup_stale_files()
            return True

        # Wait for graceful shutdown
        if self._wait_for_stop(pid, timeout):
            return True

        # Graceful shutdown failed, try hard kill
        return self._force_kill(pid)

    def _wait_for_stop(self, pid: int, timeout: float) -> bool:
        """Wait for process to stop.

        :param pid: Process ID
        :param timeout: Timeout in seconds
        :return: True if process stopped within timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self._validate_pid(pid):
                self._cleanup_stale_files()
                return True
            time.sleep(0.1)
        return False

    def _force_kill(self, pid: int) -> bool:
        """Force kill a process.

        :param pid: Process ID
        :return: True if killed successfully
        """
        if HAS_PSUTIL:
            try:
                proc = psutil.Process(pid)
                proc.terminate()  # Sends SIGTERM on Unix, TerminateProcess on Windows
                proc.wait(timeout=2.0)
                self._cleanup_stale_files()
                return True
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    proc.kill()  # SIGKILL on Unix, TerminateProcess on Windows
                    self._cleanup_stale_files()
                    return True
                except psutil.NoSuchProcess:
                    self._cleanup_stale_files()
                    return True
            except psutil.AccessDenied:
                return False
        else:
            # Without psutil, try SIGKILL on Unix (not available on Windows)
            if sys.platform != 'win32':
                try:
                    os.kill(pid, signal.SIGKILL)
                    self._cleanup_stale_files()
                    return True
                except OSError:
                    self._cleanup_stale_files()
                    return True
            return False  # type: ignore[unreachable]  # Windows without psutil

    def _cleanup_stale_files(self) -> None:
        """Clean up stale PID and status files."""
        if self._pid_file.exists():
            self._pid_file.unlink(missing_ok=True)
        if self._status_file.exists():
            self._status_file.unlink(missing_ok=True)

    def restart(self, timeout: float = 5.0) -> bool:
        """Restart the broker service.

        :param timeout: Timeout for stop operation
        :return: True if restarted successfully
        """
        self.stop(timeout=timeout)
        return self.start(wait=True)
