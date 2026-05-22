###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the :class:`aiida.cmdline.params.options.config.ConfigOption`."""

import functools
import textwrap

import click
import pytest

from aiida.cmdline.params.options import CONFIG_FILE, TEMPLATE_VARS


@pytest.fixture
def run_cli_command(run_cli_command):
    """Override the ``run_cli_command`` fixture to always run with ``use_subprocess=False`` for tests in this module."""
    return functools.partial(run_cli_command, use_subprocess=False)


@click.command()
@click.option('--integer', type=int)
@click.option('--boolean', type=bool)
@CONFIG_FILE()
def cmd(integer, boolean):
    """Test command for :class:`aiida.cmdline.params.options.config.ConfigOption`."""
    click.echo(f'Integer: {integer}')
    click.echo(f'Boolean: {boolean}')


@click.command()
@click.option('--label', type=str)
@click.option('--hostname', type=str)
@TEMPLATE_VARS()
@CONFIG_FILE()
def cmd_with_template(label, hostname):
    """Test command that supports template-aware config files."""
    click.echo(f'Label: {label}')
    click.echo(f'Hostname: {hostname}')


def test_valid(run_cli_command, tmp_path):
    """Test the option for a valid configuration file."""
    filepath = tmp_path / 'config.yml'
    filepath.write_text(
        textwrap.dedent(
            """
            integer: 1
            boolean: false
            """
        )
    )

    result = run_cli_command(cmd, ['--config', str(filepath)])
    assert 'Integer: 1' in result.output_lines[0]
    assert 'Boolean: False' in result.output_lines[1]


@pytest.mark.filterwarnings('ignore')
def test_invalid_unknown_keys(run_cli_command, tmp_path):
    """Test the option for an invalid configuration file containing unknown keys.

    The test emits a ``ResourceWarning`` because the config file is not closed since the command errors, but this is
    just a side-effect of how the test is run and doesn't apply to the real CLI command invocation.
    """
    filepath = tmp_path / 'config.yml'
    filepath.write_text(
        textwrap.dedent(
            """
            integer: 1
            unknown: 2.0
            """
        )
    )

    result = run_cli_command(cmd, ['--config', str(filepath)], raises=True)
    assert "Error: Invalid value for '--config': Invalid configuration file" in result.stderr
    assert "the following keys are not supported: {'unknown'}" in result.stderr


@pytest.mark.parametrize(
    'template_vars_arg',
    [
        '{"label": "my-computer"}',
        pytest.param('vars_file', id='yaml_file'),
    ],
)
def test_template_config_with_template_vars(run_cli_command, tmp_path, template_vars_arg):
    """Test that a templated config file is resolved via ``--template-vars`` (JSON or file)."""
    filepath = tmp_path / 'config.yml'
    filepath.write_text(
        textwrap.dedent(
            """\
            label: '{{ label }}'
            hostname: localhost
            metadata:
                template_variables:
                    label:
                        default: test
                        description: A label
            """
        )
    )

    if template_vars_arg == 'vars_file':
        vars_file = tmp_path / 'vars.yaml'
        vars_file.write_text('label: my-computer\n')
        template_vars_arg = str(vars_file)

    for args in [
        ['--template-vars', template_vars_arg, '--config', str(filepath)],
        ['--config', str(filepath), '--template-vars', template_vars_arg],
    ]:
        result = run_cli_command(cmd_with_template, args)
        assert 'Label: my-computer' in result.output
        assert 'Hostname: localhost' in result.output
