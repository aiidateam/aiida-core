# -*- coding: utf-8 -*-
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
from aiida.plugins import CalculationFactory, WorkflowFactory
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
    'entry_point_string', (
        'aiida.calculations:arithmetic.add',
        'aiida.workflows:arithmetic.multiply_add',
        'aiida.workflows:arithmetic.add_multiply',
    )
)
def test_plugin_list_detail(run_cli_command, entry_point_string):
    """Test the `verdi plugin list` command for specific entry points."""
    from aiida.plugins.entry_point import parse_entry_point_string

    entry_point_group, entry_point_name = parse_entry_point_string(entry_point_string)
    factory = CalculationFactory if entry_point_group == 'aiida.calculations' else WorkflowFactory
    entry_point = factory(entry_point_name)

    result = run_cli_command(cmd_plugin.plugin_list, [entry_point_group, entry_point_name])
    assert entry_point.__doc__ in result.output
