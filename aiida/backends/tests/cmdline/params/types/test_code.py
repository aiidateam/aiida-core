# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `CodeParamType`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types import CodeParamType
from aiida.orm import Code
from aiida.orm.utils.loaders import OrmEntityLoader


class TestCodeParamType(AiidaTestCase):
    """Tests for the `CodeParamType`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create some code to test the CodeParamType parameter type for the command line infrastructure
        We create an initial code with a random name and then on purpose create two code with a name
        that matches exactly the ID and UUID, respectively, of the first one. This allows us to test
        the rules implemented to solve ambiguities that arise when determing the identifier type
        """
        super(TestCodeParamType, cls).setUpClass(*args, **kwargs)

        cls.param_base = CodeParamType()
        cls.param_entry_point = CodeParamType(entry_point='arithmetic.add')
        cls.entity_01 = Code(remote_computer_exec=(cls.computer, '/bin/true')).store()
        cls.entity_02 = Code(
            remote_computer_exec=(cls.computer, '/bin/true'), input_plugin_name='arithmetic.add').store()
        cls.entity_03 = Code(
            remote_computer_exec=(cls.computer, '/bin/true'), input_plugin_name='templatereplacer').store()

        cls.entity_01.label = 'computer_01'
        cls.entity_02.label = str(cls.entity_01.pk)
        cls.entity_03.label = str(cls.entity_01.uuid)

    def test_get_by_id(self):
        """
        Verify that using the ID will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.pk)
        result = self.param_base.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

    def test_get_by_uuid(self):
        """
        Verify that using the UUID will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.uuid)
        result = self.param_base.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

    def test_get_by_label(self):
        """
        Verify that using the LABEL will retrieve the correct entity
        """
        identifier = '{}'.format(self.entity_01.label)
        result = self.param_base.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

    def test_get_by_fullname(self):
        """
        Verify that using the LABEL@machinename will retrieve the correct entity
        """
        identifier = '{}@{}'.format(self.entity_01.label, self.computer.name)  # pylint: disable=no-member
        result = self.param_base.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

    def test_ambiguous_label_pk(self):
        """
        Situation: LABEL of entity_02 is exactly equal to ID of entity_01

        Verify that using an ambiguous identifier gives precedence to the ID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = '{}'.format(self.entity_02.label)
        result = self.param_base.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_02.label, OrmEntityLoader.label_ambiguity_breaker)
        result = self.param_base.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_02.uuid)

    def test_ambiguous_label_uuid(self):
        """
        Situation: LABEL of entity_03 is exactly equal to UUID of entity_01

        Verify that using an ambiguous identifier gives precedence to the UUID interpretation
        Appending the special ambiguity breaker character will force the identifier to be treated as a LABEL
        """
        identifier = '{}'.format(self.entity_03.label)
        result = self.param_base.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_01.uuid)

        identifier = '{}{}'.format(self.entity_03.label, OrmEntityLoader.label_ambiguity_breaker)
        result = self.param_base.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_03.uuid)

    def test_entry_point_validation(self):
        """Verify that when an `entry_point` is defined in the constructor, it is respected in the validation."""
        identifier = '{}'.format(self.entity_02.pk)
        result = self.param_entry_point.convert(identifier, None, None)
        self.assertEqual(result.uuid, self.entity_02.uuid)

        with self.assertRaises(click.BadParameter):
            identifier = '{}'.format(self.entity_03.pk)
            result = self.param_entry_point.convert(identifier, None, None)
