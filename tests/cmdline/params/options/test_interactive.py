###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the InteractiveOption."""

import functools

import click
import pytest

from aiida.cmdline.params.options import NON_INTERACTIVE
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.params.types.plugin import PluginParamType


@pytest.fixture
def run_cli_command(run_cli_command):
    """Override the ``run_cli_command`` fixture to always run with ``use_subprocess=False`` for tests in this module."""
    return functools.partial(run_cli_command, use_subprocess=False)


class Only42IntParamType(click.types.IntParamType):
    """Param type that only accepts 42 as valid value"""

    name = 'only42int'

    def convert(self, value, param, ctx):
        newval = super().convert(value, param, ctx)
        if newval != 42:
            self.fail('Type validation: invalid, should be 42')
        return newval

    def __repr__(self):
        return 'ONLY42INT'


def user_callback(_ctx, param, value):
    """A fake user callback ued for testing.

    :param _ctx: The click context
    :param param: The parameter name
    :param value: The parameter value
    :return: The validated parameter
    """
    if not value:
        return -1

    if value != 42:
        raise click.BadParameter('invalid', param=param)

    return value


def validate_positive_number(ctx, param, value):
    """Validate that the number passed to this parameter is a positive number.

    :param ctx: the `click.Context`
    :param param: the parameter
    :param value: the value passed for the parameter
    :raises `click.BadParameter`: if the value is not a positive number
    """
    if not isinstance(value, (int, float)) or value < 0:
        from click import BadParameter

        raise BadParameter(f'{value} is not a valid positive number')

    return value


def validate_positive_number_with_echo(ctx, param, value):
    """Validate that the number passed to this parameter is a positive number.
       Also echos a message to the terminal

    :param ctx: the `click.Context`
    :param param: the parameter
    :param value: the value passed for the parameter
    :raises `click.BadParameter`: if the value is not a positive number
    """
    click.echo(f'Validating {value}')
    if not isinstance(value, (int, float)) or value < 0:
        from click import BadParameter

        raise BadParameter(f'{value} is not a valid positive number')

    return value


def create_command(**kwargs):
    """Return a simple command with one InteractiveOption, kwargs get relayed to the option."""

    @click.command()
    @click.option('--opt', prompt='Opt', cls=InteractiveOption, **kwargs)
    @NON_INTERACTIVE()
    def cmd(opt, non_interactive):
        """Test command for InteractiveOption"""
        click.echo(str(opt))

    return cmd


@pytest.mark.parametrize(
    ('character', 'explicit', 'user_input', 'expected'),
    (
        ('!', True, None, '!'),  # When explicitly passing ``!`` it should simply be accepted
        ('!', False, None, 'None'),  # When passing ``!`` at the prompt, it should set ``None`` as the value
        ('?', True, None, '?'),  # When explicitly passing ``?`` it should simply be accepted
        ('?', False, '?\n100\n', '100'),  # When passing ``?`` at the prompt, it should print the help message
    ),
)
def test_special_characters(run_cli_command, character, explicit, user_input, expected):
    """Test the behavior of special characters."""
    help_string = 'This is the help string for the single option'
    cmd = create_command(help=help_string)

    if explicit:
        options = ['--opt', character]
        user_input = None
    else:
        options = []
        user_input = user_input or f'{character}\n'

    result = run_cli_command(cmd, options, user_input=user_input)
    assert result.output_lines[-1] == expected

    if character == '?':
        if explicit:
            assert help_string not in result.output
        else:
            assert help_string in result.output


@pytest.mark.parametrize(
    ('user_input', 'expected'),
    (
        ('!\n', 'None'),  # When explicitly passing ``!`` it should simply be accepted
        ('?\n100\n', '100'),  # When passing ``?`` at the prompt, it should print the help message
    ),
)
def test_special_characters_validation(run_cli_command, user_input, expected):
    """Test that the special characters do not get through to the validation of the parameter."""
    cmd = create_command(type=int)
    result = run_cli_command(cmd, [], user_input=user_input)
    assert result.output_lines[-1].strip() == expected


@pytest.mark.parametrize(
    ('options', 'user_input', 'expected'),
    (
        ([], '\n', 'default-value'),  # Simply entering at the prompt should return the default
        (
            ['--non-interactive'],
            None,
            'default-value',
        ),  # Specifying ``--non-interactive`` should not prompt and return default
        ([], 'custom-value', 'custom-value'),  # Specifying value at the prompt
        (['--opt', 'custom-value'], None, 'custom-value'),  # Specifying value explicitly on the command line
    ),
)
def test_default(run_cli_command, options, user_input, expected):
    """Test the behavior of defaults being specified for the interactive option."""
    cmd = create_command(default='default-value')
    result = run_cli_command(cmd, options, user_input=user_input)
    assert result.output_lines[-1].strip() == expected


def test_help_string(run_cli_command):
    """Test the help string of interactive options."""
    help_string = 'This is the help string for the single option'
    cmd = create_command(help=help_string)
    result = run_cli_command(cmd, ['--help'])
    assert help_string in result.output


def prompt_output(cli_input, converted=None):
    """Return expected output of simple_command, given a commandline cli_input string."""
    return f'Opt: {cli_input}\n{converted or cli_input}\n'


def test_callback_prompt_twice(run_cli_command):
    """scenario: using InteractiveOption with type=float and callback that tests for positive number
    behaviour: should fail everytime either type validation or callback validation fails
    """
    cmd = create_command(type=float, callback=validate_positive_number)
    result = run_cli_command(cmd, [], user_input='string\n-1\n-1\n1\n')
    assert 'is not a valid float.' in result.output_lines[3]
    assert 'is not a valid positive number' in result.output_lines[5]
    assert 'is not a valid positive number' in result.output_lines[7]
    assert '1.0' in result.output_lines[9]


def test_callback_prompt_only_once(run_cli_command):
    """scenario: using InteractiveOption with type=float and callback that echos an additional message
    behaviour: the callback should be called at most once per prompt
    """
    cmd = create_command(type=float, callback=validate_positive_number_with_echo)
    result = run_cli_command(cmd, [], user_input='string\n-1\n1\n')
    assert result.output_lines[3] == "Error: 'string' is not a valid float."
    assert result.output_lines[5] == 'Validating -1.0', result.output
    assert result.output_lines[6] == 'Error: -1.0 is not a valid positive number'
    assert result.output_lines[8] == 'Validating 1.0'
    assert result.output_lines[9] == '1.0'


def test_prompt_str(run_cli_command):
    """scenario: using InteractiveOption with type=str
    behaviour: giving no option prompts, accepts a string
    """
    cmd = create_command(type=str)
    result = run_cli_command(cmd, [], user_input='TEST\n')
    expected = 'Opt: TEST\nTEST\n'
    assert expected in result.output


def test_prompt_empty_input(run_cli_command):
    """scenario: using InteractiveOption with type=str and invoking without options
    behaviour: pressing enter on empty line at prompt repeats the prompt without a message
    """
    cmd = create_command(type=str)
    result = run_cli_command(cmd, [], user_input='\nTEST\n')
    expected = 'Opt: \nOpt: TEST\nTEST\n'
    assert expected in result.output


def test_prompt_help_default(run_cli_command):
    """scenario: using InteractiveOption with type=str and no help parameter and invoking without options
    behaviour: entering '?' leads to a default help message being printed and prompt repeated
    """
    cmd = create_command(type=str)
    result = run_cli_command(cmd, [], user_input='?\nTEST\n')
    assert 'Opt: ?\n' in result.output
    assert 'Expecting text\n' in result.output
    assert 'Opt: TEST\nTEST\n' in result.output


def test_prompt_help_custom(run_cli_command):
    """scenario: using InteractiveOption with type=str and help message and invoking without options
    behaviour: entering '?' leads to the given help message being printed and the prompt repeated
    """
    cmd = create_command(type=str, help='Please enter some text')
    result = run_cli_command(cmd, [], user_input='?\nTEST\n')
    assert 'Opt: ?\n' in result.output
    assert 'Please enter some text\n' in result.output
    assert 'Opt: TEST\nTEST\n' in result.output


def test_prompt_simple(run_cli_command):
    """scenario: using InteractiveOption with type=bool
    behaviour: giving no option prompts, accepts 'true'
    """
    cmd = create_command(type=bool, help='help msg')
    result = run_cli_command(cmd, [], user_input='\n?\ny\n')
    expected_1 = 'Opt: \nOpt: ?\nhelp msg\nOpt: y\nTrue'
    assert expected_1 in result.output


def test_prompt_simple_other_types(run_cli_command):
    """scenario: using InteractiveOption with type of int or float
    behaviour: giving no option prompts, accepts int or float
    """
    params = [(int, '98', '98'), (float, '3.14e-7', '3.14e-07')]
    for ptype, cli_input, output in params:
        cmd = create_command(type=ptype, help='help msg')
        result = run_cli_command(cmd, [], user_input=f'\n?\n{cli_input}\n')
        expected_1 = f'help msg\nOpt: {cli_input}\n{output}\n'
        assert expected_1 in result.output


@pytest.mark.parametrize('parameter_type', (click.File(), click.Path(exists=True)))
def test_prompt_complex(run_cli_command, parameter_type):
    """scenario: using InteractiveOption with type of file or path
    behaviour: giving no option prompts, file
    """
    cmd = create_command(type=parameter_type, help='help msg')
    result = run_cli_command(cmd, [], user_input=f'\n?\n{__file__}\n')
    expected_1 = 'Opt: \nOpt: ?\n'
    expected_2 = f'help msg\nOpt: {__file__}'
    assert expected_1 in result.output
    assert expected_2 in result.output


def test_default_value_prompt(run_cli_command):
    """scenario: using InteractiveOption with a default value, invoke without options
    behaviour: prompt, showing the default value, take default on empty cli_input.
    """
    returns = []
    cmd = create_command(default='default')
    result = run_cli_command(cmd, [], user_input='\n')
    returns.append(result)
    expected = 'Opt [default]: \ndefault\n'
    assert expected in result.output
    result = run_cli_command(cmd, [], user_input='TEST\n')
    returns.append(result)
    expected = 'Opt [default]: TEST\nTEST\n'
    assert expected in result.output


def test_default_value_empty_opt(run_cli_command):
    """scenario: InteractiveOption with default value, invoke with empty option (--opt=)
    behaviour: accept empty string as input
    """
    cmd = create_command(default='default')
    result = run_cli_command(cmd, ['--opt='])
    assert result.output == '\n'


def test_opt_given_valid(run_cli_command):
    """scenario: InteractiveOption, invoked with a valid value on the cmdline
    behaviour: accept valid value
    """
    cmd = create_command(type=int)
    result = run_cli_command(cmd, ['--opt=4'])
    expected = '4\n'
    assert result.output == expected


def test_opt_given_invalid(run_cli_command):
    """scenario: InteractiveOption, invoked with a valid value on the cmdline
    behaviour: accept valid value
    """
    cmd = create_command(type=int)
    result = run_cli_command(cmd, ['--opt=foo'], raises=True)
    assert 'Invalid value' in result.output


def test_non_interactive(run_cli_command):
    """scenario: InteractiveOption, invoked with only --non-interactive (and the option is required)
    behaviout: fail
    """
    cmd = create_command(required=True)
    result = run_cli_command(cmd, ['--non-interactive'], raises=True)
    assert 'Usage' in result.output
    assert 'Missing option' in result.output


def test_non_interactive_default(run_cli_command):
    """scenario: InteractiveOption, invoked with only --non-interactive
    behaviour: success
    """
    cmd = create_command(default='default')
    result = run_cli_command(cmd, ['--non-interactive'])
    assert result.output == 'default\n'


def test_after_callback_valid(run_cli_command):
    """scenario: InteractiveOption with a user callback
    action: invoke with valid value
    behaviour: user callback runs & succeeds
    """
    cmd = create_command(callback=user_callback, type=int)
    result = run_cli_command(cmd, ['--opt=42'])
    assert result.output == '42\n'


def test_after_callback_invalid(run_cli_command):
    """scenario: InteractiveOption with a user callback
    action: invoke with invalid value of right type
    behaviour: user callback runs & succeeds
    """
    cmd = create_command(callback=user_callback, type=int)
    result = run_cli_command(cmd, ['--opt=234234'], raises=True)
    assert 'Invalid value' in result.output


def test_after_callback_wrong_type(run_cli_command):
    """scenario: InteractiveOption with a user callback
    action: invoke with invalid value of wrong type
    behaviour: user callback does not run
    """
    cmd = create_command(callback=user_callback, type=int)
    result = run_cli_command(cmd, ['--opt=bla'], raises=True)
    assert 'Invalid value' in result.output
    assert 'bla' in result.output


def test_after_callback_empty(run_cli_command):
    """scenario: InteractiveOption with a user callback
    action: invoke with invalid value of wrong type
    behaviour: user callback does not run
    """
    cmd = create_command(callback=user_callback, type=int)
    result = run_cli_command(cmd, ['--opt='], raises=True)
    assert 'Invalid value' in result.output
    assert 'empty' not in result.output


def test_after_validation_interactive(run_cli_command):
    """Test that the type validation gets called on values entered at a prompt.

    Scenario:
        * InteractiveOption with custom type and prompt set
        * invoked without passing the options
        * on prompt: first enter an invalid value, then a valid one

    Behaviour:
        * Prompt for the value
        * reject invalid value, prompt again
        * accept valid value
    """
    cmd = create_command(callback=user_callback, type=Only42IntParamType())
    result = run_cli_command(cmd, [], user_input='23\n42\n')
    assert 'Opt: 23\n' in result.output
    assert 'Type validation: invalid' in result.output
    assert 'Opt: 42\n42\n' in result.output


def test_after_callback_default_noninteractive(run_cli_command):
    """Test that the callback gets called on the default, in line with click 6 behaviour.

    Scenario:
        * InteractiveOption with user callback and invalid default
        * invoke with no options and --non-interactive

    Behaviour:
        * the default value gets passed through the callback and rejected
    """
    cmd = create_command(callback=user_callback, type=int, default=23)
    result = run_cli_command(cmd, ['--non-interactive'], raises=True)
    assert 'invalid' in result.output


def test_default_empty_empty_cli(run_cli_command):
    """Test that default="" allows to pass an empty cli option."""
    cmd = create_command(default='', type=str)
    result = run_cli_command(cmd, ['--opt='])
    assert result.output == '\n'


def test_default_empty_prompt(run_cli_command):
    """Test that default="" allows to pass an empty cli option."""
    cmd = create_command(default='', type=str)
    result = run_cli_command(cmd, user_input='\n')
    expected = 'Opt []: \n\n'
    assert expected in result.output


def test_not_required_noninteractive(run_cli_command):
    cmd = create_command(required=False)
    result = run_cli_command(cmd, ['--non-interactive'])
    # I strip, there is typically a \n at the end
    assert result.output == 'None\n'


def test_not_required_interactive(run_cli_command):
    cmd = create_command(required=False)
    result = run_cli_command(cmd, user_input='value\n')
    expected = 'Opt: value\nvalue\n'
    assert expected in result.output


def test_not_required_noninteractive_default(run_cli_command):
    cmd = create_command(required=False, default='')
    result = run_cli_command(cmd, ['--non-interactive'])
    assert result.output == '\n'


def test_not_required_interactive_default(run_cli_command):
    cmd = create_command(required=False, default='')
    result = run_cli_command(cmd, user_input='\nnot needed\n')
    expected = 'Opt []: \n\n'
    assert expected in result.output


def test_interactive_ignore_default_not_required_option(run_cli_command):
    """Test that if an option is not required ``!`` is accepted and is translated to ``None``."""
    cmd = create_command(required=False)
    result = run_cli_command(cmd, user_input='!\n')
    expected = 'Opt: !\nNone\n'
    assert expected in result.output


def test_interactive_ignore_default_required_option(run_cli_command):
    """Test that if an option is required, ``!`` is translated to ``None`` and so is not accepted."""
    cmd = create_command(required=True)
    result = run_cli_command(cmd, user_input='!\nvalue\n')
    expected = 'Opt: !\nError: Opt has to be specified\nOpt: value\nvalue\n'
    assert expected in result.output


def test_get_help_message():
    """Test the :meth:`aiida.cmdline.params.options.interactive.InteractiveOption.get_help_message`."""
    option = InteractiveOption('-s', type=click.STRING)
    message = option.get_help_message()
    assert message == 'Expecting text'

    option = InteractiveOption('-P', type=PluginParamType(group='aiida.groups'))
    message = option.get_help_message()
    assert 'Expecting plugin' in message
    assert 'Select one of:' in message
    assert 'core' in message
    assert 'core.auto' in message
