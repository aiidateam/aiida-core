# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `IdentifierParamType`."""
import click
import pytest

from aiida.cmdline.params.types import IdentifierParamType, NodeParamType
from aiida.orm import Bool, Float, Int


@pytest.mark.usefixtures('aiida_profile_clean')
class TestIdentifierParamType:
    """Tests for the `IdentifierParamType`."""

    # pylint: disable=no-self-use

    def test_base_class(self):
        """
        The base class is abstract and should not be constructable
        """
        with pytest.raises(TypeError):
            IdentifierParamType()  # pylint: disable=abstract-class-instantiated

    def test_identifier_sub_invalid_type(self):
        """
        The sub_classes keyword argument should expect a tuple
        """
        with pytest.raises(TypeError):
            NodeParamType(sub_classes='aiida.data:core.structure')

        with pytest.raises(TypeError):
            NodeParamType(sub_classes=(None,))

    def test_identifier_sub_invalid_entry_point(self):
        """
        The sub_classes keyword argument should expect a tuple of valid entry point strings
        """
        with pytest.raises(ValueError):
            NodeParamType(sub_classes=('aiida.data.structure',))

        with pytest.raises(ValueError):
            NodeParamType(sub_classes=('aiida.data:not_existent',))

    def test_identifier_sub_classes(self):
        """
        The sub_classes keyword argument should allow to narrow the scope of the query based on the orm class
        """
        node_bool = Bool(True).store()
        node_float = Float(0.0).store()
        node_int = Int(1).store()

        param_type_normal = NodeParamType()
        param_type_scoped = NodeParamType(sub_classes=('aiida.data:core.bool', 'aiida.data:core.float'))

        # For the base NodeParamType all node types should be matched
        assert param_type_normal.convert(str(node_bool.pk), None, None).uuid == node_bool.uuid
        assert param_type_normal.convert(str(node_float.pk), None, None).uuid == node_float.uuid
        assert param_type_normal.convert(str(node_int.pk), None, None).uuid == node_int.uuid

        # The scoped NodeParamType should only match Bool and Float
        assert param_type_scoped.convert(str(node_bool.pk), None, None).uuid == node_bool.uuid
        assert param_type_scoped.convert(str(node_float.pk), None, None).uuid == node_float.uuid

        # The Int should not be found and raise
        with pytest.raises(click.BadParameter):
            param_type_scoped.convert(str(node_int.pk), None, None)
