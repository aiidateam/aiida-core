###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi`."""

import click
import pytest

from aiida import get_version
from aiida.cmdline.commands import cmd_verdi


@pytest.mark.usefixtures('config_with_profile')
def test_verdi_version(run_cli_command):
    """Regression test for #2238: verify that `verdi --version` prints the current version"""
    result = run_cli_command(cmd_verdi.verdi, ['--version'])
    assert get_version() in result.output


@pytest.mark.usefixtures('config_with_profile')
def test_verdi_with_empty_profile_list(run_cli_command):
    """Regression test for #2424: verify that verdi remains operable even if profile list is empty"""
    from aiida.manage.configuration import CONFIG

    # Run verdi command with updated CONFIG featuring an empty profile list
    CONFIG.dictionary[CONFIG.KEY_PROFILES] = {}
    run_cli_command(cmd_verdi.verdi, ['-h'], use_subprocess=False)


@pytest.mark.usefixtures('config_with_profile')
def test_invalid_cmd_matches(run_cli_command):
    """Test that verdi with an invalid command will return matches if somewhat close"""
    result = run_cli_command(cmd_verdi.verdi, ['usr'], raises=True)
    assert 'is not a verdi command' in result.output
    assert 'The most similar commands are' in result.output
    assert 'user' in result.output


@pytest.mark.usefixtures('config_with_profile')
def test_invalid_cmd_no_matches(run_cli_command):
    """Test that verdi with an invalid command with no matches returns an appropriate message"""
    result = run_cli_command(cmd_verdi.verdi, ['foobar'], raises=True)
    assert 'is not a verdi command' in result.output
    assert 'No similar commands found' in result.output


def test_verbosity_options():
    """Recursively find all leaf commands of ``verdi`` and ensure they have the ``--verbosity`` option."""

    def recursively_check_leaf_commands(ctx, command, leaf_commands):
        """Recursively return the leaf commands of the given command."""
        try:
            for subcommand in command.commands:
                # We need to fetch the subcommand through the ``get_command``, because that is what the ``verdi``
                # command does when a subcommand is invoked on the command line.
                recursively_check_leaf_commands(ctx, command.get_command(ctx, subcommand), leaf_commands)
        except AttributeError:
            # There are not subcommands so this is a leaf command, verify it has the verbosity option
            assert 'verbosity' in [p.name for p in command.params], f'`{command.name} does not have verbosity option'

    leaf_commands = []
    ctx = click.Context(cmd_verdi.verdi)
    recursively_check_leaf_commands(ctx, cmd_verdi.verdi, leaf_commands)
