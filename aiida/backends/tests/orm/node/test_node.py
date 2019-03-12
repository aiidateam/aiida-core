# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the Node ORM class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions, LinkType
from aiida.orm import Data, Node, User, CalculationNode, WorkflowNode
from aiida.orm.utils.links import LinkTriple


class TestNodeLinks(AiidaTestCase):
    """Test for linking from and to Node."""

    def setUp(self):
        super(TestNodeLinks, self).setUp()
        self.node_source = CalculationNode()
        self.node_target = Data()
        self.user = User.objects.get_default()

    def test_repository_garbage_collection(self):
        """Verify that the repository sandbox folder is cleaned after the node instance is garbage collected."""
        node = Data()
        dirpath = node._repository._get_temp_folder().abspath  # pylint: disable=protected-access

        self.assertTrue(os.path.isdir(dirpath))
        del node
        self.assertFalse(os.path.isdir(dirpath))

    def test_computer_user_immutability(self):
        """Test that computer and user of a node are immutable after storing."""
        node = Data().store()

        with self.assertRaises(exceptions.ModificationNotAllowed):
            node.computer = self.computer

        with self.assertRaises(exceptions.ModificationNotAllowed):
            node.user = self.user

    def test_get_stored_link_triples(self):
        """Validate the `get_stored_link_triples` method."""
        data = Data().store()
        calculation = CalculationNode().store()

        calculation.add_incoming(data, LinkType.INPUT_CALC, 'input')
        stored_triples = calculation.get_stored_link_triples()

        self.assertEqual(len(stored_triples), 1)

        link_triple = stored_triples[0]

        # Verify the type and value of the tuple elements
        self.assertTrue(isinstance(link_triple, LinkTriple))
        self.assertTrue(isinstance(link_triple.node, Node))
        self.assertTrue(isinstance(link_triple.link_type, LinkType))
        self.assertEqual(link_triple.node.uuid, data.uuid)
        self.assertEqual(link_triple.link_type, LinkType.INPUT_CALC)
        self.assertEqual(link_triple.link_label, 'input')

    def test_validate_incoming_ipsum(self):
        """Test the `validate_incoming` method with respect to linking ourselves."""
        with self.assertRaises(ValueError):
            self.node_target.validate_incoming(self.node_target, LinkType.CREATE, 'link_label')

    def test_validate_incoming(self):
        """Test the `validate_incoming` method

        For a generic Node all incoming link types are valid as long as the source is also of type Node and the link
        type is a valid LinkType enum value.
        """
        with self.assertRaises(TypeError):
            self.node_target.validate_incoming(self.node_source, None, 'link_label')

        with self.assertRaises(TypeError):
            self.node_target.validate_incoming(None, LinkType.CREATE, 'link_label')

        with self.assertRaises(TypeError):
            self.node_target.validate_incoming(self.node_source, LinkType.CREATE.value, 'link_label')

    def test_add_incoming_create(self):
        """Nodes can only have a single incoming CREATE link, independent of the source node."""
        source_one = CalculationNode()
        source_two = CalculationNode()
        target = Data()

        target.add_incoming(source_one, LinkType.CREATE, 'link_label')

        # Can only have a single incoming CREATE link
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.CREATE, 'link_label')

        # Even when the source node is different
        with self.assertRaises(ValueError):
            target.validate_incoming(source_two, LinkType.CREATE, 'link_label')

        # Or when the link label is different
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.CREATE, 'other_label')

    def test_add_incoming_call_calc(self):
        """Nodes can only have a single incoming CALL_CALC link, independent of the source node."""
        source_one = WorkflowNode()
        source_two = WorkflowNode()
        target = CalculationNode()

        target.add_incoming(source_one, LinkType.CALL_CALC, 'link_label')

        # Can only have a single incoming CALL_CALC link
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.CALL_CALC, 'link_label')

        # Even when the source node is different
        with self.assertRaises(ValueError):
            target.validate_incoming(source_two, LinkType.CALL_CALC, 'link_label')

        # Or when the link label is different
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.CALL_CALC, 'other_label')

    def test_add_incoming_call_work(self):
        """Nodes can only have a single incoming CALL_WORK link, independent of the source node."""
        source_one = WorkflowNode()
        source_two = WorkflowNode()
        target = WorkflowNode()

        target.add_incoming(source_one, LinkType.CALL_WORK, 'link_label')

        # Can only have a single incoming CALL_WORK link
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.CALL_WORK, 'link_label')

        # Even when the source node is different
        with self.assertRaises(ValueError):
            target.validate_incoming(source_two, LinkType.CALL_WORK, 'link_label')

        # Or when the link label is different
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.CALL_WORK, 'other_label')

    def test_add_incoming_input_calc(self):
        """Nodes can have an infinite amount of incoming INPUT_CALC links, as long as the link pair is unique."""
        source_one = Data()
        source_two = Data()
        target = CalculationNode()

        target.add_incoming(source_one, LinkType.INPUT_CALC, 'link_label')

        # Can only have a single incoming INPUT_CALC link from each source node if the label is not unique
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.INPUT_CALC, 'link_label')

        # Using another link label is fine
        target.validate_incoming(source_one, LinkType.INPUT_CALC, 'other_label')

        # However, using the same link, even from another node is illegal
        with self.assertRaises(ValueError):
            target.validate_incoming(source_two, LinkType.INPUT_CALC, 'link_label')

    def test_add_incoming_input_work(self):
        """Nodes can have an infinite amount of incoming INPUT_WORK links, as long as the link pair is unique."""
        source_one = Data()
        source_two = Data()
        target = WorkflowNode()

        target.add_incoming(source_one, LinkType.INPUT_WORK, 'link_label')

        # Can only have a single incoming INPUT_WORK link from each source node if the label is not unique
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.INPUT_WORK, 'link_label')

        # Using another link label is fine
        target.validate_incoming(source_one, LinkType.INPUT_WORK, 'other_label')

        # However, using the same link, even from another node is illegal
        with self.assertRaises(ValueError):
            target.validate_incoming(source_two, LinkType.INPUT_WORK, 'link_label')

    def test_add_incoming_return(self):
        """Nodes can have an infinite amount of incoming RETURN links, as long as the link triple is unique."""
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

    def test_get_incoming(self):
        """Test that `Node.get_incoming` will return stored and cached input links."""
        source_one = Data().store()
        source_two = Data()
        target = CalculationNode().store()

        target.add_incoming(source_one, LinkType.INPUT_CALC, 'link_one')
        target.add_incoming(source_two, LinkType.INPUT_CALC, 'link_two')

        # Without link type
        incoming_nodes = target.get_incoming().all()
        incoming_uuids = sorted([neighbor.node.uuid for neighbor in incoming_nodes])
        self.assertEqual(incoming_uuids, sorted([source_one.uuid, source_two.uuid]))

        # Using a single link type
        incoming_nodes = target.get_incoming(link_type=LinkType.INPUT_CALC).all()
        incoming_uuids = sorted([neighbor.node.uuid for neighbor in incoming_nodes])
        self.assertEqual(incoming_uuids, sorted([source_one.uuid, source_two.uuid]))

        # Using a link type tuple
        incoming_nodes = target.get_incoming(link_type=(LinkType.INPUT_CALC, LinkType.INPUT_WORK)).all()
        incoming_uuids = sorted([neighbor.node.uuid for neighbor in incoming_nodes])
        self.assertEqual(incoming_uuids, sorted([source_one.uuid, source_two.uuid]))

    def test_node_indegree_unique_pair(self):
        """Test that the validation of links with indegree `unique_pair` works correctly

        The example here is a `DataNode` that has two incoming links with the same label, but with different types.
        This is legal and should pass validation.
        """
        caller = WorkflowNode().store()
        data = Data().store()
        called = CalculationNode()

        # Verify that adding two incoming links with the same link label but different type is allowed
        called.add_incoming(caller, link_type=LinkType.CALL_CALC, link_label='call')
        called.add_incoming(data, link_type=LinkType.INPUT_CALC, link_label='call')
        called.store()

        uuids_incoming = set(node.uuid for node in called.get_incoming().all_nodes())
        uuids_expected = set([caller.uuid, data.uuid])
        self.assertEqual(uuids_incoming, uuids_expected)

    def test_node_indegree_unique_triple(self):
        """Test that the validation of links with indegree `unique_triple` works correctly

        The example here is a `DataNode` that has two incoming RETURN links with the same label, but from different
        source nodes. This is legal and should pass validation.
        """
        return_one = WorkflowNode().store()
        return_two = WorkflowNode().store()
        data = Data()

        # Verify that adding two return links with the same link label but from different source is allowed
        data.add_incoming(return_one, link_type=LinkType.RETURN, link_label='return')
        data.add_incoming(return_two, link_type=LinkType.RETURN, link_label='return')
        data.store()

        uuids_incoming = set(node.uuid for node in data.get_incoming().all_nodes())
        uuids_expected = set([return_one.uuid, return_two.uuid])
        self.assertEqual(uuids_incoming, uuids_expected)

    def test_node_outdegree_unique_triple(self):
        """Test that the validation of links with outdegree `unique_triple` works correctly

        The example here is a `CalculationNode` that has two outgoing CREATE links with the same label, but to different
        target nodes. This is legal and should pass validation.
        """
        creator = CalculationNode().store()
        data_one = Data()
        data_two = Data()

        # Verify that adding two create links with the same link label but to different target is allowed from the
        # perspective of the source node (the CalculationNode in this case)
        data_one.add_incoming(creator, link_type=LinkType.CREATE, link_label='create')
        data_two.add_incoming(creator, link_type=LinkType.CREATE, link_label='create')
        data_one.store()
        data_two.store()

        uuids_outgoing = set(node.uuid for node in creator.get_outgoing().all_nodes())
        uuids_expected = set([data_one.uuid, data_two.uuid])
        self.assertEqual(uuids_outgoing, uuids_expected)

    def test_get_node_by_label(self):
        """Test the get_node_by_label() method of the `LinkManager`

        In particular, check both the it returns the correct values, but also that it raises the expected
        exceptions where appropriate (missing link with a given label, or more than one link)
        """
        data = Data().store()
        calc_one_a = CalculationNode().store()
        calc_one_b = CalculationNode().store()
        calc_two = CalculationNode().store()

        # Two calcs using the data with the same label
        calc_one_a.add_incoming(data, link_type=LinkType.INPUT_CALC, link_label='input')
        calc_one_b.add_incoming(data, link_type=LinkType.INPUT_CALC, link_label='input')
        # A different label
        calc_two.add_incoming(data, link_type=LinkType.INPUT_CALC, link_label='the_input')

        # Retrieve a link when the label is unique
        output_the_input = data.get_outgoing(link_type=LinkType.INPUT_CALC).get_node_by_label('the_input')
        self.assertEqual(output_the_input.pk, calc_two.pk)

        with self.assertRaises(exceptions.MultipleObjectsError):
            data.get_outgoing(link_type=LinkType.INPUT_CALC).get_node_by_label('input')

        with self.assertRaises(exceptions.NotExistent):
            data.get_outgoing(link_type=LinkType.INPUT_CALC).get_node_by_label('some_weird_label')

    def test_tab_completable_properties(self):
        """Test properties to go from one node to a neighboring one"""
        input1 = Data().store()
        input2 = Data().store()

        top_workflow = WorkflowNode().store()
        workflow = WorkflowNode().store()
        calc1 = CalculationNode().store()
        calc2 = CalculationNode().store()

        output1 = Data().store()
        output2 = Data().store()

        # top_workflow has two inputs, proxies them to workflow, that in turn
        # calls two calcs (passing 1 data to each),
        # and return the two data nodes returned one by each called calculation
        top_workflow.add_incoming(input1, link_type=LinkType.INPUT_WORK, link_label='a')
        top_workflow.add_incoming(input2, link_type=LinkType.INPUT_WORK, link_label='b')

        workflow.add_incoming(input1, link_type=LinkType.INPUT_WORK, link_label='a')
        workflow.add_incoming(input2, link_type=LinkType.INPUT_WORK, link_label='b')
        workflow.add_incoming(top_workflow, link_type=LinkType.CALL_WORK, link_label='CALL')

        calc1.add_incoming(input1, link_type=LinkType.INPUT_CALC, link_label='input_value')
        calc1.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='CALL')
        output1.add_incoming(calc1, link_type=LinkType.CREATE, link_label='result')

        calc2.add_incoming(input2, link_type=LinkType.INPUT_CALC, link_label='input_value')
        calc2.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='CALL')
        output2.add_incoming(calc2, link_type=LinkType.CREATE, link_label='result')

        output1.add_incoming(workflow, link_type=LinkType.RETURN, link_label='result_a')
        output2.add_incoming(workflow, link_type=LinkType.RETURN, link_label='result_b')
        output1.add_incoming(top_workflow, link_type=LinkType.RETURN, link_label='result_a')
        output2.add_incoming(top_workflow, link_type=LinkType.RETURN, link_label='result_b')

        ## Now we test the methods
        # creator
        self.assertEqual(output1.creator.pk, calc1.pk)
        self.assertEqual(output2.creator.pk, calc2.pk)

        # caller (for calculations)
        self.assertEqual(calc1.caller.pk, workflow.pk)
        self.assertEqual(calc2.caller.pk, workflow.pk)

        # caller (for workflows)
        self.assertEqual(workflow.caller.pk, top_workflow.pk)

        # .inputs for calculations
        self.assertEqual(calc1.inputs.input_value.pk, input1.pk)
        self.assertEqual(calc2.inputs.input_value.pk, input2.pk)
        with self.assertRaises(exceptions.NotExistent):
            _ = calc1.inputs.some_label

        # .inputs for workflows
        self.assertEqual(top_workflow.inputs.a.pk, input1.pk)
        self.assertEqual(top_workflow.inputs.b.pk, input2.pk)
        self.assertEqual(workflow.inputs.a.pk, input1.pk)
        self.assertEqual(workflow.inputs.b.pk, input2.pk)
        with self.assertRaises(exceptions.NotExistent):
            _ = workflow.inputs.some_label

        # .outputs for calculations
        self.assertEqual(calc1.outputs.result.pk, output1.pk)
        self.assertEqual(calc2.outputs.result.pk, output2.pk)
        with self.assertRaises(exceptions.NotExistent):
            _ = calc1.outputs.some_label

        # .outputs for workflows
        self.assertEqual(top_workflow.outputs.result_a.pk, output1.pk)
        self.assertEqual(top_workflow.outputs.result_b.pk, output2.pk)
        self.assertEqual(workflow.outputs.result_a.pk, output1.pk)
        self.assertEqual(workflow.outputs.result_b.pk, output2.pk)
        with self.assertRaises(exceptions.NotExistent):
            _ = workflow.outputs.some_label  #  noqa
