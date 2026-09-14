###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``aiida.brokers.zeromq.service.ZeromqBrokerService``."""

from __future__ import annotations

import threading
import time
from unittest.mock import patch

from aiida.brokers.zeromq.service import ZeromqBrokerService, run_broker_service


class TestZeromqBrokerService:
    """Tests for the ZeromqBrokerService."""

    def test_init(self, tmp_path):
        """Test service initialization."""
        service = ZeromqBrokerService(service_dir=tmp_path)
        assert service.service_dir == tmp_path
        assert service.log_file == tmp_path / 'broker.log'
        assert service.pid_file == tmp_path / 'broker.pid'
        assert service.status_file == tmp_path / 'broker.status'

    def test_run_broker_service_configures_logging(self, tmp_path):
        """Test ``run_broker_service`` configures persistent broker logging."""
        with (
            patch('aiida.brokers.zeromq.service.configure_logging') as mock_configure_logging,
            patch.object(ZeromqBrokerService, 'run_forever') as mock_run_forever,
        ):
            run_broker_service(service_dir=tmp_path)

        mock_configure_logging.assert_called_once_with(daemon=True, daemon_log_file=tmp_path / 'broker.log')
        mock_run_forever.assert_called_once_with()
        assert tmp_path.is_dir()

    def test_start_stop(self, tmp_path):
        """Test starting and stopping the service."""
        service = ZeromqBrokerService(service_dir=tmp_path)
        service.start()

        try:
            assert service.pid_file.exists()
            assert service.status_file.exists()
        finally:
            service.stop()

        assert not service.pid_file.exists()
        assert not service.status_file.exists()

    def test_start_idempotent(self, tmp_path):
        """Test start is idempotent."""
        service = ZeromqBrokerService(service_dir=tmp_path)
        service.start()
        try:
            service.start()  # should be no-op
            assert service._running
        finally:
            service.stop()

    def test_stop_idempotent(self, tmp_path):
        """Test stop when not running is no-op."""
        service = ZeromqBrokerService(service_dir=tmp_path)
        service.stop()  # should not raise

    def test_orphaned_sockets_cleanup(self, tmp_path):
        """Test cleanup of orphaned sockets from previous run."""
        sockets_file = tmp_path / 'broker.sockets'
        old_sockets = tmp_path / 'old_sockets'
        old_sockets.mkdir()
        sockets_file.write_text(str(old_sockets))

        service = ZeromqBrokerService(service_dir=tmp_path)
        service.start()
        try:
            assert not old_sockets.exists()
        finally:
            service.stop()

    def test_run_forever_with_early_stop(self, tmp_path):
        """Test run_forever exits when _running is set to False."""
        service = ZeromqBrokerService(service_dir=tmp_path)

        def stop_after_delay():
            time.sleep(0.5)
            service._running = False

        t = threading.Thread(target=stop_after_delay, daemon=True)
        t.start()

        service.run_forever(poll_timeout=0.1, status_interval=0.2)

        assert not service._running
        t.join(timeout=2)
