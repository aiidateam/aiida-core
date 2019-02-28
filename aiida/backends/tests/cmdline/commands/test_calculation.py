# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=protected-access,too-many-locals,invalid-name,too-many-public-methods
"""Tests for `verdi calculation`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import unittest

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_calculation as command
from aiida.common.datastructures import CalcJobState
from aiida.plugins.entry_point import get_entry_point_string_from_class


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiCalculation(AiidaTestCase):
    """Tests for `verdi calculation`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiCalculation, cls).setUpClass(*args, **kwargs)
        from aiida.backends.tests.utils.fixtures import import_archive_fixture
        from aiida.common.links import LinkType
        from aiida.engine import ProcessState
        from aiida.orm import Data, CalcJobNode, Dict
        from aiida.plugins import CalculationFactory
        from aiida import orm

        cls.computer = orm.Computer(
            name='comp',
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida').store()

        cls.code = orm.Code(remote_computer_exec=(cls.computer, '/bin/true')).store()
        cls.group = orm.Group(label='test_group').store()
        cls.node = Data().store()
        cls.calcs = []

        user = orm.User.objects.get_default()
        authinfo = orm.AuthInfo(computer=cls.computer, user=user)
        authinfo.store()

        process_class = CalculationFactory('templatereplacer')
        process_type = get_entry_point_string_from_class(process_class.__module__, process_class.__name__)

        # Create 5 CalcJobNodes (one for each CalculationState)
        for calculation_state in CalcJobState:

            calc = CalcJobNode(computer=cls.computer, process_type=process_type)
            calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
            calc.store()

            calc.set_process_state(ProcessState.RUNNING)
            cls.calcs.append(calc)

            if calculation_state == CalcJobState.PARSING:
                cls.KEY_ONE = 'key_one'
                cls.KEY_TWO = 'key_two'
                cls.VAL_ONE = 'val_one'
                cls.VAL_TWO = 'val_two'

                output_parameters = Dict(dict={
                    cls.KEY_ONE: cls.VAL_ONE,
                    cls.KEY_TWO: cls.VAL_TWO,
                }).store()

                output_parameters.add_incoming(calc, LinkType.CREATE, 'output_parameters')

                # Create shortcut for easy dereferencing
                cls.result_job = calc

                # Add a single calc to a group
                cls.group.add_nodes([calc])

        # Create a single failed CalcJobNode
        cls.EXIT_STATUS = 100
        calc = CalcJobNode(computer=cls.computer)
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc.store()
        calc.set_exit_status(cls.EXIT_STATUS)
        calc.set_process_state(ProcessState.FINISHED)
        cls.calcs.append(calc)

        # Uncomment when issue 2342 is addressed
        # # Load the fixture containing a single ArithmeticAddCalculation node
        # import_archive_fixture('calcjob/arithmetic.add.aiida')

        # # Get the imported ArithmeticAddCalculation node
        # ArithmeticAddCalculation = CalculationFactory('arithmetic.add')
        # calculations = orm.QueryBuilder().append(ArithmeticAddCalculation).all()[0]
        # cls.arithmetic_job = calculations[0]

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_calculation_res(self):
        """Test verdi calculation res"""
        options = [str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calculation_res, options)
        self.assertClickResultNoException(result)
        self.assertIn(self.KEY_ONE, result.output)
        self.assertIn(self.VAL_ONE, result.output)
        self.assertIn(self.KEY_TWO, result.output)
        self.assertIn(self.VAL_TWO, result.output)

        for flag in ['-k', '--keys']:
            options = [flag, self.KEY_ONE, '--', str(self.result_job.uuid)]
            result = self.cli_runner.invoke(command.calculation_res, options)
            self.assertClickResultNoException(result)
            self.assertIn(self.KEY_ONE, result.output)
            self.assertIn(self.VAL_ONE, result.output)
            self.assertNotIn(self.KEY_TWO, result.output)
            self.assertNotIn(self.VAL_TWO, result.output)

    def test_calculation_list_identifiers(self):
        """Test verdi calculation list with specific identifiers"""
        options = ['-r', '--project', 'pk', '--'] + [str(calc.pk) for calc in self.calcs[:2]]
        result = self.cli_runner.invoke(command.calculation_list, options)
        self.assertClickResultNoException(result)

        valid_pks = [calc.pk for calc in self.calcs]
        for line in get_result_lines(result):
            self.assertIn(int(line), valid_pks)

    def test_calculation_list_all_user(self):
        """Test verdi calculation list with the all users option"""
        for flag in ['-A', '--all-users']:
            options = ['-r', '-a', flag]
            result = self.cli_runner.invoke(command.calculation_list, options)
            self.assertClickResultNoException(result)
            self.assertEqual(len(get_result_lines(result)), 6)

    def test_calculation_list_all(self):
        """Test verdi calculation list with the all option"""

        # Without the flag I should only get the "active" states, which should be five
        options = ['-r']
        result = self.cli_runner.invoke(command.calculation_list, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 5, result.output)

        for flag in ['-a', '--all']:
            options = ['-r', flag]
            result = self.cli_runner.invoke(command.calculation_list, options)
            self.assertClickResultNoException(result)
            self.assertEqual(len(get_result_lines(result)), 6, result.output)

    def test_calculation_list_limit(self):
        """Test verdi calculation list with the limit option"""
        for flag in ['-l', '--limit']:
            limit = 1
            options = ['-r', flag, limit]
            result = self.cli_runner.invoke(command.calculation_list, options)
            self.assertClickResultNoException(result)
            self.assertEqual(len(get_result_lines(result)), limit)

    def test_calculation_list_project(self):
        """Test verdi calculation list with the project option"""
        for flag in ['-P', '--project']:
            options = ['-r', flag, 'pk']
            result = self.cli_runner.invoke(command.calculation_list, options)
            self.assertClickResultNoException(result)

            valid_pks = [calc.pk for calc in self.calcs]
            for line in get_result_lines(result):
                self.assertIn(int(line), valid_pks)

    def test_calculation_list_process_state(self):
        """Test verdi calculation list with the process state filter"""
        for flag in ['-S', '--process-state']:
            for state in ['finished', 'running']:

                options = ['-r', flag, state]
                result = self.cli_runner.invoke(command.calculation_list, options)

                self.assertClickResultNoException(result)

                if state == 'finished':
                    self.assertEqual(len(get_result_lines(result)), 1, result.output)
                else:
                    self.assertEqual(len(get_result_lines(result)), 5, result.output)

    def test_calculation_list_failed(self):
        """Test verdi calculation list with the failed filter"""
        for flag in ['-X', '--failed']:
            options = ['-r', flag]
            result = self.cli_runner.invoke(command.calculation_list, options)

            self.assertClickResultNoException(result)
            self.assertEqual(len(get_result_lines(result)), 1, result.output)

    def test_calculation_list_exit_status(self):
        """Test verdi calculation list with the exit status filter"""
        for flag in ['-E', '--exit-status']:
            for exit_status in [self.EXIT_STATUS]:
                options = ['-r', flag, exit_status]
                result = self.cli_runner.invoke(command.calculation_list, options)

                self.assertClickResultNoException(result)
                self.assertEqual(len(get_result_lines(result)), 1)

    def test_calculation_show(self):
        """Test verdi calculation show"""

        # Running without identifiers should not except and not print anything
        options = []
        result = self.cli_runner.invoke(command.calculation_show, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 0)

        # Giving a single identifier should print a non empty string message
        options = [str(self.calcs[0].pk)]
        result = self.cli_runner.invoke(command.calculation_show, options)
        self.assertClickResultNoException(result)
        self.assertTrue(len(get_result_lines(result)) > 0)

        # Giving multiple identifiers should print a non empty string message
        options = [str(calc.pk) for calc in self.calcs]
        result = self.cli_runner.invoke(command.calculation_show, options)
        self.assertClickResultNoException(result)
        self.assertTrue(len(get_result_lines(result)) > 0)

    def test_calculation_logshow(self):
        """Test verdi calculation logshow"""

        # Running without identifiers should not except and not print anything
        options = []
        result = self.cli_runner.invoke(command.calculation_logshow, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 0)

        # Giving a single identifier should print a non empty string message
        options = [str(self.calcs[0].pk)]
        result = self.cli_runner.invoke(command.calculation_logshow, options)
        self.assertClickResultNoException(result)
        self.assertTrue(len(get_result_lines(result)) > 0)

        # Giving multiple identifiers should print a non empty string message
        options = [str(calc.pk) for calc in self.calcs]
        result = self.cli_runner.invoke(command.calculation_logshow, options)
        self.assertClickResultNoException(result)
        self.assertTrue(len(get_result_lines(result)) > 0)

    @unittest.skip('reenable when issue #2342 is addressed')
    def test_calculation_plugins(self):
        """Test verdi calculation plugins"""
        from aiida.plugins.entry_point import get_entry_points

        calculation_plugins = get_entry_points('aiida.calculations')

        result = self.cli_runner.invoke(command.calculation_plugins, ['non_existent'])
        self.assertIsNotNone(result.exception)

        result = self.cli_runner.invoke(command.calculation_plugins, ['arithmetic.add'])
        self.assertClickResultNoException(result)
        self.assertTrue(len(get_result_lines(result)) > 0)

        result = self.cli_runner.invoke(command.calculation_plugins)
        self.assertClickResultNoException(result)
        self.assertTrue(len(get_result_lines(result)) > len(calculation_plugins))

    @unittest.skip('reenable when issue #2342 is addressed')
    def test_calculation_inputls(self):
        """Test verdi calculation inputls"""
        options = []
        result = self.cli_runner.invoke(command.calculation_inputls, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calculation_inputls, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 3)
        self.assertIn('.aiida', get_result_lines(result))
        self.assertIn('aiida.in', get_result_lines(result))
        self.assertIn('_aiidasubmit.sh', get_result_lines(result))

        options = [self.arithmetic_job.uuid, '.aiida']
        result = self.cli_runner.invoke(command.calculation_inputls, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 2)
        self.assertIn('calcinfo.json', get_result_lines(result))
        self.assertIn('job_tmpl.json', get_result_lines(result))

    @unittest.skip('reenable when issue #2342 is addressed')
    def test_calculation_outputls(self):
        """Test verdi calculation outputls"""
        options = []
        result = self.cli_runner.invoke(command.calculation_outputls, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calculation_outputls, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 3)
        self.assertIn('_scheduler-stderr.txt', get_result_lines(result))
        self.assertIn('_scheduler-stdout.txt', get_result_lines(result))
        self.assertIn('aiida.out', get_result_lines(result))

        options = [self.arithmetic_job.uuid, 'aiida.out']
        result = self.cli_runner.invoke(command.calculation_outputls, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertIn('aiida.out', get_result_lines(result))

    @unittest.skip('reenable when issue #2342 is addressed')
    def test_calculation_inputcat(self):
        """Test verdi calculation inputcat"""
        options = []
        result = self.cli_runner.invoke(command.calculation_inputcat, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calculation_inputcat, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertEqual(get_result_lines(result)[0], '2 3')

        options = [self.arithmetic_job.uuid, 'aiida.in']
        result = self.cli_runner.invoke(command.calculation_inputcat, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertEqual(get_result_lines(result)[0], '2 3')

    @unittest.skip('reenable when issue #2342 is addressed')
    def test_calculation_outputcat(self):
        """Test verdi calculation outputcat"""
        options = []
        result = self.cli_runner.invoke(command.calculation_outputcat, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calculation_outputcat, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertEqual(get_result_lines(result)[0], '5')

        options = [self.arithmetic_job.uuid, 'aiida.out']
        result = self.cli_runner.invoke(command.calculation_outputcat, options)
        self.assertClickResultNoException(result)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertEqual(get_result_lines(result)[0], '5')

    def test_calculation_cleanworkdir(self):
        """Test verdi calculation cleanworkdir"""

        # Specifying no filtering options and no explicit calculations should exit with non-zero status
        options = []
        result = self.cli_runner.invoke(command.calculation_cleanworkdir, options)
        self.assertIsNotNone(result.exception)

        # Cannot specify both -p and -o options
        for flag_p in ['-p', '--past-days']:
            for flag_o in ['-o', '--older-than']:
                options = [flag_p, '5', flag_o, '1']
                result = self.cli_runner.invoke(command.calculation_cleanworkdir, options)
                self.assertIsNotNone(result.exception)

        # Without the force flag it should fail
        options = [str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calculation_cleanworkdir, options)
        self.assertIsNotNone(result.exception)

        # With force flag we should find one calculation
        options = ['-f', str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calculation_cleanworkdir, options)
        self.assertClickResultNoException(result)
