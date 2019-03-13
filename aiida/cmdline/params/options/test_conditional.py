# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the ConditionalOption."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import unittest

import click
from click.testing import CliRunner

from .conditional import ConditionalOption


class ConditionalOptionTest(unittest.TestCase):
    """Unit tests for ConditionalOption."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()

    def simple_cmd(self, pname, required_fn=lambda ctx: ctx.params.get('on'), **kwargs):
        """
        returns a command with two options:

            * an option created from the args and kwargs
            * --opt, ConditionalOption with required_fn from kwargs
        """

        # pylint: disable=no-self-use

        @click.command()
        @click.option(pname, **kwargs)
        @click.option('--opt', required_fn=required_fn, cls=ConditionalOption)
        def cmd(on, opt):
            """dummy command for testing"""
            # pylint: disable=unused-argument, invalid-name

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

        # pylint: disable=no-self-use

        @click.command()
        @click.option('--a/--b', 'a_or_b')
        @click.option('--opt-a', required_fn=lambda c: c.params.get('a_or_b'), cls=ConditionalOption)
        @click.option('--opt-b', required_fn=lambda c: not c.params.get('a_or_b'), cls=ConditionalOption)
        def cmd(a_or_b, opt_a, opt_b):
            """test command for scenario a-or-b"""
            # pylint: disable=unused-argument

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

    @staticmethod
    def user_callback(_ctx, param, value):
        """
        Testing callback that does not accept 42 and transforms a missing value to -1
        """
        if not value:
            return -1

        if value != 42:
            raise click.BadParameter('invalid', param=param)

        return value

    @staticmethod
    def setup_flag_cond(**kwargs):
        """Set up a command with a flag and a customizable option that depends on it."""

        @click.command()
        @click.option('--flag', is_flag=True)
        @click.option('--opt-a', required_fn=lambda c: c.params.get('flag'), cls=ConditionalOption, **kwargs)
        def cmd(flag, opt_a):
            """ A command with a flag and customizable options that dependon it """
            # pylint: disable=unused-argument

            click.echo('{}'.format(opt_a))

        return cmd

    def test_default(self):
        """Test that the default still gets passed."""
        cmd = self.setup_flag_cond(default='default')
        result_noflag = self.runner.invoke(cmd)
        self.assertIsNone(result_noflag.exception)
        self.assertEqual('default\n', result_noflag.output)

        result_flag = self.runner.invoke(cmd, ['--flag'])
        self.assertIsNone(result_flag.exception)
        self.assertEqual('default\n', result_flag.output)

    def test_callback(self):
        """Test that the callback still gets called."""
        cmd = self.setup_flag_cond(default=23, type=int, callback=self.user_callback)
        result_noflag = self.runner.invoke(cmd)
        self.assertIsNotNone(result_noflag.exception)

        result_flag = self.runner.invoke(cmd, ['--flag'])
        self.assertIsNotNone(result_flag.exception)

    def test_prompt_callback(self):
        """Test that the callback gets called on prompt results."""
        cmd = self.setup_flag_cond(prompt='A', default=23, type=int, callback=self.user_callback)
        result_noflag = self.runner.invoke(cmd, input='\n')
        self.assertIsNotNone(result_noflag.exception)
        self.assertIn('A [23]: \n', result_noflag.output)
        self.assertIn('Invalid', result_noflag.output)

        result_flag = self.runner.invoke(cmd, ['--flag'], input='\n')
        self.assertIsNotNone(result_flag.exception)
        self.assertIn('A [23]: \n', result_flag.output)
        self.assertIn('Invalid', result_flag.output)

    def test_required(self):
        """Test that required_fn overrides required if it evaluates to False."""
        cmd = self.setup_flag_cond(required=True)
        result_noflag = self.runner.invoke(cmd)
        self.assertIsNone(result_noflag.exception)
        result_flag = self.runner.invoke(cmd, ['--flag'])
        self.assertIsNotNone(result_flag.exception)
