# -*- coding: utf-8 -*-
"""Tests for the Node ORM class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.orm.data import Data
from aiida.orm.node.process import CalculationNode, WorkflowNode


class TestNodeLinks(AiidaTestCase):
    """Test for linking from and to Node."""

    def setUp(self):
        super(TestNodeLinks, self).setUp()
        self.node_source = CalculationNode()
        self.node_target = Data()

    def test_validate_incoming_ipsum(self):
        """Test the `validate_incoming` method with respect to linking ourselves."""
        with self.assertRaises(ValueError):
            self.node_target.validate_incoming(self.node_target, LinkType.CREATE)

    def test_validate_incoming(self):
        """Test the `validate_incoming` method

        For a generic Node all incoming link types are valid as long as the source is also of type Node and the link
        type is a valid LinkType enum value.
        """
        with self.assertRaises(TypeError):
            self.node_target.validate_incoming(self.node_source, None)

        with self.assertRaises(TypeError):
            self.node_target.validate_incoming(None, LinkType.CREATE)

        with self.assertRaises(TypeError):
            self.node_target.validate_incoming(self.node_source, LinkType.CREATE.value)

    def test_add_incoming_create(self):
        """Nodes can only have a single incoming CREATE link, independent of the source node."""
        source_one = CalculationNode()
        source_two = CalculationNode()
        target = Data()

        target.add_incoming(source_one, LinkType.CREATE, 'link_label')

        # Can only have a single incoming CREATE link
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.CREATE)

        # Even when the source node is different
        with self.assertRaises(ValueError):
            target.validate_incoming(source_two, LinkType.CREATE)

    def test_add_incoming_call_calc(self):
        """Nodes can only have a single incoming CALL_CALC link, independent of the source node."""
        source_one = WorkflowNode()
        source_two = WorkflowNode()
        target = CalculationNode()

        target.add_incoming(source_one, LinkType.CALL_CALC, 'link_label')

        # Can only have a single incoming CALL_CALC link
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.CALL_CALC)

        # Even when the source node is different
        with self.assertRaises(ValueError):
            target.validate_incoming(source_two, LinkType.CALL_CALC)

    def test_add_incoming_call_work(self):
        """Nodes can only have a single incoming CALL_WORK link, independent of the source node."""
        source_one = WorkflowNode()
        source_two = WorkflowNode()
        target = WorkflowNode()

        target.add_incoming(source_one, LinkType.CALL_WORK, 'link_label')

        # Can only have a single incoming CALL_WORK link
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.CALL_WORK)

        # Even when the source node is different
        with self.assertRaises(ValueError):
            target.validate_incoming(source_two, LinkType.CALL_WORK)

    def test_add_incoming_return(self):
        """Nodes can have an infinite amount of incoming RETURN links, as long as (source, label) pair is unique."""
        source_one = WorkflowNode()
        source_two = WorkflowNode()
        target = Data()

        target.add_incoming(source_one, LinkType.RETURN, 'link_label')

        # Can only have a single incoming RETURN link from each source node if the label is not unique
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.RETURN, 'link_label')

        # From another source node or using another label is fine
        target.validate_incoming(source_one, LinkType.RETURN, 'other_label')
        target.validate_incoming(source_two, LinkType.RETURN, 'link_label')

    def test_add_incoming_input_calc(self):
        """Nodes can have an infinite amount of incoming INPUT_CALC links, as long as (source, label) pair is unique."""
        source_one = Data()
        source_two = Data()
        target = CalculationNode()

        target.add_incoming(source_one, LinkType.INPUT_CALC, 'link_label')

        # Can only have a single incoming INPUT_CALC link from each source node if the label is not unique
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.INPUT_CALC, 'link_label')

        # From another source node or using another label is fine
        target.validate_incoming(source_one, LinkType.INPUT_CALC, 'other_label')
        target.validate_incoming(source_two, LinkType.INPUT_CALC, 'link_label')

    def test_add_incoming_input_work(self):
        """Nodes can have an infinite amount of incoming INPUT_WORK links, as long as (source, label) pair is unique."""
        source_one = Data()
        source_two = Data()
        target = WorkflowNode()

        target.add_incoming(source_one, LinkType.INPUT_WORK, 'link_label')

        # Can only have a single incoming INPUT_WORK link from each source node if the label is not unique
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.INPUT_WORK, 'link_label')

        # From another source node or using another label is fine
        target.validate_incoming(source_one, LinkType.INPUT_WORK, 'other_label')
        target.validate_incoming(source_two, LinkType.INPUT_WORK, 'link_label')
