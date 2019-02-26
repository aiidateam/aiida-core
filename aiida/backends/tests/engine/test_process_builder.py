# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.engine import WorkChain, Process
from aiida.orm import Dict, Bool, Float, Int
from aiida.plugins import CalculationFactory

DEFAULT_INT = 256


class TestWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(TestWorkChain, cls).define(spec)
        spec.input('a', valid_type=Int, help='A pointless integer')
        spec.input('b', valid_type=Float, help='A pointless float')
        spec.input('c.d', valid_type=Bool, help='A pointless boolean')
        spec.input('e', valid_type=Int, default=Int(DEFAULT_INT))


class TestProcessBuilder(AiidaTestCase):

    def setUp(self):
        super(TestProcessBuilder, self).setUp()
        self.assertIsNone(Process.current())
        self.process_class = CalculationFactory('templatereplacer')
        self.builder = self.process_class.get_builder()

    def tearDown(self):
        super(TestProcessBuilder, self).tearDown()
        self.assertIsNone(Process.current())

    def test_process_builder_attributes(self):
        """
        Check that the builder has all the input ports of the process class as attributes
        """
        for name, port in self.process_class.spec().inputs.items():
            self.assertTrue(hasattr(self.builder, name))

    def test_process_builder_set_attributes(self):
        """
        Verify that setting attributes in builder works
        """
        label = 'Test label'
        description = 'Test description'

        self.builder.metadata.label = label
        self.builder.metadata.description = description

        self.assertEquals(self.builder.metadata.label, label)
        self.assertEquals(self.builder.metadata.description, description)

    def test_workchain(self):
        """
        Verify that the attributes of the TestWorkChain can be set but defaults are not there
        """
        builder = TestWorkChain.get_builder()
        builder.a = Int(2)
        builder.b = Float(2.3)
        builder.c.d = Bool(True)
        self.assertEquals(builder, {'a': Int(2), 'b': Float(2.3), 'c': {'d': Bool(True)}, 'metadata': {'options': {}}})

    def test_invalid_setattr_raises(self):
        """
        Verify that __setattr__ cannot be called on a terminal Port
        """
        builder = TestWorkChain.get_builder()
        with self.assertRaises(AttributeError):
            builder.a.b = 3

    def test_dynamic_getters_value(self):
        """
        Verify that getters will return the actual value
        """
        builder = TestWorkChain.get_builder()
        builder.a = Int(2)
        builder.b = Float(2.3)
        builder.c.d = Bool(True)

        # Verify that the correct type is returned by the getter
        self.assertTrue(isinstance(builder.a, Int))
        self.assertTrue(isinstance(builder.b, Float))
        self.assertTrue(isinstance(builder.c.d, Bool))

        # Verify that the correct value is returned by the getter
        self.assertEquals(builder.a, Int(2))
        self.assertEquals(builder.b, Float(2.3))
        self.assertEquals(builder.c.d, Bool(True))

    def test_dynamic_getters_doc_string(self):
        """
        Verify that getters have the correct docstring
        """
        builder = TestWorkChain.get_builder()
        self.assertEquals(builder.__class__.a.__doc__, str(TestWorkChain.spec().inputs['a']))
        self.assertEquals(builder.__class__.b.__doc__, str(TestWorkChain.spec().inputs['b']))
        self.assertEquals(builder.__class__.c.__doc__, str(TestWorkChain.spec().inputs['c']))
        self.assertEquals(builder.c.__class__.d.__doc__, str(TestWorkChain.spec().inputs['c']['d']))

    def test_job_calculation_get_builder_restart(self):
        """
        Test the get_builder_restart method of CalcJobNode class
        """
        from aiida.orm import CalcJobNode

        # Have to set the process type manually, because usually this will be done automatically when the node is
        # instantiated by the process itself. Since we hack it here and instantiate the node directly ourselves we
        # have to set the process type for the restart builder to be able to recreate the process class.
        original = CalcJobNode(
            computer=self.computer, process_type='aiida.calculations:templatereplacer', label='original')
        original.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        original.set_option('max_wallclock_seconds', 1800)
        original.store()

        builder = original.get_builder_restart()

        self.assertDictEqual(builder.metadata.options, original.get_options())

    def test_code_get_builder(self):
        """
        Test that the get_builder method of Code returns a builder
        where the code is already set.
        """
        from aiida.orm import Code

        code1 = Code()
        # This also sets the code as a remote code
        code1.set_remote_computer_exec((self.computer, '/bin/true'))
        code1.label = 'test_code1'
        code1.set_input_plugin_name('templatereplacer')
        code1.store()

        # Check that I can get a builder
        builder = code1.get_builder()
        self.assertEquals(builder.code.pk, code1.pk)

        # Check that I can set the parameters
        builder.parameters = Dict(dict={})

        # Check that it complains for an unknown input
        with self.assertRaises(AttributeError):
            builder.unknown_parameter = 3

        # Check that it complains if the type is not the correct one
        # (for the templatereplacer, it should be a
        # Dict)
        with self.assertRaises(ValueError):
            builder.parameters = Int(3)
