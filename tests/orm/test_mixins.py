###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the ORM mixin classes."""

import pytest

from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.orm import CalculationNode, Int
from aiida.orm.utils.mixins import Sealable


class TestSealable:
    """Tests for the `Sealable` mixin class."""

    @staticmethod
    def test_change_updatable_attrs_after_store():
        """Verify that a Sealable node can alter updatable attributes even after storing."""
        node = CalculationNode().store()

        for attr in CalculationNode._updatable_attributes:
            if attr != Sealable.SEALED_KEY:
                node.base.attributes.set(attr, 'a')

    def test_validate_incoming_sealed(self):
        """Verify that trying to add a link to a sealed node will raise."""
        data = Int(1).store()
        node = CalculationNode().store()
        node.seal()

        with pytest.raises(exceptions.ModificationNotAllowed):
            node.base.links.validate_incoming(data, link_type=LinkType.INPUT_CALC, link_label='input')

    def test_validate_outgoing_sealed(self):
        """Verify that trying to add a link from a sealed node will raise."""
        data = Int(1).store()
        node = CalculationNode().store()
        node.seal()

        with pytest.raises(exceptions.ModificationNotAllowed):
            node.base.links.validate_outgoing(data, link_type=LinkType.CREATE, link_label='create')
