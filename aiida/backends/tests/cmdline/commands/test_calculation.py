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
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_calculation as command
from aiida.common.datastructures import calc_states
from aiida.orm.calculation.job import JobCalculationExitStatus
from aiida.work import runners, rmq


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiCalculation(AiidaTestCase):
    """Tests for `verdi calculation`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiCalculation, cls).setUpClass(*args, **kwargs)
        from aiida.backends.tests.utils.fixtures import import_archive_fixture
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.common.links import LinkType
        from aiida.orm import Code, Group, Node, JobCalculation, CalculationFactory
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.work.processes import ProcessState
        from aiida.orm.backends import construct_backend
        backend = construct_backend()

        rmq_config = rmq.get_rmq_config()

        # These two need to share a common event loop otherwise the first will never send
        # the message while the daemon is running listening to intercept
        cls.runner = runners.Runner(rmq_config=rmq_config, rmq_submit=True, poll_interval=0.)
        cls.daemon_runner = runners.DaemonRunner(rmq_config=rmq_config, rmq_submit=True, poll_interval=0.)

        cls.computer = backend.computers.create(name='comp', hostname='localhost', transport_type='local',
                                                scheduler_type='direct', workdir='/tmp/aiida').store()

        cls.code = Code(remote_computer_exec=(cls.computer, '/bin/true')).store()
        cls.group = Group(name='test_group').store()
        cls.node = Node().store()
        cls.calcs = []

        authinfo = backend.authinfos.create(computer=cls.computer, user=backend.users.get_automatic_user())
        authinfo.store()

        # Create 13 JobCalculations (one for each CalculationState)
        for calculation_state in calc_states:

            calc = JobCalculation(
                computer=cls.computer, resources={
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1
                }).store()

            # Trying to set NEW will raise, but in this case we don't need to change the state
            try:
                calc._set_state(calculation_state)
            except ModificationNotAllowed:
                pass

            try:
                exit_status = JobCalculationExitStatus[calculation_state]
            except KeyError:
                if calculation_state == 'IMPORTED':
                    calc._set_process_state(ProcessState.FINISHED)
                else:
                    calc._set_process_state(ProcessState.RUNNING)
            else:
                calc._set_exit_status(exit_status)
                calc._set_process_state(ProcessState.FINISHED)

            cls.calcs.append(calc)

            if calculation_state == 'PARSING':
                cls.KEY_ONE = 'key_one'
                cls.KEY_TWO = 'key_two'
                cls.VAL_ONE = 'val_one'
                cls.VAL_TWO = 'val_two'

                output_parameters = ParameterData(dict={
                    cls.KEY_ONE: cls.VAL_ONE,
                    cls.KEY_TWO: cls.VAL_TWO,
                }).store()

                output_parameters.add_link_from(calc, 'output_parameters', link_type=LinkType.RETURN)

                # Create shortcut for easy dereferencing
                cls.result_job = calc

                # Add a single calc to a group
                cls.group.add_nodes([calc])

        # Load the fixture containing a single ArithmeticAddCalculation node
        import_archive_fixture('calculation/simpleplugins.arithmetic.add.aiida')

        # Get the imported ArithmeticAddCalculation node
        ArithmeticAddCalculation = CalculationFactory('simpleplugins.arithmetic.add')
        calculations = QueryBuilder().append(ArithmeticAddCalculation).all()[0]
        cls.arithmetic_job = calculations[0]

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_calculation_res(self):
        """Test verdi calculation res"""
        options = [str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calculation_res, options)
        self.assertIsNone(result.exception)
        self.assertIn(self.KEY_ONE, result.output)
        self.assertIn(self.VAL_ONE, result.output)
        self.assertIn(self.KEY_TWO, result.output)
        self.assertIn(self.VAL_TWO, result.output)

        for flag in ['-k', '--keys']:
            options = [flag, self.KEY_ONE, '--', str(self.result_job.uuid)]
            result = self.cli_runner.invoke(command.calculation_res, options)
            self.assertIsNone(result.exception)
            self.assertIn(self.KEY_ONE, result.output)
            self.assertIn(self.VAL_ONE, result.output)
            self.assertNotIn(self.KEY_TWO, result.output)
            self.assertNotIn(self.VAL_TWO, result.output)

    def test_calculation_list_identifiers(self):
        """Test verdi calculation list with specific identifiers"""
        options = ['-r', '--project', 'pk', '--'] + [str(calc.pk) for calc in self.calcs[:2]]
        result = self.cli_runner.invoke(command.calculation_list, options)
        self.assertIsNone(result.exception)

        valid_pks = [calc.pk for calc in self.calcs]
        for line in get_result_lines(result):
            self.assertIn(int(line), valid_pks)

    def test_calculation_list_all_user(self):
        """Test verdi calculation list with the all users option"""
        for flag in ['-A', '--all-users']:
            options = ['-r', '-a', flag]
            result = self.cli_runner.invoke(command.calculation_list, options)
            self.assertIsNone(result.exception)
            self.assertEquals(len(get_result_lines(result)), 14)

    def test_calculation_list_all(self):
        """Test verdi calculation list with the all option"""

        # Without the flag I should only get the "active" states, which should be seven
        options = ['-r']
        result = self.cli_runner.invoke(command.calculation_list, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 7, result.output)

        for flag in ['-a', '--all']:
            options = ['-r', flag]
            result = self.cli_runner.invoke(command.calculation_list, options)
            self.assertIsNone(result.exception)
            self.assertEquals(len(get_result_lines(result)), 13)

    def test_calculation_list_limit(self):
        """Test verdi calculation list with the limit option"""
        for flag in ['-l', '--limit']:
            limit = 1
            options = ['-r', flag, limit]
            result = self.cli_runner.invoke(command.calculation_list, options)
            self.assertIsNone(result.exception)
            self.assertEquals(len(get_result_lines(result)), limit)

    def test_calculation_list_group(self):
        """Test verdi calculation list with the group option"""
        for flag in ['-G', '--groups']:
            options = ['-r', '-a', flag, self.group.uuid]
            result = self.cli_runner.invoke(command.calculation_list, options)
            self.assertIsNone(result.exception)
            self.assertEquals(len(get_result_lines(result)), 1)

    def test_calculation_list_project(self):
        """Test verdi calculation list with the project option"""
        for flag in ['-P', '--project']:
            options = ['-r', flag, 'pk']
            result = self.cli_runner.invoke(command.calculation_list, options)
            self.assertIsNone(result.exception)

            valid_pks = [calc.pk for calc in self.calcs]
            for line in get_result_lines(result):
                self.assertIn(int(line), valid_pks)

    def test_calculation_list_calculation_state(self):
        """Test verdi calculation list with the calculation state filter"""
        for flag in ['-s', '--calculation-state']:
            for state in calc_states:
                # Each valid state should have exactly one entry
                options = ['-r', flag, state]
                result = self.cli_runner.invoke(command.calculation_list, options)
                self.assertIsNone(result.exception)
                self.assertEquals(len(get_result_lines(result)), 1)

    def test_calculation_list_process_state(self):
        """Test verdi calculation list with the process state filter"""
        for flag in ['-S', '--process-state']:
            for state in ['finished', 'running']:

                options = ['-r', flag, state]
                result = self.cli_runner.invoke(command.calculation_list, options)

                self.assertIsNone(result.exception)

                if state == 'finished':
                    self.assertEquals(len(get_result_lines(result)), 6, result.output)
                else:
                    self.assertEquals(len(get_result_lines(result)), 7, result.output)

    def test_calculation_list_failed(self):
        """Test verdi calculation list with the failed filter"""
        for flag in ['-X', '--failed']:
            options = ['-r', flag]
            result = self.cli_runner.invoke(command.calculation_list, options)

            self.assertIsNone(result.exception)
            self.assertEquals(len(get_result_lines(result)), 4, result.output)

    def test_calculation_list_exit_status(self):
        """Test verdi calculation list with the exit status filter"""
        for flag in ['-E', '--exit-status']:
            for exit_status in JobCalculationExitStatus:
                options = ['-r', flag, exit_status.value]
                result = self.cli_runner.invoke(command.calculation_list, options)

                self.assertIsNone(result.exception)
                self.assertEquals(len(get_result_lines(result)), 1)

    def test_calculation_show(self):
        """Test verdi calculation show"""

        # Running without identifiers should not except and not print anything
        options = []
        result = self.cli_runner.invoke(command.calculation_show, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 0)

        # Giving a single identifier should print a non empty string message
        options = [str(self.calcs[0].pk)]
        result = self.cli_runner.invoke(command.calculation_show, options)
        self.assertIsNone(result.exception)
        self.assertTrue(len(get_result_lines(result)) > 0)

        # Giving multiple identifiers should print a non empty string message
        options = [str(calc.pk) for calc in self.calcs]
        result = self.cli_runner.invoke(command.calculation_show, options)
        self.assertIsNone(result.exception)
        self.assertTrue(len(get_result_lines(result)) > 0)

    def test_calculation_logshow(self):
        """Test verdi calculation logshow"""

        # Running without identifiers should not except and not print anything
        options = []
        result = self.cli_runner.invoke(command.calculation_logshow, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 0)

        # Giving a single identifier should print a non empty string message
        options = [str(self.calcs[0].pk)]
        result = self.cli_runner.invoke(command.calculation_logshow, options)
        self.assertIsNone(result.exception)
        self.assertTrue(len(get_result_lines(result)) > 0)

        # Giving multiple identifiers should print a non empty string message
        options = [str(calc.pk) for calc in self.calcs]
        result = self.cli_runner.invoke(command.calculation_logshow, options)
        self.assertIsNone(result.exception)
        self.assertTrue(len(get_result_lines(result)) > 0)

    def test_calculation_plugins(self):
        """Test verdi calculation plugins"""
        from aiida.plugins.entry_point import get_entry_points

        calculation_plugins = get_entry_points('aiida.calculations')

        result = self.cli_runner.invoke(command.calculation_plugins, ['non_existent'])
        self.assertIsNotNone(result.exception)

        result = self.cli_runner.invoke(command.calculation_plugins, ['simpleplugins.arithmetic.add'])
        self.assertIsNone(result.exception)
        self.assertTrue(len(get_result_lines(result)) > 0)

        result = self.cli_runner.invoke(command.calculation_plugins)
        self.assertIsNone(result.exception)
        self.assertTrue(len(get_result_lines(result)) > len(calculation_plugins))

    def test_calculation_inputls(self):
        """Test verdi calculation inputls"""
        options = []
        result = self.cli_runner.invoke(command.calculation_inputls, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calculation_inputls, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 3)
        self.assertIn('.aiida', get_result_lines(result))
        self.assertIn('aiida.in', get_result_lines(result))
        self.assertIn('_aiidasubmit.sh', get_result_lines(result))

        options = [self.arithmetic_job.uuid, '.aiida']
        result = self.cli_runner.invoke(command.calculation_inputls, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 2)
        self.assertIn('calcinfo.json', get_result_lines(result))
        self.assertIn('job_tmpl.json', get_result_lines(result))

    def test_calculation_outputls(self):
        """Test verdi calculation outputls"""
        options = []
        result = self.cli_runner.invoke(command.calculation_outputls, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calculation_outputls, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 3)
        self.assertIn('_scheduler-stderr.txt', get_result_lines(result))
        self.assertIn('_scheduler-stdout.txt', get_result_lines(result))
        self.assertIn('aiida.out', get_result_lines(result))

        options = [self.arithmetic_job.uuid, 'aiida.out']
        result = self.cli_runner.invoke(command.calculation_outputls, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 1)
        self.assertIn('aiida.out', get_result_lines(result))

    def test_calculation_inputcat(self):
        """Test verdi calculation inputcat"""
        options = []
        result = self.cli_runner.invoke(command.calculation_inputcat, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calculation_inputcat, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 1)
        self.assertEquals(get_result_lines(result)[0], '2 3')

        options = [self.arithmetic_job.uuid, 'aiida.in']
        result = self.cli_runner.invoke(command.calculation_inputcat, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 1)
        self.assertEquals(get_result_lines(result)[0], '2 3')

    def test_calculation_outputcat(self):
        """Test verdi calculation outputcat"""
        options = []
        result = self.cli_runner.invoke(command.calculation_outputcat, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calculation_outputcat, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 1)
        self.assertEquals(get_result_lines(result)[0], '5')

        options = [self.arithmetic_job.uuid, 'aiida.out']
        result = self.cli_runner.invoke(command.calculation_outputcat, options)
        self.assertIsNone(result.exception)
        self.assertEquals(len(get_result_lines(result)), 1)
        self.assertEquals(get_result_lines(result)[0], '5')

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
        self.assertIsNone(result.exception)
