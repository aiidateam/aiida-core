# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import click
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params import options
from aiida.cmdline.params.types import CalculationParamType
from aiida.orm import Calculation, FunctionCalculation, InlineCalculation, JobCalculation, WorkCalculation
from aiida.orm.utils.loaders import OrmEntityLoader


class TestCalculationParamType(AiidaTestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create some code to test the CalculationParamType parameter type for the command line infrastructure
        We create an initial code with a random name and then on purpose create two code with a name
        that matches exactly the ID and UUID, respectively, of the first one. This allows us to test
        the rules implemented to solve ambiguities that arise when determing the identifier type
        """
        super(TestCalculationParamType, cls).setUpClass()

        cls.param = CalculationParamType()
        cls.entity_01 = Calculation().store()
        cls.entity_02 = Calculation().store()
        cls.entity_03 = Calculation().store()
        cls.entity_04 = FunctionCalculation()
        cls.entity_05 = InlineCalculation()
        cls.entity_06 = JobCalculation()
        cls.entity_07 = WorkCalculation()

        cls.entity_01.label = 'calculation_01'
        cls.entity_02.label = str(cls.entity_01.pk)
        cls.entity_03.label = str(cls.entity_01.uuid)

    def test_get_by_id(self):
        """
        Verify that using the ID will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.pk)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

    def test_get_by_uuid(self):
        """
        Verify that using the UUID will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.uuid)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

    def test_get_by_label(self):
        """
        Verify that using the LABEL will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.label)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

    def test_ambiguous_label_pk(self):
        """
        Situation: LABEL of entity_02 is exactly equal to ID of entity_01

        Verify that using an ambiguous identifier gives precedence to the ID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = '{}'.format(self.entity_02.label)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_02.label, OrmEntityLoader.LABEL_AMBIGUITY_BREAKER_CHARACTER)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_02.uuid)

    def test_ambiguous_label_uuid(self):
        """
        Situation: LABEL of entity_03 is exactly equal to UUID of entity_01

        Verify that using an ambiguous identifier gives precedence to the UUID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = '{}'.format(self.entity_03.label)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_03.label, OrmEntityLoader.LABEL_AMBIGUITY_BREAKER_CHARACTER)
        result = self.param.convert(identifier, None, None)
        self.assertEquals(result.uuid, self.entity_03.uuid)
