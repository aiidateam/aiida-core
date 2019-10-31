# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the `CalcJob` process sub class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import copy

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.engine import launch, CalcJob, Process
from aiida.engine.processes.ports import PortNamespace
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')  # pylint: disable=invalid-name


class TestCalcJob(AiidaTestCase):
    """Test for the `CalcJob` process sub class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestCalcJob, cls).setUpClass(*args, **kwargs)
        cls.remote_code = orm.Code(remote_computer_exec=(cls.computer, '/bin/true')).store()
        cls.local_code = orm.Code(local_executable='true', files=['/bin/true']).store()
        cls.inputs = {
            'x': orm.Int(1),
            'y': orm.Int(2),
            'metadata': {
                'options': {
                    'resources': {
                        'num_machines': 1,
                        'num_mpiprocs_per_machine': 1
                    },
                }
            }
        }

    def setUp(self):
        super(TestCalcJob, self).setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super(TestCalcJob, self).tearDown()
        self.assertIsNone(Process.current())

    def test_run_base_class(self):
        """Verify that it is impossible to run, submit or instantiate a base `CalcJob` class."""
        with self.assertRaises(exceptions.InvalidOperation):
            CalcJob()

        with self.assertRaises(exceptions.InvalidOperation):
            launch.run(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.run_get_node(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.run_get_pk(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.submit(CalcJob)

    def test_define_not_calling_super(self):
        """A `CalcJob` that does not call super in `define` classmethod should raise."""

        class IncompleteDefineCalcJob(CalcJob):
            """Test class with incomplete define method"""

            @classmethod
            def define(cls, spec):
                pass

            def prepare_for_submission(self, folder):
                pass

        with self.assertRaises(AssertionError):
            launch.run(IncompleteDefineCalcJob)

    def test_spec_options_property(self):
        """`CalcJob.spec_options` should return the options port namespace of its spec."""
        self.assertIsInstance(CalcJob.spec_options, PortNamespace)
        self.assertEqual(CalcJob.spec_options, CalcJob.spec().inputs['metadata']['options'])

    def test_invalid_options_type(self):
        """Verify that passing an invalid type to `metadata.options` raises a `TypeError`."""

        class SimpleCalcJob(CalcJob):
            """Simple `CalcJob` implementation"""

            @classmethod
            def define(cls, spec):
                super(SimpleCalcJob, cls).define(spec)

            def prepare_for_submission(self, folder):
                pass

        # The `metadata.options` input expects a plain dict and not a node `Dict`
        with self.assertRaises(TypeError):
            launch.run(SimpleCalcJob, code=self.remote_code, metadata={'options': orm.Dict(dict={'a': 1})})

    def test_remote_code_set_computer_implicit(self):
        """Test launching a `CalcJob` with a remote code *with* explicitly defining a computer.

        This should work, because the `computer` should be retrieved from the `code` and automatically set for the
        process by the engine itself.
        """
        inputs = copy.deepcopy(self.inputs)
        inputs['code'] = self.remote_code

        process = ArithmeticAddCalculation(inputs=inputs)
        self.assertTrue(process.node.is_stored)
        self.assertEqual(process.node.computer.uuid, self.remote_code.computer.uuid)

    def test_remote_code_unstored_computer(self):
        """Test launching a `CalcJob` with an unstored computer which should raise."""
        inputs = copy.deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['computer'] = orm.Computer('different', 'localhost', 'desc', 'local', 'direct')

        with self.assertRaises(exceptions.InputValidationError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_remote_code_set_computer_explicit(self):
        """Test launching a `CalcJob` with a remote code *with* explicitly defining a computer.

        This should work as long as the explicitly defined computer is the same as the one configured for the `code`
        input. If this is not the case, it should raise.
        """
        inputs = copy.deepcopy(self.inputs)
        inputs['code'] = self.remote_code

        # Setting explicitly a computer that is not the same as that of the `code` should raise
        with self.assertRaises(exceptions.InputValidationError):
            inputs['metadata']['computer'] = orm.Computer('different', 'localhost', 'desc', 'local', 'direct').store()
            process = ArithmeticAddCalculation(inputs=inputs)

        # Setting the same computer as that of the `code` effectively accomplishes nothing but should be fine
        inputs['metadata']['computer'] = self.remote_code.computer
        process = ArithmeticAddCalculation(inputs=inputs)
        self.assertTrue(process.node.is_stored)
        self.assertEqual(process.node.computer.uuid, self.remote_code.computer.uuid)

    def test_local_code_set_computer(self):
        """Test launching a `CalcJob` with a local code *with* explicitly defining a computer, which should work."""
        inputs = copy.deepcopy(self.inputs)
        inputs['code'] = self.local_code
        inputs['metadata']['computer'] = self.computer

        process = ArithmeticAddCalculation(inputs=inputs)
        self.assertTrue(process.node.is_stored)
        self.assertEqual(process.node.computer.uuid, self.computer.uuid)  # pylint: disable=no-member

    def test_local_code_no_computer(self):
        """Test launching a `CalcJob` with a local code *without* explicitly defining a computer, which should raise."""
        inputs = copy.deepcopy(self.inputs)
        inputs['code'] = self.local_code

        with self.assertRaises(exceptions.InputValidationError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_invalid_parser_name(self):
        """Passing an invalid parser name should already stop during input validation."""
        inputs = copy.deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['options']['parser_name'] = 'invalid_parser'

        with self.assertRaises(exceptions.InputValidationError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_invalid_resources(self):
        """Passing invalid resources should already stop during input validation."""
        inputs = copy.deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['options']['resources'].pop('num_machines')

        with self.assertRaises(exceptions.InputValidationError):
            ArithmeticAddCalculation(inputs=inputs)
