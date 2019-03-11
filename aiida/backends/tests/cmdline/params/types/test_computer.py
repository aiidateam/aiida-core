# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `ComputerParamType`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types import ComputerParamType
from aiida.orm.utils.loaders import OrmEntityLoader

from aiida import orm


class TestComputerParamType(AiidaTestCase):
    """Tests for the `ComputerParamType`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create some computers to test the ComputerParamType parameter type for the command line infrastructure
        We create an initial computer with a random name and then on purpose create two computers with a name
        that matches exactly the ID and UUID, respectively, of the first one. This allows us to test
        the rules implemented to solve ambiguities that arise when determing the identifier type
        """
        super(TestComputerParamType, cls).setUpClass(*args, **kwargs)

        kwargs = {
            'hostname': 'localhost',
            'transport_type': 'local',
            'scheduler_type': 'direct',
            'workdir': '/tmp/aiida'
        }

        cls.param = ComputerParamType()
        cls.entity_01 = orm.Computer(name='computer_01', **kwargs).store()
        cls.entity_02 = orm.Computer(name=str(cls.entity_01.pk), **kwargs).store()
        cls.entity_03 = orm.Computer(name=str(cls.entity_01.uuid), **kwargs).store()

    def test_get_by_id(self):
        """
        Verify that using the ID will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.pk)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

    def test_get_by_uuid(self):
        """
        Verify that using the UUID will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.uuid)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

    def test_get_by_label(self):
        """
        Verify that using the LABEL will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.name)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

    def test_ambiguous_label_pk(self):
        """
        Situation: LABEL of entity_02 is exactly equal to ID of entity_01

        Verify that using an ambiguous identifier gives precedence to the ID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = '{}'.format(self.entity_02.name)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_02.name, OrmEntityLoader.label_ambiguity_breaker)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_02.uuid)

    def test_ambiguous_label_uuid(self):
        """
        Situation: LABEL of entity_03 is exactly equal to UUID of entity_01

        Verify that using an ambiguous identifier gives precedence to the UUID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = '{}'.format(self.entity_03.name)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_03.name, OrmEntityLoader.label_ambiguity_breaker)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_03.uuid)
