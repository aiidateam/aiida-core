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

import aiida
from aiida import get_version
from aiida.cmdline.commands import cmd_verdi
from aiida.manage.configuration import get_profile


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


@pytest.mark.parametrize('arguments', [['--help'], ['profile', '--help']])
def test_verdi_help_does_not_warn_about_development_version(
    monkeypatch, config_with_profile_factory, run_cli_command, arguments
):
    """Showing help does not require acknowledging development-version risks."""
    config = config_with_profile_factory(load=False)
    config.set_option('warnings.development_version', True)
    monkeypatch.setattr(aiida, '__version__', '3.0.0.dev0')

    result = run_cli_command(cmd_verdi.verdi, arguments, use_subprocess=False, initialize_ctx_obj=False)

    assert 'You are using a development version of AiiDA' not in result.output


def test_verdi_with_profile_loads_selected_profile(empty_config, profile_factory, run_cli_command):
    """Test ``verdi --profile`` loads the explicitly selected profile."""
    default_profile = profile_factory('default')
    explicit_profile = profile_factory('explicit')
    empty_config.add_profile(default_profile)
    empty_config.add_profile(explicit_profile)
    empty_config.set_default_profile(default_profile.name, overwrite=True)
    empty_config.store()

    result = run_cli_command(
        cmd_verdi.verdi,
        ['--profile', explicit_profile.name, '--help'],
        use_subprocess=False,
        initialize_ctx_obj=False,
    )

    assert get_profile().name == explicit_profile.name
    assert 'Usage: verdi [OPTIONS] COMMAND [ARGS]...' in result.output


def test_verdi_with_unknown_profile_fails(config_with_profile_factory, run_cli_command):
    """Test ``verdi --profile`` fails for a profile that does not exist."""
    config_with_profile_factory(load=False)

    result = run_cli_command(
        cmd_verdi.verdi,
        ['--profile', 'profile-does-not-exist', '--help'],
        use_subprocess=False,
        initialize_ctx_obj=False,
        raises=True,
    )

    assert result.exception is not None
    assert 'profile `profile-does-not-exist` does not exist' in str(result.exception)


def test_group_option_names_do_not_overlap_with_ancestors():
    """Test built-in `verdi` groups do not reuse ancestor option parameter names."""
    from aiida.tools.pytest_fixtures.cli import assert_verdi_group_option_names_do_not_overlap_with_ancestors

    assert_verdi_group_option_names_do_not_overlap_with_ancestors()


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


def test_quicksetup_command_removed(run_cli_command):
    """The old setup shortcut is no longer available from the CLI."""
    result = run_cli_command(cmd_verdi.verdi, ['quicksetup', '--help'], use_subprocess=False, raises=True)
    assert '`quicksetup` is not a verdi command' in result.output


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
