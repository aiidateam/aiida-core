# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `GroupParamType`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types import GroupParamType
from aiida.orm import Group
from aiida.orm.utils.loaders import OrmEntityLoader


class TestGroupParamType(AiidaTestCase):
    """Tests for the `GroupParamType`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create some groups to test the GroupParamType parameter type for the command line infrastructure
        We create an initial group with a random name and then on purpose create two groups with a name
        that matches exactly the ID and UUID, respectively, of the first one. This allows us to test
        the rules implemented to solve ambiguities that arise when determing the identifier type
        """
        super(TestGroupParamType, cls).setUpClass(*args, **kwargs)

        cls.param = GroupParamType()
        cls.entity_01 = Group(label='group_01').store()
        cls.entity_02 = Group(label=str(cls.entity_01.pk)).store()
        cls.entity_03 = Group(label=str(cls.entity_01.uuid)).store()

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
        identifier = '{}'.format(self.entity_01.label)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

    def test_ambiguous_label_pk(self):
        """
        Situation: LABEL of entity_02 is exactly equal to ID of entity_01

        Verify that using an ambiguous identifier gives precedence to the ID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = '{}'.format(self.entity_02.label)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_02.label, OrmEntityLoader.label_ambiguity_breaker)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_02.uuid)

    def test_ambiguous_label_uuid(self):
        """
        Situation: LABEL of entity_03 is exactly equal to UUID of entity_01

        Verify that using an ambiguous identifier gives precedence to the UUID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = '{}'.format(self.entity_03.label)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_03.label, OrmEntityLoader.label_ambiguity_breaker)
        result = self.param.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_03.uuid)
