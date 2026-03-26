"""ZMQ Broker Service - process wrapper for ZmqBrokerServer.

Manages PID/status files, socket directory, and signal handling.
Circus handles process lifecycle (daemonization, keepalive, log capture).
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

from .server import ZmqBrokerServer

_LOGGER = logging.getLogger(__name__)


class ZmqBrokerService:
    """Process wrapper for ZmqBrokerServer.

    Directory structure:
        {base_path}/
        ├── storage/        # Task queue persistence
        ├── logs/
        │   └── broker.log  # Broker service log
        ├── broker.pid      # PID file
        ├── broker.status   # Status JSON file
        └── broker.sockets  # Path to temp socket directory

        {temp_dir}/         # Short path for IPC socket limit
        └── router.sock
    """

    def __init__(self, base_path: Path | str):
        self._base_path = Path(base_path)
        self._storage_path = self._base_path / 'storage'
        self._sockets_path: Path | None = None
        self._sockets_file = self._base_path / 'broker.sockets'
        self._pid_file = self._base_path / 'broker.pid'
        self._status_file = self._base_path / 'broker.status'
        self._log_file = self._base_path / 'logs' / 'broker.log'
        self._server: ZmqBrokerServer | None = None
        self._running = False

    @property
    def base_path(self) -> Path:
        return self._base_path

    @property
    def pid_file(self) -> Path:
        return self._pid_file

    @property
    def status_file(self) -> Path:
        return self._status_file

    def _setup_logging(self) -> None:
        """Set up file logging for the broker service."""
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(self._log_file)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        for name in [__name__, 'aiida.brokers.zmq.server', 'aiida.brokers.zmq.queue']:
            logger = logging.getLogger(name)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    def start(self) -> None:
        if self._running:
            return

        self._base_path.mkdir(parents=True, exist_ok=True)
        self._setup_logging()

        # Use temp directory for sockets (Unix IPC path limit ~107 bytes)
        self._sockets_path = Path(tempfile.mkdtemp(prefix='aiida_zmq_'))
        self._sockets_file.write_text(str(self._sockets_path))

        from aiida.brokers.utils import YAML_DECODER, YAML_ENCODER

        self._server = ZmqBrokerServer(
            storage_path=self._storage_path,
            sockets_path=self._sockets_path,
            encoder=YAML_ENCODER,
            decoder=YAML_DECODER,
        )

        self._pid_file.write_text(f'aiida-zmq-broker {os.getpid()}')

        # SIGINT (ctrl-c / circus graceful) + SIGTERM (circus stop)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        self._server.start()
        self._running = True
        self._write_status(self._server.get_status())

    def stop(self) -> None:
        if not self._running:
            return

        self._running = False

        if self._server:
            self._server.stop()
            self._server = None

        self._pid_file.unlink(missing_ok=True)
        self._status_file.unlink(missing_ok=True)
        if self._sockets_path and self._sockets_path.exists():
            shutil.rmtree(self._sockets_path, ignore_errors=True)
        self._sockets_file.unlink(missing_ok=True)

    def run_forever(self, poll_timeout: int = 1000, status_interval: float = 5.0) -> None:
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

    def _handle_shutdown(self, signum: int, frame) -> None:
        _LOGGER.info('Received signal %s, shutting down', signum)
        self._running = False

    def _write_status(self, status: dict) -> None:
        status['timestamp'] = time.time()
        status['pid'] = os.getpid()
        temp_file = self._status_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(status, indent=2))
        temp_file.rename(self._status_file)


def run_broker_service(base_path: str | Path) -> None:
    """Entry point for ``verdi daemon broker``."""
    ZmqBrokerService(base_path=base_path).run_forever()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--base-path', '-b', required=True)
    args = parser.parse_args()
    run_broker_service(base_path=args.base_path)
