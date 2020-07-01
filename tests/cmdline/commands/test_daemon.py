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
import pytest

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_daemon
from aiida.common.extendeddicts import AttributeDict
from aiida.engine.daemon.client import DaemonClient
from aiida.manage.configuration import get_config


class VerdiRunner(CliRunner):
    """Subclass of `click`'s `CliRunner` that injects an object in the context containing current config and profile."""

    def __init__(self, config, profile, **kwargs):
        """Construct an instance and define the `obj` dictionary that is required by the `Context`."""
        super().__init__(**kwargs)
        self.obj = AttributeDict({'config': config, 'profile': profile})

    def invoke(self, *args, **extra):  # pylint: disable=signature-differs
        """Invoke the command but add the `obj` to the `extra` keywords.

        The `**extra` keywords will be forwarded all the way to the `Context` that finally invokes the command. Some
        `verdi` commands will rely on this `obj` to be there to retrieve the current active configuration and profile.
        """
        extra['obj'] = self.obj
        return super().invoke(*args, **extra)


class TestVerdiDaemon(AiidaTestCase):
    """Tests for `verdi daemon` commands."""

    def setUp(self):
        super().setUp()
        self.config = get_config()
        self.profile = self.config.current_profile
        self.daemon_client = DaemonClient(self.profile)
        self.cli_runner = VerdiRunner(self.config, self.profile)

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

    def test_daemon_restart(self):
        """Test `verdi daemon restart` both with and without `--reset` flag."""
        try:
            result = self.cli_runner.invoke(cmd_daemon.start, [])
            self.assertClickResultNoException(result)

            result = self.cli_runner.invoke(cmd_daemon.restart, [])
            self.assertClickResultNoException(result)

            result = self.cli_runner.invoke(cmd_daemon.restart, ['--reset'])
            self.assertClickResultNoException(result)

            daemon_response = self.daemon_client.get_daemon_info()
            worker_response = self.daemon_client.get_worker_info()

            self.assertIn('status', daemon_response, daemon_response)
            self.assertEqual(daemon_response['status'], 'ok', daemon_response)

            self.assertIn('info', worker_response, worker_response)
            self.assertEqual(len(worker_response['info']), 1, worker_response)
        finally:
            self.daemon_client.stop_daemon(wait=True)

    @pytest.mark.skip(reason='Test fails non-deterministically; see issue #3051.')
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

    @pytest.mark.skip(reason='Test fails non-deterministically; see issue #3051.')
    def test_daemon_start_number_config(self):
        """Test `verdi daemon start` with `daemon.default_workers` config option being set."""
        number = 3
        self.config.set_option('daemon.default_workers', number, self.profile.name)

        try:
            result = self.cli_runner.invoke(cmd_daemon.start)
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
