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
from aiida.work.process_builder import ProcessBuilder
from aiida.work import utils


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