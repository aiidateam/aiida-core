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
import io
import textwrap

import click
import pytest

from aiida.cmdline.params.options import CONFIG_FILE
from aiida.cmdline.params.options.config import configuration_callback, yaml_config_file_provider


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


@pytest.mark.parametrize(
    'contents, error',
    [
        ('unknown: 1', click.BadParameter),
        ('invalid: [', click.BadOptionUsage),
    ],
)
def test_config_handle_closed_on_callback_error(contents, error, tmp_path):
    """Release the Click-owned config handle when reading or validating it fails."""
    path = tmp_path / 'config.yml'
    path.write_text(contents)
    context = click.Context(cmd)
    param = next(param for param in cmd.params if param.name == 'config')
    handle = param.type.convert(str(path), param, context)

    with pytest.raises(error):
        configuration_callback(
            None, '--config', 'config', None, yaml_config_file_provider, False, context, param, handle
        )

    assert handle.closed


def test_config_url_closed_on_callback_error(monkeypatch):
    """Register URL responses for the same Click context cleanup as local files."""
    response = io.BytesIO(b'unknown: 1')
    monkeypatch.setattr('aiida.cmdline.params.types.path.convert_possible_url', lambda value, timeout: response)
    context = click.Context(cmd)
    param = next(param for param in cmd.params if param.name == 'config')
    handle = param.type.convert('https://example.invalid/config.yml', param, context)

    with pytest.raises(click.BadParameter):
        configuration_callback(
            None, '--config', 'config', None, yaml_config_file_provider, False, context, param, handle
        )

    assert response.closed


def test_config_handle_left_open_for_saved_callback(tmp_path):
    """Click still owns the handle after a successful config callback."""
    path = tmp_path / 'config.yml'
    path.write_text('integer: 1')
    context = click.Context(cmd)
    param = next(param for param in cmd.params if param.name == 'config')
    handle = param.type.convert(str(path), param, context)

    def saved_callback(ctx, option, value):
        assert not value.closed
        return value

    result = configuration_callback(
        None, '--config', 'config', saved_callback, yaml_config_file_provider, False, context, param, handle
    )
    assert result is handle
    assert not handle.closed
    context.close()
    assert handle.closed


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


def test_invalid_unknown_keys(run_cli_command, tmp_path):
    """Test the option for a configuration file containing unknown keys."""
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
