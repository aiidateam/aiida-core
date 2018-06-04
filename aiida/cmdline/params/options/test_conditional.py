"""Unit tests for the ConditionalOption."""
import unittest

import click
from click.testing import CliRunner

from aiida.cmdline.params.options.conditional import ConditionalOption


class ConditionalOptionTest(unittest.TestCase):
    """Unit tests for ConditionalOption."""

    def simple_cmd(self, pname, required_fn=lambda ctx: ctx.params.get('on'), **kwargs):
        """
        returns a command with two options:

            * an option created from the args and kwargs
            * --opt, ConditionalOption with required_fn from kwargs
        """

        @click.command()
        @click.option(pname, **kwargs)
        @click.option('--opt', required_fn=required_fn, cls=ConditionalOption)
        def cmd(on, opt):
            """dummy command for testing"""
            click.echo(opt)

        return cmd

    def test_switch_off(self):
        """
        scenario: switch --on/--off detrmines if option opt is required
        action: invoke with no options
        behaviour: flag is off by default -> command runs without complaining
        """

        cmd = self.simple_cmd('--on/--off')
        runner = CliRunner()
        result = runner.invoke(cmd, [])
        self.assertIsNone(result.exception)

    def test_switch_on(self):
        """
        scenario: switch --on/--off detrmines if option opt is required
        action: invoke with --on
        behaviour: fails with Missin option message
        """
        cmd = self.simple_cmd('--on/--off')
        runner = CliRunner()
        result = runner.invoke(cmd, ['--on'])
        self.assertIsNotNone(result.exception)
        self.assertIn('Error: Missing option "--opt".', result.output)

    def test_flag_off(self):
        """
        scenario: flag "--on" detrmines if option opt is required
        action: invoke without options
        behaviour: command runs without complaining
        """
        cmd = self.simple_cmd('--on', is_flag=True)
        runner = CliRunner()
        result = runner.invoke(cmd, [])
        self.assertIsNone(result.exception)

    def test_flag_on(self):
        """
        scenario: flag "--on" detrmines if option opt is required
        action: invoke with --on
        behaviour: fails with Missing option message
        """
        cmd = self.simple_cmd('--on', is_flag=True)
        runner = CliRunner()
        result = runner.invoke(cmd, ['--on'])
        self.assertIsNotNone(result.exception)
        self.assertIn('Error: Missing option "--opt".', result.output)

    def setup_multi_non_eager(self):
        """
        scenario a-or-b:

            * flag a_or_b (--a/--b)
            * opt-a required if a_or_b == True
            * opt-b required if a_or_b == False
        """

        @click.command()
        @click.option('--a/--b', 'a_or_b')
        @click.option('--opt-a', required_fn=lambda c: c.params.get('a_or_b'), cls=ConditionalOption)
        @click.option('--opt-b', required_fn=lambda c: not c.params.get('a_or_b'), cls=ConditionalOption)
        def cmd(a_or_b, opt_a, opt_b):
            """test command for scenario a-or-b"""
            click.echo('{} / {}'.format(opt_a, opt_b))

        runner = CliRunner()
        return runner, cmd

    def test_aa(self):
        """
        scenario = a-or-b
        action: require a, give a (+ reversed order)
        behaviour: command runs
        """
        runner, cmd = self.setup_multi_non_eager()
        result = runner.invoke(cmd, ['--a', '--opt-a=Bla'])
        self.assertIsNone(result.exception)
        self.assertEqual(result.output, 'Bla / None\n')

        result_rev = runner.invoke(cmd, ['--opt-a=Bla', '--a'])
        self.assertIsNone(result_rev.exception)
        self.assertEqual(result_rev.output, 'Bla / None\n')

    def test_ab(self):
        """
        scenario = a-or-b
        action: require a, give b (+ reversed order)
        behaviour: fail, Missing option
        """
        runner, cmd = self.setup_multi_non_eager()
        result = runner.invoke(cmd, ['--a', '--opt-b=Bla'])
        self.assertIsNotNone(result.exception)
        self.assertIn('Error: Missing option "--opt-a".', result.output)

        result_rev = runner.invoke(cmd, ['--opt-b=Bla', '--a'])
        self.assertIsNotNone(result_rev.exception)
        self.assertIn('Error: Missing option "--opt-a".', result_rev.output)

    def test_ba(self):
        """
        scenario = a-or-b
        action: require b, give a (+ reversed order)
        behaviour: fail, Missing option
        """
        runner, cmd = self.setup_multi_non_eager()
        result = runner.invoke(cmd, ['--b', '--opt-a=Bla'])
        self.assertIsNotNone(result.exception)
        self.assertIn('Error: Missing option "--opt-b".', result.output)

        result_rev = runner.invoke(cmd, ['--opt-a=Bla', '--b'])
        self.assertIsNotNone(result_rev.exception)
        self.assertIn('Error: Missing option "--opt-b".', result_rev.output)
