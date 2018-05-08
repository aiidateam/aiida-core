# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import CalculationFactory
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.bool import Bool
from aiida.orm.data.float import Float
from aiida.orm.data.int import Int
from aiida.work.process_builder import ProcessBuilder
from aiida.work.workchain import WorkChain
from aiida.work import utils

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
        self.assertEquals(len(utils.ProcessStack.stack()), 0)
        self.calculation_class = CalculationFactory('simpleplugins.templatereplacer')
        self.process_class = self.calculation_class.process()
        self.builder = self.process_class.get_builder()

    def tearDown(self):
        super(TestProcessBuilder, self).tearDown()
        self.assertEquals(len(utils.ProcessStack.stack()), 0)

    def test_process_builder_attributes(self):
        """
        Check that the builder has all the input ports of the process class as attributes
        """
        for name, port in self.process_class.spec().inputs.iteritems():
            self.assertTrue(hasattr(self.builder, name))

    def test_process_builder_set_attributes(self):
        """
        Verify that setting attributes in builder works
        """
        label = 'Test label'
        description = 'Test description'

        self.builder.label = label
        self.builder.description = description

        self.assertEquals(self.builder.label, label)
        self.assertEquals(self.builder.description, description)

    def test_workchain(self):
        """
        Verify that the attributes of the TestWorkChain can be set but defaults are not there
        """
        builder = TestWorkChain.get_builder()
        builder.a = Int(2)
        builder.b = Float(2.3)
        builder.c.d = Bool(True)
        self.assertEquals(builder, {'a': Int(2), 'b': Float(2.3), 'c': {'d': Bool(True)}})

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
