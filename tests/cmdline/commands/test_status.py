# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi status`."""
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_status

from tests.utils.configuration import with_temporary_config_instance


class TestVerdiStatus(AiidaTestCase):
    """Tests for `verdi status`.

    Note: The exit status may differ depending on the environment in which the tests are run.
        Also cannot check for the exit status to see if connecting to all services worked, because
        the profile might not be properly setup in this temporary config instance unittest.
    """

    def setUp(self):
        super().setUp()
        self.cli_runner = CliRunner()

    @with_temporary_config_instance
    def test_status_1(self):
        """Test running verdi status."""
        options = []
        result = self.cli_runner.invoke(cmd_status.verdi_status, options)
        self.assertIsInstance(result.exception, SystemExit)
        for string in ['config', 'profile', 'postgres', 'rabbitmq', 'daemon']:
            self.assertIn(string, result.output)

    @with_temporary_config_instance
    def test_status_no_rmq(self):
        """Test running verdi status, with no rmq check"""
        options = ['--no-rmq']
        result = self.cli_runner.invoke(cmd_status.verdi_status, options)
        self.assertIsInstance(result.exception, SystemExit)
        for string in ['config', 'profile', 'postgres', 'daemon']:
            self.assertIn(string, result.output)
        self.assertNotIn('rabbitmq', result.output)

    @with_temporary_config_instance
    def test_status_no_daemon(self):
        """Test running verdi status, with no daemon check"""
        options = ['--no-daemon']
        result = self.cli_runner.invoke(cmd_status.verdi_status, options)
        self.assertIsInstance(result.exception, SystemExit)
        for string in ['config', 'profile', 'postgres', 'rabbitmq']:
            self.assertIn(string, result.output)
        self.assertNotIn('daemon', result.output)
