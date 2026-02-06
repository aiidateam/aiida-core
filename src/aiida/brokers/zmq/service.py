"""ZMQ Broker Service - thin process wrapper for ZmqBrokerServer.

This module provides process lifecycle management for the ZMQ broker server:
- PID file management
- Signal handling (SIGINT for cross-platform shutdown)
- Status file updates
- CLI entry point
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import signal
import tempfile
import time
from pathlib import Path
from typing import Any

from .server import ZmqBrokerServer

_LOGGER = logging.getLogger(__name__)


class ZmqBrokerService:
    """Process wrapper for ZmqBrokerServer.

    Responsibilities:
    - Instantiate and run ZmqBrokerServer
    - Write PID file on start, remove on stop
    - Handle SIGINT for cross-platform shutdown
    - Write status info to file periodically

    Directory structure:
        {base_path}/
        ├── storage/        # Task queue persistence (passed to server)
        ├── logs/           # Log files
        ├── broker.pid      # PID file
        ├── broker.status   # Status JSON file
        └── broker.sockets  # Path to temp directory containing sockets

        {temp_dir}/         # Temp directory for sockets (short path for IPC)
        ├── router.sock
        └── pub.sock

    Note: Unix domain sockets have a path length limit (~107 bytes), so we use
    a temporary directory with a short path for the socket files.
    """

    def __init__(
        self,
        base_path: Path | str,
        log_file: Path | str | None = None,
    ):
        """Initialize the broker service.

        :param base_path: Base path for broker data
        :param log_file: Path to log file (default: {base_path}/logs/broker.log)
        """
        self._base_path = Path(base_path)
        self._storage_path = self._base_path / 'storage'
        self._logs_path = self._base_path / 'logs'

        # Sockets will be created in a temp directory (short path for IPC limit)
        self._sockets_path: Path | None = None
        self._sockets_file = self._base_path / 'broker.sockets'

        # Ensure directories exist
        self._logs_path.mkdir(parents=True, exist_ok=True)

        # File paths
        self._pid_file = self._base_path / 'broker.pid'
        self._status_file = self._base_path / 'broker.status'
        self._log_file = Path(log_file) if log_file else self._logs_path / 'broker.log'

        # Server instance
        self._server: ZmqBrokerServer | None = None
        self._running = False

        # Set up logging
        self._setup_logging()

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

    @property
    def log_file(self) -> Path:
        """Return the log file path."""
        return self._log_file

    def _setup_logging(self) -> None:
        """Set up file logging for the broker service."""
        file_handler = logging.FileHandler(self._log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        # Add handler to relevant loggers
        for logger_name in [__name__, 'aiida.brokers.zmq.server', 'aiida.brokers.zmq.queue']:
            logger = logging.getLogger(logger_name)
            logger.addHandler(file_handler)
            logger.setLevel(logging.DEBUG)

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown.

        Uses SIGINT which is available on all platforms (including Windows).
        """
        signal.signal(signal.SIGINT, self._handle_shutdown)
        _LOGGER.debug('Signal handlers installed')

    def _handle_shutdown(self, signum: int, frame: Any) -> None:
        """Handle shutdown signal."""
        _LOGGER.info('Received shutdown signal (%s)', signum)
        self._running = False

    def _write_pid_file(self) -> None:
        """Write current PID to file."""
        pid = os.getpid()
        self._pid_file.write_text(str(pid))
        _LOGGER.debug('Wrote PID file: %s (pid=%d)', self._pid_file, pid)

    def _remove_pid_file(self) -> None:
        """Remove PID file."""
        if self._pid_file.exists():
            self._pid_file.unlink()
            _LOGGER.debug('Removed PID file: %s', self._pid_file)

    def _write_status(self, status: dict) -> None:
        """Write status info to file."""
        status['timestamp'] = time.time()
        status['pid'] = os.getpid()

        # Write atomically
        temp_file = self._status_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(status, indent=2))
        temp_file.rename(self._status_file)

    def _remove_status_file(self) -> None:
        """Remove status file."""
        if self._status_file.exists():
            self._status_file.unlink()
            _LOGGER.debug('Removed status file: %s', self._status_file)

    def _create_sockets_directory(self) -> Path:
        """Create a temporary directory for socket files.

        Unix domain sockets have a path length limit (~107 bytes on macOS, 108 on Linux).
        We use a temporary directory to ensure the path is short enough.

        :return: Path to the temporary socket directory
        """
        socket_dir = Path(tempfile.mkdtemp(prefix='aiida_zmq_'))
        self._sockets_file.write_text(str(socket_dir))
        _LOGGER.debug('Created socket directory: %s', socket_dir)
        return socket_dir

    def _remove_sockets_directory(self) -> None:
        """Remove the temporary socket directory."""
        if self._sockets_path and self._sockets_path.exists():
            try:
                shutil.rmtree(self._sockets_path)
                _LOGGER.debug('Removed socket directory: %s', self._sockets_path)
            except OSError as e:
                _LOGGER.warning('Failed to remove socket directory: %s', e)

        if self._sockets_file.exists():
            self._sockets_file.unlink()
            _LOGGER.debug('Removed sockets file: %s', self._sockets_file)

    def start(self) -> None:
        """Start the broker service.

        Creates the server and writes PID file.
        """
        if self._running:
            return

        _LOGGER.info('Starting ZMQ Broker Service')
        _LOGGER.info('Base path: %s', self._base_path)
        _LOGGER.info('Log file: %s', self._log_file)

        # Create temp directory for sockets (short path for IPC limit)
        self._sockets_path = self._create_sockets_directory()
        _LOGGER.info('Sockets path: %s', self._sockets_path)

        # Create server
        self._server = ZmqBrokerServer(
            storage_path=self._storage_path,
            sockets_path=self._sockets_path,
        )

        # Write PID file
        self._write_pid_file()

        # Set up signal handlers
        self._setup_signal_handlers()

        # Start server
        self._server.start()
        self._running = True

        # Write initial status
        self._write_status(self._server.get_status())

        _LOGGER.info('ZMQ Broker Service started')

    def stop(self) -> None:
        """Stop the broker service.

        Stops the server and removes PID file.
        """
        if not self._running:
            return

        _LOGGER.info('Stopping ZMQ Broker Service')
        self._running = False

        if self._server:
            self._server.stop()
            self._server = None

        self._remove_pid_file()
        self._remove_status_file()
        self._remove_sockets_directory()

        _LOGGER.info('ZMQ Broker Service stopped')

    def run_forever(self, poll_timeout: int = 1000, status_interval: float = 5.0) -> None:
        """Run the broker service until stopped.

        Blocks until stop() is called or SIGINT received.

        :param poll_timeout: Polling timeout in milliseconds
        :param status_interval: Interval for status file updates in seconds
        """
        self.start()

        last_status_time = time.time()

        try:
            while self._running and self._server:
                self._server.run_once(poll_timeout)

                # Update status file periodically
                now = time.time()
                if now - last_status_time >= status_interval:
                    self._write_status(self._server.get_status())
                    last_status_time = now

        except KeyboardInterrupt:
            _LOGGER.info('Interrupted')
        finally:
            self.stop()


def run_broker_service(
    base_path: str | Path,
    log_file: str | Path | None = None,
) -> None:
    """Run the broker service as a standalone process.

    :param base_path: Base path for broker data
    :param log_file: Path to log file (default: {base_path}/logs/broker.log)
    """
    service = ZmqBrokerService(
        base_path=base_path,
        log_file=log_file,
    )
    service.run_forever()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='ZMQ Broker Service')
    parser.add_argument('--base-path', '-b', required=True, help='Base directory for broker data')
    parser.add_argument('--log-file', '-l', help='Log file path (default: {base_path}/logs/broker.log)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable debug logging to console')

    args = parser.parse_args()

    # Set up console logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    run_broker_service(
        base_path=args.base_path,
        log_file=args.log_file,
    )
