# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Unit tests for the :class:`aiida.cmdline.params.options.config.ConfigOption`."""
import functools
import tempfile
import textwrap

import click
import pytest

from aiida.cmdline.params.options import CONFIG_FILE


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


def test_valid(run_cli_command):
    """Test the option for a valid configuration file."""
    with tempfile.NamedTemporaryFile('w+') as handle:
        handle.write(textwrap.dedent("""
            integer: 1
            boolean: false
        """))
        handle.flush()

        result = run_cli_command(cmd, ['--config', handle.name])
        assert 'Integer: 1' in result.output_lines[0]
        assert 'Boolean: False' in result.output_lines[1]


def test_invalid_unknown_keys(run_cli_command):
    """Test the option for an invalid configuration file containing unknown keys."""
    with tempfile.NamedTemporaryFile('w+') as handle:
        handle.write(textwrap.dedent("""
            integer: 1
            unknown: 2.0
        """))
        handle.flush()

        result = run_cli_command(cmd, ['--config', handle.name], raises=True)
        assert "Error: Invalid value for '--config': Invalid configuration file" in result.stderr
        assert "the following keys are not supported: {'unknown'}" in result.stderr
