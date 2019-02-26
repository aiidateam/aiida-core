# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the ORM mixin classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.orm import Int, CalculationNode
from aiida.orm.utils.mixins import Sealable


class TestSealable(AiidaTestCase):
    """Tests for the `Sealable` mixin class."""

    @staticmethod
    def test_change_updatable_attrs_after_store():
        """Verify that a Sealable node can alter updatable attributes even after storing."""

        node = CalculationNode().store()

        for attr in CalculationNode._updatable_attributes:  # pylint: disable=protected-access,not-an-iterable
            if attr != Sealable.SEALED_KEY:
                node.set_attribute(attr, 'a')

    def test_validate_incoming_sealed(self):
        """Verify that trying to add a link to a sealed node will raise."""
        data = Int(1).store()
        node = CalculationNode().store()
        node.seal()

        with self.assertRaises(exceptions.ModificationNotAllowed):
            node.validate_incoming(data, link_type=LinkType.INPUT_CALC, link_label='input')

    def test_validate_outgoing_sealed(self):
        """Verify that trying to add a link from a sealed node will raise."""
        data = Int(1).store()
        node = CalculationNode().store()
        node.seal()

        with self.assertRaises(exceptions.ModificationNotAllowed):
            node.validate_outgoing(data, link_type=LinkType.CREATE, link_label='create')
