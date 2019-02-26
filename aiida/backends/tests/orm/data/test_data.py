# -*- coding: utf-8 -*-
"""Tests for the Dat ORM class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.orm import CalculationNode, Data


class TestDataNodeLinks(AiidaTestCase):
    """Test for linking from and to Data nodes."""

    def setUp(self):
        super(TestDataNodeLinks, self).setUp()
        self.calculation_node_source = CalculationNode()
        self.calculation_node_target = CalculationNode()
        self.data_node_source = Data()
        self.data_node_target = Data()

    def test_validate_incoming(self):
        """Test the `validate_incoming` method

        For a Data node all incoming link types are valid as long as the source is also of type Node and the link
        type is a valid LinkType enum value.
        """
        for link_type in LinkType:

            # From Data nodes only CALL_CALC links are valid
            if link_type in (LinkType.CALL_CALC,):
                self.calculation_node_target.validate_incoming(self.calculation_node_source, link_type, 'label')
            else:
                with self.assertRaises(ValueError):
                    self.calculation_node_target.validate_incoming(self.calculation_node_source, link_type, 'label')

            # From Data nodes only INPUT_CALC links are valid
            if link_type in (LinkType.INPUT_CALC,):
                self.calculation_node_target.validate_incoming(self.data_node_source, link_type, 'label')
            else:
                with self.assertRaises(ValueError):
                    self.calculation_node_target.validate_incoming(self.data_node_source, link_type, 'label')

    def test_validate_outgoing(self):
        """Test the `validate_outgoing` method

        For a Data node all outgoing link types are valid as long as the source is also of type Node and the link
        type is a valid LinkType enum value.
        """
        for link_type in LinkType:

            # Into CalculationNodes only CALL_CALC links are valid
            if link_type in (LinkType.CALL_CALC,):
                self.calculation_node_source.validate_outgoing(self.calculation_node_target, link_type, 'label')
            else:
                with self.assertRaises(ValueError):
                    self.calculation_node_source.validate_outgoing(self.calculation_node_target, link_type, 'label')

            # Into Data nodes only CREATE links are valid
            if link_type in (LinkType.CREATE,):
                self.calculation_node_source.validate_outgoing(self.data_node_target, link_type, 'label')
            else:
                with self.assertRaises(ValueError):
                    self.calculation_node_source.validate_outgoing(self.data_node_target, link_type, 'label')
