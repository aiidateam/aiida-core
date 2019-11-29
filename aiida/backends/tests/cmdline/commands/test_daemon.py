# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi daemon`."""

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_daemon
from aiida.engine.daemon.client import DaemonClient
from aiida.manage.configuration import get_config


class TestVerdiDaemon(AiidaTestCase):
    """Tests for `verdi daemon` commands."""

    def setUp(self):
        super().setUp()
        self.daemon_client = DaemonClient(get_config().current_profile)
        self.cli_runner = CliRunner()

    def test_daemon_start(self):
        """Test `verdi daemon start`."""
        try:
            result = self.cli_runner.invoke(cmd_daemon.start, [])
            self.assertClickResultNoException(result)

            daemon_response = self.daemon_client.get_daemon_info()
            worker_response = self.daemon_client.get_worker_info()

            self.assertIn('status', daemon_response, daemon_response)
            self.assertEqual(daemon_response['status'], 'ok', daemon_response)

            self.assertIn('info', worker_response, worker_response)
            self.assertEqual(len(worker_response['info']), 1, worker_response)
        finally:
            self.daemon_client.stop_daemon(wait=True)

    def test_daemon_start_number(self):
        """Test `verdi daemon start` with a specific number of workers."""

        # The `number` argument should be a positive non-zero integer
        for invalid_number in ['string', 0, -1]:
            result = self.cli_runner.invoke(cmd_daemon.start, [str(invalid_number)])
            self.assertIsNotNone(result.exception)

        try:
            number = 4
            result = self.cli_runner.invoke(cmd_daemon.start, [str(number)])
            self.assertClickResultNoException(result)

            daemon_response = self.daemon_client.get_daemon_info()
            worker_response = self.daemon_client.get_worker_info()

            self.assertIn('status', daemon_response, daemon_response)
            self.assertEqual(daemon_response['status'], 'ok', daemon_response)

            self.assertIn('info', worker_response, worker_response)
            self.assertEqual(len(worker_response['info']), number, worker_response)
        finally:
            self.daemon_client.stop_daemon(wait=True)

    def test_foreground_multiple_workers(self):
        """Test `verdi daemon start` in foreground with more than one worker will fail."""
        try:
            number = 4
            result = self.cli_runner.invoke(cmd_daemon.start, ['--foreground', str(number)])
            self.assertIsNotNone(result.exception)
        finally:
            self.daemon_client.stop_daemon(wait=True)
