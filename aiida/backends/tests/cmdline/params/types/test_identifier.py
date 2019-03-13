# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `IdentifierParamType`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types import IdentifierParamType, NodeParamType
from aiida.orm import Bool, Float, Int


class TestIdentifierParamType(AiidaTestCase):
    """Tests for the `IdentifierParamType`."""

    def test_base_class(self):
        """
        The base class is abstract and should not be constructable
        """
        with self.assertRaises(TypeError):
            IdentifierParamType()  # pylint: disable=abstract-class-instantiated

    def test_identifier_sub_invalid_type(self):
        """
        The sub_classes keyword argument should expect a tuple
        """
        with self.assertRaises(TypeError):
            NodeParamType(sub_classes='aiida.data:structure')

        with self.assertRaises(TypeError):
            NodeParamType(sub_classes=(None,))

    def test_identifier_sub_invalid_entry_point(self):
        """
        The sub_classes keyword argument should expect a tuple of valid entry point strings
        """
        with self.assertRaises(ValueError):
            NodeParamType(sub_classes=('aiida.data.structure',))

        with self.assertRaises(ValueError):
            NodeParamType(sub_classes=('aiida.data:not_existent',))

    def test_identifier_sub_classes(self):
        """
        The sub_classes keyword argument should allow to narrow the scope of the query based on the orm class
        """
        node_bool = Bool(True).store()
        node_float = Float(0.0).store()
        node_int = Int(1).store()

        param_type_normal = NodeParamType()
        param_type_scoped = NodeParamType(sub_classes=('aiida.data:bool', 'aiida.data:float'))

        # For the base NodeParamType all node types should be matched
        self.assertEqual(param_type_normal.convert(str(node_bool.pk), None, None).uuid, node_bool.uuid)
        self.assertEqual(param_type_normal.convert(str(node_float.pk), None, None).uuid, node_float.uuid)
        self.assertEqual(param_type_normal.convert(str(node_int.pk), None, None).uuid, node_int.uuid)

        # The scoped NodeParamType should only match Bool and Float
        self.assertEqual(param_type_scoped.convert(str(node_bool.pk), None, None).uuid, node_bool.uuid)
        self.assertEqual(param_type_scoped.convert(str(node_float.pk), None, None).uuid, node_float.uuid)

        # The Int should not be found and raise
        with self.assertRaises(click.BadParameter):
            param_type_scoped.convert(str(node_int.pk), None, None)
