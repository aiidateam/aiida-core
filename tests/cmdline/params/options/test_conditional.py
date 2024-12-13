###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.cmdline.params.options.conditional` module."""

import functools

import click
import pytest

from aiida.cmdline.params.options.conditional import ConditionalOption


@pytest.fixture
def run_cli_command(run_cli_command):
    """Override the ``run_cli_command`` fixture to always run with ``use_subprocess=False`` for tests in this module."""
    return functools.partial(run_cli_command, use_subprocess=False)


def construct_simple_cmd(pname, required_fn=lambda ctx: ctx.params.get('on'), **kwargs):
    """Return a command with two options.

    * an option created from the ``args`` and ``kwargs``
    * --opt, ``ConditionalOption`` with ``required_fn`` from ``kwargs``.
    """

    @click.command()
    @click.option(pname, **kwargs)
    @click.option('--opt', required_fn=required_fn, cls=ConditionalOption)
    def cmd(on, opt):
        """Dummy command for testing"""
        click.echo(opt)

    return cmd


@click.command()
@click.option('--a/--b', 'a_or_b')
@click.option('--opt-a', required_fn=lambda c: c.params.get('a_or_b'), cls=ConditionalOption)
@click.option('--opt-b', required_fn=lambda c: not c.params.get('a_or_b'), cls=ConditionalOption)
def command_multi_non_eager(a_or_b, opt_a, opt_b):
    """Return a command that has two scenarios.

    * flag a_or_b (--a/--b)
    * opt-a required if a_or_b is True
    * opt-b required if a_or_b  is False
    """
    click.echo(f'{opt_a} / {opt_b}')


def test_switch_off(run_cli_command):
    """scenario: switch --on/--off detrmines if option opt is required
    action: invoke with no options
    behaviour: flag is off by default -> command runs without complaining
    """
    cmd = construct_simple_cmd('--on/--off')
    run_cli_command(cmd, [])


def test_switch_on(run_cli_command):
    """scenario: switch --on/--off detrmines if option opt is required
    action: invoke with --on
    behaviour: fails with Missing option message
    """
    cmd = construct_simple_cmd('--on/--off')
    result = run_cli_command(cmd, ['--on'], raises=True)
    assert 'Error: Missing option' in result.output and '--opt' in result.output


def test_flag_off(run_cli_command):
    """scenario: flag "--on" detrmines if option opt is required
    action: invoke without options
    behaviour: command runs without complaining
    """
    cmd = construct_simple_cmd('--on', is_flag=True)
    run_cli_command(cmd, [])


def test_flag_on(run_cli_command):
    """scenario: flag "--on" detrmines if option opt is required
    action: invoke with --on
    behaviour: fails with Missing option message
    """
    cmd = construct_simple_cmd('--on', is_flag=True)
    result = run_cli_command(cmd, ['--on'], raises=True)
    assert 'Error: Missing option' in result.output and '--opt' in result.output


def test_aa(run_cli_command):
    """Scenario = a-or-b
    action: require a, give a (+ reversed order)
    behaviour: command runs
    """
    result = run_cli_command(command_multi_non_eager, ['--a', '--opt-a=Bla'])
    assert result.output == 'Bla / None\n'

    result = run_cli_command(command_multi_non_eager, ['--opt-a=Bla', '--a'])
    assert result.output == 'Bla / None\n'


def test_ab(run_cli_command):
    """Scenario = a-or-b
    action: require a, give b (+ reversed order)
    behaviour: fail, Missing option
    """
    result = run_cli_command(command_multi_non_eager, ['--a', '--opt-b=Bla'], raises=True)
    assert 'Error: Missing option' in result.output and '--opt-a' in result.output

    result = run_cli_command(command_multi_non_eager, ['--opt-b=Bla', '--a'], raises=True)
    assert 'Error: Missing option' in result.output and '--opt-a' in result.output


def test_ba(run_cli_command):
    """Scenario = a-or-b
    action: require b, give a (+ reversed order)
    behaviour: fail, Missing option
    """
    result = run_cli_command(command_multi_non_eager, ['--b', '--opt-a=Bla'], raises=True)
    assert 'Error: Missing option' in result.output and '--opt-b' in result.output

    result = run_cli_command(command_multi_non_eager, ['--opt-a=Bla', '--b'], raises=True)
    assert 'Error: Missing option' in result.output and '--opt-b' in result.output


def user_callback(_ctx, param, value):
    """Testing callback that transforms a missing value to -1 and otherwise only accepts 42."""
    if not value:
        return -1

    if value != 42:
        raise click.BadParameter('invalid integer', param=param)

    return value


def construct_command_flag_conditional(**kwargs):
    """Set up a command with a flag and a customizable option that depends on it."""

    @click.command()
    @click.option('--required', is_flag=True)
    @click.option('--opt-a', required_fn=lambda ctx: ctx.params.get('required'), cls=ConditionalOption, **kwargs)
    def cmd(required, opt_a):
        """A command with a flag and customizable options that depend on it."""
        click.echo(f'{opt_a}')

    return cmd


@pytest.mark.parametrize('options', ([], ['--required']))
def test_default(run_cli_command, options):
    """Test that the default still gets passed."""
    cmd = construct_command_flag_conditional(default='default')
    result = run_cli_command(cmd, options)
    assert result.output == 'default\n'


@pytest.mark.parametrize('options', ([], ['--required']))
def test_callback(run_cli_command, options):
    """Test that the callback still gets called."""
    cmd = construct_command_flag_conditional(default=23, type=int, callback=user_callback)
    run_cli_command(cmd, options, raises=True)


def test_prompt_callback(run_cli_command):
    """Test that the callback gets called on prompt results and will keep prompting until callback passes."""
    cmd = construct_command_flag_conditional(prompt='A', default=23, type=int, callback=user_callback)
    result = run_cli_command(cmd, user_input='\n42\n')
    assert 'A [23]: \n' in result.output
    assert 'invalid integer' in result.output

    result = run_cli_command(cmd, ['--required'], user_input='\n42\n')
    assert 'A [23]: \n' in result.output
    assert 'invalid integer' in result.output


def test_required(run_cli_command):
    """Test that required_fn overrides required if it evaluates to False."""
    cmd = construct_command_flag_conditional(required=True)
    run_cli_command(cmd)
    run_cli_command(cmd, ['--required'], raises=True)
