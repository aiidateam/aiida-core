"""Unit tests for the InteractiveOption."""
import unittest

import click
from click.testing import CliRunner

from aiida.cmdline.params.options.types.interactive import InteractiveOption


class InteractiveOptionTest(unittest.TestCase):
    """Unit tests for InteractiveOption."""

    def simple_command(self, **kwargs):
        """Return a simple command with one InteractiveOption, kwargs get relayed to the option."""

        @click.command()
        @click.option('--opt', prompt='Opt', cls=InteractiveOption, **kwargs)
        @click.option('--non-interactive', is_flag=True)
        def cmd(opt, non_interactive):
            """test command for InteractiveOption"""
            click.echo(str(opt))

        return cmd

    def prompt_output(self, cli_input, converted=None):
        """Return expected output of simple_command, given a commandline cli_input string."""
        return "Opt: {}\n{}\n".format(cli_input, converted or cli_input)

    def test_prompt_str(self):
        """
        scenario: using InteractiveOption with type=str
        behaviour: giving no option prompts, accepts a string
        """
        cmd = self.simple_command(type=str)
        runner = CliRunner()
        result = runner.invoke(cmd, [], input='TEST\n')
        expected = self.prompt_output('TEST')
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, expected)

    def test_prompt_empty_input(self):
        """
        scenario: using InteractiveOption with type=str and invoking without options
        behaviour: pressing enter on empty line at prompt repeats the prompt without a message
        """
        cmd = self.simple_command(type=str)
        runner = CliRunner()
        result = runner.invoke(cmd, [], input='\nTEST\n')
        expected = "Opt: \nOpt: TEST\nTEST\n"
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, expected)

    def test_prompt_help_default(self):
        """
        scenario: using InteractiveOption with type=str and no help parameter and invoking without options
        behaviour: entering '?' leads to a default help message being printed and prompt repeated
        """
        cmd = self.simple_command(type=str)
        runner = CliRunner()
        result = runner.invoke(cmd, [], input='?\nTEST\n')
        expected = "Opt: ?\n\tExpecting text\nOpt: TEST\nTEST\n"
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, expected)

    def test_prompt_help_custom(self):
        """
        scenario: using InteractiveOption with type=str and help message and invoking without options
        behaviour: entering '?' leads to the given help message being printed and the prompt repeated
        """
        cmd = self.simple_command(type=str, help='Please enter some text')
        runner = CliRunner()
        result = runner.invoke(cmd, [], input='?\nTEST\n')
        expected = "Opt: ?\n\tPlease enter some text\nOpt: TEST\nTEST\n"
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, expected)

    def test_prompt_simple(self):
        """
        scenario: using InteractiveOption with type=bool
        behaviour: giving no option prompts, accepts 'true'
        """
        params = [(bool, 'true', 'True'), (int, '98', '98'), (float, '3.14e-7', '3.14e-07')]
        for ptype, cli_input, output in params:
            cmd = self.simple_command(type=ptype, help='help msg')
            runner = CliRunner()
            result = runner.invoke(cmd, [], input='\n?\n{}\n'.format(cli_input))
            expected = 'Opt: \nOpt: ?\n\thelp msg\n'
            expected += self.prompt_output(cli_input, output)
            self.assertIsNone(result.exception)
            self.assertEqual(result.output, expected)

    def strip_line(self, text):
        """returns text without the last line"""
        return text.rsplit('\n')[0]

    def test_prompt_complex(self):
        """
        scenario: using InteractiveOption with type=float
        behaviour: giving no option prompts, accepts 3.14e-7
        """
        params = [(click.File(), __file__), (click.Path(exists=True), __file__)]
        for ptype, cli_input in params:
            cmd = self.simple_command(type=ptype, help='help msg')
            runner = CliRunner()
            result = runner.invoke(cmd, [], input='\n?\n{}\n'.format(cli_input))
            expected_beginning = 'Opt: \nOpt: ?\n\thelp msg\n'
            expected_beginning += self.strip_line(self.prompt_output(cli_input))
            self.assertIsNone(result.exception)
            self.assertTrue(result.output.startswith(expected_beginning))

    def test_default_value_prompt(self):
        """
        scenario: using InteractiveOption with a default value, invoke without options
        behaviour: prompt, showing the default value, take default on empty cli_input.
        """
        returns = []
        cmd = self.simple_command(default='default')
        runner = CliRunner()
        result = runner.invoke(cmd, [], input='\n')
        returns.append(result)
        expected = 'Opt [default]: \ndefault\n'
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, expected)
        result = runner.invoke(cmd, [], input='TEST\n')
        returns.append(result)
        expected = 'Opt [default]: TEST\nTEST\n'
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, expected)
        return returns

    def test_default_value_empty_opt(self):
        """
        scenario: InteractiveOption with default value, invoke with empty option (--opt=)
        behaviour: accept empty string as input
        """
        cmd = self.simple_command(default='default')
        runner = CliRunner()
        result = runner.invoke(cmd, ['--opt='])
        expected = '\n'
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, expected)

    def test_opt_given_valid(self):
        """
        scenario: InteractiveOption, invoked with a valid value on the cmdline
        behaviour: accept valid value
        """
        cmd = self.simple_command(type=int)
        runner = CliRunner()
        result = runner.invoke(cmd, ['--opt=4'])
        expected = '4\n'
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, expected)

    def test_opt_given_invalid(self):
        """
        scenario: InteractiveOption, invoked with a valid value on the cmdline
        behaviour: accept valid value
        """
        cmd = self.simple_command(type=int)
        runner = CliRunner()
        result = runner.invoke(cmd, ['--opt=foo'])
        self.assertIsNotNone(result.exception)
        self.assertIn('Invalid value', result.output)

    def test_non_interactive(self):
        """
        scenario: InteractiveOption, invoked with only --non-interactive
        behaviout: fail
        """
        cmd = self.simple_command()
        runner = CliRunner()
        result = runner.invoke(cmd, ['--non-interactive'])
        self.assertIsNotNone(result.exception)
        self.assertIn('Usage: ', result.output)
        self.assertIn('Missing option', result.output)

    def test_non_interactive_default(self):
        """
        scenario: InteractiveOption, invoked with only --non-interactive
        behaviour: fail
        """
        cmd = self.simple_command(default='default')
        runner = CliRunner()
        result = runner.invoke(cmd, ['--non-interactive'])
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, 'default\n')

    def user_callback(self, ctx, param, value):
        if not value:
            return -1
        elif value != 42:
            raise click.BadParameter('invalid', param=param)
        else:
            return value

    def test_after_callback_valid(self):
        """
        scenario: InteractiveOption with a user callback
        action: invoke with valid value
        behaviour: user callback runs & succeeds
        """
        cmd = self.simple_command(callback=self.user_callback, type=int)
        runner = CliRunner()
        result = runner.invoke(cmd, ['--opt=42'])
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, '42\n')

    def test_after_callback_invalid(self):
        """
        scenario: InteractiveOption with a user callback
        action: invoke with invalid value of right type
        behaviour: user callback runs & succeeds
        """
        cmd = self.simple_command(callback=self.user_callback, type=int)
        runner = CliRunner()
        result = runner.invoke(cmd, ['--opt=234234'])
        self.assertIsNotNone(result.exception)
        self.assertIn('Invalid value', result.output)
        self.assertIn('invalid', result.output)

    def test_after_callback_wrong_typ(self):
        """
        scenario: InteractiveOption with a user callback
        action: invoke with invalid value of wrong type
        behaviour: user callback does not run
        """
        cmd = self.simple_command(callback=self.user_callback, type=int)
        runner = CliRunner()
        result = runner.invoke(cmd, ['--opt=bla'])
        self.assertIsNotNone(result.exception)
        self.assertIn('Invalid value', result.output)
        self.assertIn('bla', result.output)

    def test_after_callback_empty(self):
        """
        scenario: InteractiveOption with a user callback
        action: invoke with invalid value of wrong type
        behaviour: user callback does not run
        """
        cmd = self.simple_command(callback=self.user_callback, type=int)
        runner = CliRunner()
        result = runner.invoke(cmd, ['--opt='])
        self.assertIsNotNone(result.exception)
        self.assertIn('Invalid value', result.output)
        self.assertNotIn('empty', result.output)
