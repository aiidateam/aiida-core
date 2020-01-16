# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi help`."""

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_verdi

from tests.utils.configuration import with_temporary_config_instance


class TestVerdiHelpCommand(AiidaTestCase):
    """Tests for `verdi help`."""

    def setUp(self):
        super().setUp()
        self.cli_runner = CliRunner()

    @with_temporary_config_instance
    def test_without_arg(self):
        """
        Ensure we get the same help for `verdi` (which gives the same as `verdi --help`)
        and `verdi help`
        """
        # don't invoke the cmd directly to make sure ctx.parent is properly populated
        # as it would be when called as a cli
        result_help = self.cli_runner.invoke(cmd_verdi.verdi, ['help'], catch_exceptions=False)
        result_verdi = self.cli_runner.invoke(cmd_verdi.verdi, [], catch_exceptions=False)
        self.assertEqual(result_help.output, result_verdi.output)

    @with_temporary_config_instance
    def test_cmd_help(self):
        """Ensure we get the same help for `verdi user --help` and `verdi help user`"""
        result_help = self.cli_runner.invoke(cmd_verdi.verdi, ['help', 'user'], catch_exceptions=False)
        result_user = self.cli_runner.invoke(cmd_verdi.verdi, ['user', '--help'], catch_exceptions=False)
        self.assertEqual(result_help.output, result_user.output)
