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
from aiida.cmdline.commands import cmd_verdi


class TestVerdiHelpCommand:
    """Tests for `verdi help`."""

    def test_without_arg(self, run_cli_command):
        """Ensure we get the same help for `verdi` (which gives the same as `verdi --help`) and `verdi help`."""
        # don't invoke the cmd directly to make sure ctx.parent is properly populated
        # as it would be when called as a cli
        result_help = run_cli_command(cmd_verdi.verdi, ['help'], use_subprocess=False)
        result_verdi = run_cli_command(cmd_verdi.verdi, [], use_subprocess=False)
        assert result_help.output == result_verdi.output

    def test_cmd_help(self, run_cli_command):
        """Ensure we get the same help for `verdi user --help` and `verdi help user`"""
        result_help = run_cli_command(cmd_verdi.verdi, ['help', 'user'])
        result_user = run_cli_command(cmd_verdi.verdi, ['user', '--help'])
        assert result_help.output == result_user.output
