# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `-v/--verbosity` option."""

from click.testing import CliRunner
from aiida.cmdline.params.options import VERBOSITY
from aiida.cmdline.commands import cmd_plugin


def test_plugin_list():
    """Test that verbosity option correctly controls output of 'verdi plugin list'."""

    # Note: When used on the command line, this is done by the verdi command group
    plugin_list = VERBOSITY()(cmd_plugin.plugin_list)

    for options in [[], ['-v', 'INFO']]:
        result = CliRunner().invoke(plugin_list, ['aiida.calculations'] + options)
        assert result.exception is None
        assert 'arithmetic.add' in result.stdout, result.stdout

    result = CliRunner().invoke(plugin_list, ['aiida.calculations', '-v', 'WARNING'])
    assert result.exception is None
    assert 'arithmetic.add' not in result.stdout, result.stdout
