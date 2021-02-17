# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi restapi`."""

from click.testing import CliRunner
import pytest

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_restapi import restapi


class TestVerdiRestapiCommand(AiidaTestCase):
    """tests for verdi restapi command"""

    def setUp(self):
        super().setUp()
        self.cli_runner = CliRunner()

    @pytest.mark.filterwarnings('ignore::aiida.common.warnings.AiidaDeprecationWarning')
    def test_run_restapi(self):
        """Test `verdi restapi`.

        Note: This test will need to be changed/removed once the hookup parameter is dropped from the CLI.
        """

        options = ['--no-hookup', '--hostname', 'localhost', '--port', '6000', '--debug', '--wsgi-profile']

        result = self.cli_runner.invoke(restapi, options)
        self.assertIsNone(result.exception, result.output)
        self.assertClickSuccess(result)

    def test_help(self):
        """Tests help text for restapi command."""
        options = ['--help']

        # verdi restapi
        result = self.cli_runner.invoke(restapi, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)
