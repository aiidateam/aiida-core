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
import pytest

from aiida.cmdline.commands import cmd_verdi


class TestVerdiHelpCommand:
    """Tests for `verdi help`."""

    @pytest.fixture(autouse=True)
    def init_profile(self, config_with_profile, run_cli_command):  # pylint: disable=unused-argument
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init
        self.cli_runner = run_cli_command

    def test_without_arg(self):
        """
        Ensure we get the same help for `verdi` (which gives the same as `verdi --help`)
        and `verdi help`
        """
        # don't invoke the cmd directly to make sure ctx.parent is properly populated
        # as it would be when called as a cli
        result_help = self.cli_runner(cmd_verdi.verdi, ['help'])
        result_verdi = self.cli_runner(cmd_verdi.verdi, [])
        assert result_help.output == result_verdi.output

    def test_cmd_help(self):
        """Ensure we get the same help for `verdi user --help` and `verdi help user`"""
        result_help = self.cli_runner(cmd_verdi.verdi, ['help', 'user'])
        result_user = self.cli_runner(cmd_verdi.verdi, ['user', '--help'])
        assert result_help.output == result_user.output
