###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `verdi plugin list` command."""

import pytest

from aiida.cmdline.commands import cmd_plugin
from aiida.parsers import Parser
from aiida.plugins import BaseFactory
from aiida.plugins.entry_point import ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP


def test_plugin_list(run_cli_command):
    """Test the `verdi plugin list` command.

    Call base command without parameters and check that all entry point groups are listed.
    """
    result = run_cli_command(cmd_plugin.plugin_list, [])
    for key in ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP:
        assert key in result.output


def test_plugin_list_group(run_cli_command):
    """Test the `verdi plugin list` command for entry point group.

    Call for each entry point group and just check it doesn't except.
    """
    for key in ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP:
        run_cli_command(cmd_plugin.plugin_list, [key])


def test_plugin_list_non_existing(run_cli_command):
    """Test the `verdi plugin list` command for a non-existing entry point."""
    run_cli_command(cmd_plugin.plugin_list, ['aiida.calculations', 'non_existing'], raises=True)


@pytest.mark.parametrize(
    'entry_point_string',
    (
        'aiida.calculations:core.arithmetic.add',
        'aiida.data:core.array',
        'aiida.workflows:core.arithmetic.multiply_add',
        'aiida.workflows:core.arithmetic.add_multiply',
    ),
)
def test_plugin_list_detail(run_cli_command, entry_point_string):
    """Test the `verdi plugin list` command for specific entry points."""
    from aiida.plugins.entry_point import parse_entry_point_string

    entry_point_group, entry_point_name = parse_entry_point_string(entry_point_string)
    entry_point = BaseFactory(entry_point_group, entry_point_name)

    result = run_cli_command(cmd_plugin.plugin_list, [entry_point_group, entry_point_name])
    assert entry_point.__doc__ in result.output


class NoDocStringPluginParser(Parser):
    pass


def test_plugin_list_no_docstring(run_cli_command, entry_points):
    """Test ``verdi plugin list`` does not fail if the plugin does not define a docstring."""
    entry_points.add(NoDocStringPluginParser, 'aiida.parsers:custom.parser')
    assert BaseFactory('aiida.parsers', 'custom.parser') is NoDocStringPluginParser

    result = run_cli_command(cmd_plugin.plugin_list, ['aiida.parsers', 'custom.parser'])
    assert result.output.strip() == 'Error: No description available for custom.parser'
