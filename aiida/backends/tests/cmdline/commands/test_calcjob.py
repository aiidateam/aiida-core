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
"""Tests for `verdi calcjob`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_calcjob as command
from aiida.common.datastructures import calc_states
from aiida.orm.node.process.calculation.calcjob import CalcJobExitStatus


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiCalculation(AiidaTestCase):
    """Tests for `verdi calcjob`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiCalculation, cls).setUpClass(*args, **kwargs)
        from aiida.backends.tests.utils.fixtures import import_archive_fixture
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.common.links import LinkType
        from aiida.orm import Node, CalculationFactory
        from aiida.orm.node.process import CalcJobNode
        from aiida.orm.data.parameter import ParameterData
        from aiida.work.processes import ProcessState
        from aiida import orm

        cls.computer = orm.Computer(
            name='comp',
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida',
            backend=cls.backend).store()

        cls.code = orm.Code(remote_computer_exec=(cls.computer, '/bin/true')).store()
        cls.group = orm.Group(name='test_group').store()
        cls.node = Node().store()
        cls.calcs = []

        user = orm.User.objects(cls.backend).get_default()
        authinfo = orm.AuthInfo(computer=cls.computer, user=user, backend=cls.backend)
        authinfo.store()

        # Create 13 CalcJobNodes (one for each CalculationState)
        for calcjob_state in calc_states:

            calc = CalcJobNode(
                computer=cls.computer, resources={
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1
                }).store()

            # Trying to set NEW will raise, but in this case we don't need to change the state
            try:
                calc._set_state(calcjob_state)
            except ModificationNotAllowed:
                pass

            try:
                exit_status = CalcJobExitStatus[calcjob_state]
            except KeyError:
                if calcjob_state == 'IMPORTED':
                    calc._set_process_state(ProcessState.FINISHED)
                else:
                    calc._set_process_state(ProcessState.RUNNING)
            else:
                calc._set_exit_status(exit_status)
                calc._set_process_state(ProcessState.FINISHED)

            cls.calcs.append(calc)

            if calcjob_state == 'PARSING':
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
        import_archive_fixture('calcjob/arithmetic.add.aiida')

        # Get the imported ArithmeticAddCalculation node
        ArithmeticAddCalculation = CalculationFactory('arithmetic.add')
        calcjobs = orm.QueryBuilder(backend=cls.backend).append(ArithmeticAddCalculation).all()[0]
        cls.arithmetic_job = calcjobs[0]

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_calcjob_res(self):
        """Test verdi calcjob res"""
        options = [str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calcjob_res, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn(self.KEY_ONE, result.output)
        self.assertIn(self.VAL_ONE, result.output)
        self.assertIn(self.KEY_TWO, result.output)
        self.assertIn(self.VAL_TWO, result.output)

        for flag in ['-k', '--keys']:
            options = [flag, self.KEY_ONE, '--', str(self.result_job.uuid)]
            result = self.cli_runner.invoke(command.calcjob_res, options)
            self.assertIsNone(result.exception, result.output)
            self.assertIn(self.KEY_ONE, result.output)
            self.assertIn(self.VAL_ONE, result.output)
            self.assertNotIn(self.KEY_TWO, result.output)
            self.assertNotIn(self.VAL_TWO, result.output)

    def test_calcjob_inputls(self):
        """Test verdi calcjob inputls"""
        options = []
        result = self.cli_runner.invoke(command.calcjob_inputls, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_inputls, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 3)
        self.assertIn('.aiida', get_result_lines(result))
        self.assertIn('aiida.in', get_result_lines(result))
        self.assertIn('_aiidasubmit.sh', get_result_lines(result))

        options = [self.arithmetic_job.uuid, '.aiida']
        result = self.cli_runner.invoke(command.calcjob_inputls, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 2)
        self.assertIn('calcinfo.json', get_result_lines(result))
        self.assertIn('job_tmpl.json', get_result_lines(result))

    def test_calcjob_outputls(self):
        """Test verdi calcjob outputls"""
        options = []
        result = self.cli_runner.invoke(command.calcjob_outputls, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_outputls, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 3)
        self.assertIn('_scheduler-stderr.txt', get_result_lines(result))
        self.assertIn('_scheduler-stdout.txt', get_result_lines(result))
        self.assertIn('aiida.out', get_result_lines(result))

        options = [self.arithmetic_job.uuid, 'aiida.out']
        result = self.cli_runner.invoke(command.calcjob_outputls, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertIn('aiida.out', get_result_lines(result))

    def test_calcjob_inputcat(self):
        """Test verdi calcjob inputcat"""
        options = []
        result = self.cli_runner.invoke(command.calcjob_inputcat, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_inputcat, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertEqual(get_result_lines(result)[0], '2 3')

        options = [self.arithmetic_job.uuid, 'aiida.in']
        result = self.cli_runner.invoke(command.calcjob_inputcat, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertEqual(get_result_lines(result)[0], '2 3')

    def test_calcjob_outputcat(self):
        """Test verdi calcjob outputcat"""
        options = []
        result = self.cli_runner.invoke(command.calcjob_outputcat, options)
        self.assertIsNotNone(result.exception)

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_outputcat, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertEqual(get_result_lines(result)[0], '5')

        options = [self.arithmetic_job.uuid, 'aiida.out']
        result = self.cli_runner.invoke(command.calcjob_outputcat, options)
        self.assertIsNone(result.exception, result.output)
        self.assertEqual(len(get_result_lines(result)), 1)
        self.assertEqual(get_result_lines(result)[0], '5')

    def test_calcjob_cleanworkdir(self):
        """Test verdi calcjob cleanworkdir"""

        # Specifying no filtering options and no explicit calcjobs should exit with non-zero status
        options = []
        result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
        self.assertIsNotNone(result.exception)

        # Cannot specify both -p and -o options
        for flag_p in ['-p', '--past-days']:
            for flag_o in ['-o', '--older-than']:
                options = [flag_p, '5', flag_o, '1']
                result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
                self.assertIsNotNone(result.exception)

        # Without the force flag it should fail
        options = [str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
        self.assertIsNotNone(result.exception)

        # With force flag we should find one calcjob
        options = ['-f', str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
        self.assertIsNone(result.exception, result.output)
