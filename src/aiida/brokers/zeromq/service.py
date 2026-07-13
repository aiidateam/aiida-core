"""ZeroMQ Broker Service - process wrapper for ZeromqBrokerServer.

Manages PID/status files, socket directory, signal handling, and broker logging.
Circus handles process lifecycle (daemonization and keepalive).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import signal
import tempfile
import time
import typing as t
from pathlib import Path

from aiida.common.log import configure_logging

from .defaults import POLL_TIMEOUT, STATUS_INTERVAL
from .server import ZeromqBrokerServer

_LOGGER = logging.getLogger(__name__)

PID_SENTINEL = 'aiida-zeromq-broker'


class ZeromqBrokerService:
    """Process wrapper for ZeromqBrokerServer.

    Directory structure:
        {base_path}/
        ├── storage/        # Task queue persistence
        ├── broker.log      # Broker log file, location is configurable
        ├── broker.pid      # PID file
        ├── broker.status   # Status JSON file
        └── broker.sockets  # Path to temp socket directory

        {temp_dir}/         # Short path for IPC socket limit
        └── router.sock
    """

    class FilepathLayout:
        """Canonical filesystem layout for the ZMQ broker state files."""

        def __init__(self, base_path: Path | str, log_file_path: Path | str | None = None) -> None:
            self.base_path = Path(base_path)
            self._log_file_path = None if log_file_path is None else Path(log_file_path)

        @property
        def storage_path(self) -> Path:
            """Return the persistent storage directory."""
            return self.base_path / 'storage'

        @property
        def log_file(self) -> Path:
            """Return the broker log file."""
            return self.base_path / 'broker.log' if self._log_file_path is None else self._log_file_path

        @property
        def pid_file(self) -> Path:
            """Return the broker PID file."""
            return self.base_path / 'broker.pid'

        @property
        def status_file(self) -> Path:
            """Return the broker status file."""
            return self.base_path / 'broker.status'

        @property
        def sockets_file(self) -> Path:
            """Return the file containing the temporary sockets directory path."""
            return self.base_path / 'broker.sockets'

    def __init__(self, base_path: Path | str, log_file_path: Path | str | None = None):
        self._layout = self.FilepathLayout(base_path, log_file_path=log_file_path)
        self._base_path = self._layout.base_path
        self._storage_path = self._layout.storage_path
        self._sockets_path: Path | None = None
        self._log_file = self._layout.log_file
        self._sockets_file = self._layout.sockets_file
        self._pid_file = self._layout.pid_file
        self._status_file = self._layout.status_file
        self._server: ZeromqBrokerServer | None = None
        self._running = False

    @property
    def base_path(self) -> Path:
        return self._base_path

    @property
    def log_file(self) -> Path:
        return self._log_file

    @property
    def pid_file(self) -> Path:
        return self._pid_file

    @property
    def status_file(self) -> Path:
        return self._status_file

    def start(self) -> None:
        if self._running:
            return

        self._base_path.mkdir(parents=True, exist_ok=True)

        # Clean up any orphaned socket directory from a previous unclean shutdown
        if self._sockets_file.exists():
            try:
                old_path = Path(self._sockets_file.read_text().strip())
                if old_path.exists():
                    shutil.rmtree(old_path, ignore_errors=True)
            except Exception:
                pass

        # Use temp directory for sockets (Unix IPC path limit ~107 bytes)
        self._sockets_path = Path(tempfile.mkdtemp(prefix='aiida_zeromq_'))
        self._sockets_file.write_text(str(self._sockets_path))

        self._server = ZeromqBrokerServer(
            storage_path=self._storage_path,
            sockets_path=self._sockets_path,
        )

        self._pid_file.write_text(f'{PID_SENTINEL} {os.getpid()}')

        # SIGINT (ctrl-c / circus graceful) + SIGTERM (circus stop)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        self._server.start()
        self._running = True
        self._write_status(self._server.get_status())

    def stop(self) -> None:
        self._running = False

        if self._server:
            self._server.stop()
            self._server = None

        self._pid_file.unlink(missing_ok=True)
        self._status_file.unlink(missing_ok=True)
        if self._sockets_path and self._sockets_path.exists():
            shutil.rmtree(self._sockets_path, ignore_errors=True)
        self._sockets_file.unlink(missing_ok=True)

    def run_forever(self, poll_timeout: float = POLL_TIMEOUT, status_interval: float = STATUS_INTERVAL) -> None:
        """Run until SIGINT/SIGTERM."""
        self.start()
        last_status_time = time.time()
        try:
            while self._running and self._server:
                self._server.run_once(poll_timeout)
                now = time.time()
                if now - last_status_time >= status_interval:
                    self._write_status(self._server.get_status())
                    last_status_time = now
        finally:
            self.stop()

    def _handle_shutdown(self, signum: int, frame: t.Any) -> None:
        _LOGGER.info('Received signal %s, shutting down', signum)
        self._running = False

    def _write_status(self, status: dict[str, t.Any]) -> None:
        status['timestamp'] = time.time()
        status['pid'] = os.getpid()
        temp_file = self._status_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(status, indent=2))
        temp_file.rename(self._status_file)


def run_broker_service(base_path: str | Path, log_file_path: Path | str | None = None) -> None:
    """Run the ZeroMQ broker service."""
    service = ZeromqBrokerService(base_path=base_path, log_file_path=log_file_path)
    service.base_path.mkdir(parents=True, exist_ok=True)
    configure_logging(daemon=True, daemon_log_file=service.log_file)
    service.run_forever()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-path', '-b', required=True)
    parser.add_argument('--log-file-path', '-l', required=False)
    args = parser.parse_args()
    run_broker_service(base_path=args.base_path, log_file_path=args.log_file_path)
