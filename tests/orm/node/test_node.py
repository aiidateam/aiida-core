# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-public-methods
"""Tests for the Node ORM class."""

import os
import tempfile

from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions, LinkType
from aiida.orm import Data, Node, User, CalculationNode, WorkflowNode, load_node
from aiida.orm.utils.links import LinkTriple


class TestNode(AiidaTestCase):
    """Tests for generic node functionality."""

    def setUp(self):
        super().setUp()
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


class TestNodeAttributesExtras(AiidaTestCase):
    """Test for node attributes and extras."""

    def setUp(self):
        super().setUp()
        self.node = Data()

    def test_attributes(self):
        """Test the `Node.attributes` property."""
        original_attribute = {'nested': {'a': 1}}

        self.node.set_attribute('key', original_attribute)
        node_attributes = self.node.attributes
        self.assertEqual(node_attributes['key'], original_attribute)
        node_attributes['key']['nested']['a'] = 2

        self.assertEqual(original_attribute['nested']['a'], 2)

        # Now store the node and verify that `attributes` then returns a deep copy
        self.node.store()
        node_attributes = self.node.attributes

        # We change the returned node attributes but the original attribute should remain unchanged
        node_attributes['key']['nested']['a'] = 3
        self.assertEqual(original_attribute['nested']['a'], 2)

    def test_get_attribute(self):
        """Test the `Node.get_attribute` method."""
        original_attribute = {'nested': {'a': 1}}

        self.node.set_attribute('key', original_attribute)
        node_attribute = self.node.get_attribute('key')
        self.assertEqual(node_attribute, original_attribute)
        node_attribute['nested']['a'] = 2

        self.assertEqual(original_attribute['nested']['a'], 2)

        default = 'default'
        self.assertEqual(self.node.get_attribute('not_existing', default=default), default)
        with self.assertRaises(AttributeError):
            self.node.get_attribute('not_existing')

        # Now store the node and verify that `get_attribute` then returns a deep copy
        self.node.store()
        node_attribute = self.node.get_attribute('key')

        # We change the returned node attributes but the original attribute should remain unchanged
        node_attribute['nested']['a'] = 3
        self.assertEqual(original_attribute['nested']['a'], 2)

        default = 'default'
        self.assertEqual(self.node.get_attribute('not_existing', default=default), default)
        with self.assertRaises(AttributeError):
            self.node.get_attribute('not_existing')

    def test_get_attribute_many(self):
        """Test the `Node.get_attribute_many` method."""
        original_attribute = {'nested': {'a': 1}}

        self.node.set_attribute('key', original_attribute)
        node_attribute = self.node.get_attribute_many(['key'])[0]
        self.assertEqual(node_attribute, original_attribute)
        node_attribute['nested']['a'] = 2

        self.assertEqual(original_attribute['nested']['a'], 2)

        # Now store the node and verify that `get_attribute` then returns a deep copy
        self.node.store()
        node_attribute = self.node.get_attribute_many(['key'])[0]

        # We change the returned node attributes but the original attribute should remain unchanged
        node_attribute['nested']['a'] = 3
        self.assertEqual(original_attribute['nested']['a'], 2)

    def test_set_attribute(self):
        """Test the `Node.set_attribute` method."""
        with self.assertRaises(exceptions.ValidationError):
            self.node.set_attribute('illegal.key', 'value')

        self.node.set_attribute('valid_key', 'value')
        self.node.store()

        with self.assertRaises(exceptions.ModificationNotAllowed):
            self.node.set_attribute('valid_key', 'value')

    def test_set_attribute_many(self):
        """Test the `Node.set_attribute` method."""
        with self.assertRaises(exceptions.ValidationError):
            self.node.set_attribute_many({'illegal.key': 'value', 'valid_key': 'value'})

        self.node.set_attribute_many({'valid_key': 'value'})
        self.node.store()

        with self.assertRaises(exceptions.ModificationNotAllowed):
            self.node.set_attribute_many({'valid_key': 'value'})

    def test_reset_attribute(self):
        """Test the `Node.reset_attribute` method."""
        attributes_before = {'attribute_one': 'value', 'attribute_two': 'value'}
        attributes_after = {'attribute_three': 'value', 'attribute_four': 'value'}
        attributes_illegal = {'attribute.illegal': 'value', 'attribute_four': 'value'}

        self.node.set_attribute_many(attributes_before)
        self.assertEqual(self.node.attributes, attributes_before)
        self.node.reset_attributes(attributes_after)
        self.assertEqual(self.node.attributes, attributes_after)

        with self.assertRaises(exceptions.ValidationError):
            self.node.reset_attributes(attributes_illegal)

        self.node.store()

        with self.assertRaises(exceptions.ModificationNotAllowed):
            self.node.reset_attributes(attributes_after)

    def test_delete_attribute(self):
        """Test the `Node.delete_attribute` method."""
        self.node.set_attribute('valid_key', 'value')
        self.assertEqual(self.node.get_attribute('valid_key'), 'value')
        self.node.delete_attribute('valid_key')

        with self.assertRaises(AttributeError):
            self.node.delete_attribute('valid_key')

        # Repeat with stored node
        self.node.set_attribute('valid_key', 'value')
        self.node.store()

        with self.assertRaises(exceptions.ModificationNotAllowed):
            self.node.delete_attribute('valid_key')

    def test_delete_attribute_many(self):
        """Test the `Node.delete_attribute_many` method."""

    def test_clear_attributes(self):
        """Test the `Node.clear_attributes` method."""
        attributes = {'attribute_one': 'value', 'attribute_two': 'value'}
        self.node.set_attribute_many(attributes)
        self.assertEqual(self.node.attributes, attributes)

        self.node.clear_attributes()
        self.assertEqual(self.node.attributes, {})

        # Repeat for stored node
        self.node.store()

        with self.assertRaises(exceptions.ModificationNotAllowed):
            self.node.clear_attributes()

    def test_attributes_items(self):
        """Test the `Node.attributes_items` generator."""
        attributes = {'attribute_one': 'value', 'attribute_two': 'value'}
        self.node.set_attribute_many(attributes)
        self.assertEqual(dict(self.node.attributes_items()), attributes)

    def test_attributes_keys(self):
        """Test the `Node.attributes_keys` generator."""
        attributes = {'attribute_one': 'value', 'attribute_two': 'value'}
        self.node.set_attribute_many(attributes)
        self.assertEqual(set(self.node.attributes_keys()), set(attributes))

    def test_extras(self):
        """Test the `Node.extras` property."""
        original_extra = {'nested': {'a': 1}}

        self.node.set_extra('key', original_extra)
        node_extras = self.node.extras
        self.assertEqual(node_extras['key'], original_extra)
        node_extras['key']['nested']['a'] = 2

        self.assertEqual(original_extra['nested']['a'], 2)

        # Now store the node and verify that `extras` then returns a deep copy
        self.node.store()
        node_extras = self.node.extras

        # We change the returned node extras but the original extra should remain unchanged
        node_extras['key']['nested']['a'] = 3
        self.assertEqual(original_extra['nested']['a'], 2)

    def test_get_extra(self):
        """Test the `Node.get_extra` method."""
        original_extra = {'nested': {'a': 1}}

        self.node.set_extra('key', original_extra)
        node_extra = self.node.get_extra('key')
        self.assertEqual(node_extra, original_extra)
        node_extra['nested']['a'] = 2

        self.assertEqual(original_extra['nested']['a'], 2)

        default = 'default'
        self.assertEqual(self.node.get_extra('not_existing', default=default), default)
        with self.assertRaises(AttributeError):
            self.node.get_extra('not_existing')

        # Now store the node and verify that `get_extra` then returns a deep copy
        self.node.store()
        node_extra = self.node.get_extra('key')

        # We change the returned node extras but the original extra should remain unchanged
        node_extra['nested']['a'] = 3
        self.assertEqual(original_extra['nested']['a'], 2)

        default = 'default'
        self.assertEqual(self.node.get_extra('not_existing', default=default), default)
        with self.assertRaises(AttributeError):
            self.node.get_extra('not_existing')

    def test_get_extra_many(self):
        """Test the `Node.get_extra_many` method."""
        original_extra = {'nested': {'a': 1}}

        self.node.set_extra('key', original_extra)
        node_extra = self.node.get_extra_many(['key'])[0]
        self.assertEqual(node_extra, original_extra)
        node_extra['nested']['a'] = 2

        self.assertEqual(original_extra['nested']['a'], 2)

        # Now store the node and verify that `get_extra` then returns a deep copy
        self.node.store()
        node_extra = self.node.get_extra_many(['key'])[0]

        # We change the returned node extras but the original extra should remain unchanged
        node_extra['nested']['a'] = 3
        self.assertEqual(original_extra['nested']['a'], 2)

    def test_set_extra(self):
        """Test the `Node.set_extra` method."""
        with self.assertRaises(exceptions.ValidationError):
            self.node.set_extra('illegal.key', 'value')

        self.node.set_extra('valid_key', 'value')
        self.node.store()

        self.node.set_extra('valid_key', 'changed')
        self.assertEqual(load_node(self.node.pk).get_extra('valid_key'), 'changed')

    def test_set_extra_many(self):
        """Test the `Node.set_extra` method."""
        with self.assertRaises(exceptions.ValidationError):
            self.node.set_extra_many({'illegal.key': 'value', 'valid_key': 'value'})

        self.node.set_extra_many({'valid_key': 'value'})
        self.node.store()

        self.node.set_extra_many({'valid_key': 'changed'})
        self.assertEqual(load_node(self.node.pk).get_extra('valid_key'), 'changed')

    def test_reset_extra(self):
        """Test the `Node.reset_extra` method."""
        extras_before = {'extra_one': 'value', 'extra_two': 'value'}
        extras_after = {'extra_three': 'value', 'extra_four': 'value'}
        extras_illegal = {'extra.illegal': 'value', 'extra_four': 'value'}

        self.node.set_extra_many(extras_before)
        self.assertEqual(self.node.extras, extras_before)
        self.node.reset_extras(extras_after)
        self.assertEqual(self.node.extras, extras_after)

        with self.assertRaises(exceptions.ValidationError):
            self.node.reset_extras(extras_illegal)

        self.node.store()

        self.node.reset_extras(extras_after)
        self.assertEqual(load_node(self.node.pk).extras, extras_after)

    def test_delete_extra(self):
        """Test the `Node.delete_extra` method."""
        self.node.set_extra('valid_key', 'value')
        self.assertEqual(self.node.get_extra('valid_key'), 'value')
        self.node.delete_extra('valid_key')

        with self.assertRaises(AttributeError):
            self.node.delete_extra('valid_key')

        # Repeat with stored node
        self.node.set_extra('valid_key', 'value')
        self.node.store()

        self.node.delete_extra('valid_key')
        with self.assertRaises(AttributeError):
            load_node(self.node.pk).get_extra('valid_key')

    def test_delete_extra_many(self):
        """Test the `Node.delete_extra_many` method."""

    def test_clear_extras(self):
        """Test the `Node.clear_extras` method."""
        extras = {'extra_one': 'value', 'extra_two': 'value'}
        self.node.set_extra_many(extras)
        self.assertEqual(self.node.extras, extras)

        self.node.clear_extras()
        self.assertEqual(self.node.extras, {})

        # Repeat for stored node
        self.node.store()

        self.node.clear_extras()
        self.assertEqual(load_node(self.node.pk).extras, {})

    def test_extras_items(self):
        """Test the `Node.extras_items` generator."""
        extras = {'extra_one': 'value', 'extra_two': 'value'}
        self.node.set_extra_many(extras)
        self.assertEqual(dict(self.node.extras_items()), extras)

    def test_extras_keys(self):
        """Test the `Node.extras_keys` generator."""
        extras = {'extra_one': 'value', 'extra_two': 'value'}
        self.node.set_extra_many(extras)
        self.assertEqual(set(self.node.extras_keys()), set(extras))


class TestNodeLinks(AiidaTestCase):
    """Test for linking from and to Node."""

    def setUp(self):
        super().setUp()
        self.node_source = CalculationNode()
        self.node_target = Data()

    def test_get_stored_link_triples(self):
        """Validate the `get_stored_link_triples` method."""
        data = Data().store()
        calculation = CalculationNode()

        calculation.add_incoming(data, LinkType.INPUT_CALC, 'input')
        calculation.store()
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
        target = Data().store()  # Needs to be stored: see `test_validate_outgoing_workflow`

        target.add_incoming(source_one, LinkType.RETURN, 'link_label')

        # Can only have a single incoming RETURN link from each source node if the label is not unique
        with self.assertRaises(ValueError):
            target.validate_incoming(source_one, LinkType.RETURN, 'link_label')

        # From another source node or using another label is fine
        target.validate_incoming(source_one, LinkType.RETURN, 'other_label')
        target.validate_incoming(source_two, LinkType.RETURN, 'link_label')

    def test_validate_outgoing_workflow(self):
        """Verify that attaching an unstored `Data` node with `RETURN` link from a `WorkflowNode` raises.

        This would for example be the case if a user inside a workfunction or work chain creates a new node based on its
        inputs or the outputs returned by another process and tries to attach it as an output. This would the provenance
        of that data node to be lost and should be explicitly forbidden by raising.
        """
        source = WorkflowNode()
        target = Data()

        with self.assertRaises(ValueError):
            target.add_incoming(source, LinkType.RETURN, 'link_label')

    def test_get_incoming(self):
        """Test that `Node.get_incoming` will return stored and cached input links."""
        source_one = Data().store()
        source_two = Data().store()
        target = CalculationNode()

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
        return_one = WorkflowNode()
        return_two = WorkflowNode()
        data = Data().store()  # Needs to be stored: see `test_validate_outgoing_workflow`

        # Verify that adding two return links with the same link label but from different source is allowed
        data.add_incoming(return_one, link_type=LinkType.RETURN, link_label='returned')
        data.add_incoming(return_two, link_type=LinkType.RETURN, link_label='returned')

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
        calc_one_a = CalculationNode()
        calc_one_b = CalculationNode()
        calc_two = CalculationNode()

        # Two calcs using the data with the same label
        calc_one_a.add_incoming(data, link_type=LinkType.INPUT_CALC, link_label='input')
        calc_one_b.add_incoming(data, link_type=LinkType.INPUT_CALC, link_label='input')
        # A different label
        calc_two.add_incoming(data, link_type=LinkType.INPUT_CALC, link_label='the_input')

        calc_one_a.store()
        calc_one_b.store()
        calc_two.store()

        # Retrieve a link when the label is unique
        output_the_input = data.get_outgoing(link_type=LinkType.INPUT_CALC).get_node_by_label('the_input')
        self.assertEqual(output_the_input.pk, calc_two.pk)

        with self.assertRaises(exceptions.MultipleObjectsError):
            data.get_outgoing(link_type=LinkType.INPUT_CALC).get_node_by_label('input')

        with self.assertRaises(exceptions.NotExistent):
            data.get_outgoing(link_type=LinkType.INPUT_CALC).get_node_by_label('some_weird_label')

    def test_tab_completable_properties(self):
        """Test properties to go from one node to a neighboring one"""
        # pylint: disable=too-many-statements
        input1 = Data().store()
        input2 = Data().store()

        top_workflow = WorkflowNode()
        workflow = WorkflowNode()
        calc1 = CalculationNode()
        calc2 = CalculationNode()

        output1 = Data().store()
        output2 = Data().store()

        # The `top_workflow` has two inputs, proxies them to `workflow`, that in turn calls two calculations, passing
        # one data node to each as input, and return the two data nodes returned one by each called calculation
        top_workflow.add_incoming(input1, link_type=LinkType.INPUT_WORK, link_label='a')
        top_workflow.add_incoming(input2, link_type=LinkType.INPUT_WORK, link_label='b')
        top_workflow.store()

        workflow.add_incoming(input1, link_type=LinkType.INPUT_WORK, link_label='a')
        workflow.add_incoming(input2, link_type=LinkType.INPUT_WORK, link_label='b')
        workflow.add_incoming(top_workflow, link_type=LinkType.CALL_WORK, link_label='CALL')
        workflow.store()

        calc1.add_incoming(input1, link_type=LinkType.INPUT_CALC, link_label='input_value')
        calc1.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='CALL')
        calc1.store()
        output1.add_incoming(calc1, link_type=LinkType.CREATE, link_label='result')

        calc2.add_incoming(input2, link_type=LinkType.INPUT_CALC, link_label='input_value')
        calc2.add_incoming(workflow, link_type=LinkType.CALL_CALC, link_label='CALL')
        calc2.store()
        output2.add_incoming(calc2, link_type=LinkType.CREATE, link_label='result')

        output1.add_incoming(workflow, link_type=LinkType.RETURN, link_label='result_a')
        output2.add_incoming(workflow, link_type=LinkType.RETURN, link_label='result_b')
        output1.add_incoming(top_workflow, link_type=LinkType.RETURN, link_label='result_a')
        output2.add_incoming(top_workflow, link_type=LinkType.RETURN, link_label='result_b')

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
            _ = workflow.outputs.some_label


# Clearing the DB is needed because other parts of the tests (not using
# the fixture infrastructure) delete the User.
def test_store_from_cache(clear_database_before_test):  # pylint: disable=unused-argument
    """
    Regression test for storing a Node with (nested) repository
    content with caching.
    """
    data = Data()
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = os.path.join(tmpdir, 'directory')
        os.makedirs(dir_path)
        with open(os.path.join(dir_path, 'file'), 'w') as file:
            file.write('content')
        data.put_object_from_tree(tmpdir)

    data.store()

    clone = data.clone()
    clone._store_from_cache(data, with_transaction=True)  # pylint: disable=protected-access

    assert clone.is_stored
    assert clone.get_cache_source() == data.uuid
    assert data.get_hash() == clone.get_hash()
