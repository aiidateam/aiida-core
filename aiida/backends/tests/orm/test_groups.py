# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the Group ORM class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions


class TestGroups(AiidaTestCase):
    """Test backend entities and their collections"""

    def setUp(self):
        """Remove all existing Groups."""
        for group in orm.Group.objects.all():
            orm.Group.objects.delete(group.id)

    def test_count(self):
        """Test the `count` method."""
        node_00 = orm.Data().store()
        node_01 = orm.Data().store()
        nodes = [node_00, node_01]

        group = orm.Group(label='label', description='description').store()
        group.add_nodes(nodes)

        self.assertEqual(group.count(), len(nodes))

    def test_creation(self):
        """Test the creation of Groups."""
        node = orm.Data()
        stored_node = orm.Data().store()

        group = orm.Group(label='testgroup')

        with self.assertRaises(exceptions.ModificationNotAllowed):
            # group unstored
            group.add_nodes(node)

        with self.assertRaises(exceptions.ModificationNotAllowed):
            # group unstored
            group.add_nodes(stored_node)

        group.store()

        with self.assertRaises(ValueError):
            # node unstored
            group.add_nodes(node)

        group.add_nodes(stored_node)

        nodes = list(group.nodes)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].pk, stored_node.pk)

    def test_node_iterator(self):
        """Test the indexing and slicing functionality of the node iterator."""
        node_00 = orm.Data().store()
        node_01 = orm.Data().store()
        node_02 = orm.Data().store()
        node_03 = orm.Data().store()
        nodes = [node_00, node_01, node_02, node_03]

        group = orm.Group(label='label', description='description').store()
        group.add_nodes(nodes)

        # Indexing
        node_indexed = group.nodes[0]
        self.assertTrue(isinstance(node_indexed, orm.Data))
        self.assertIn(node_indexed.uuid, [node.uuid for node in nodes])

        # Slicing
        nodes_sliced = group.nodes[1:3]
        self.assertTrue(isinstance(nodes_sliced, list))
        self.assertEqual(len(nodes_sliced), 2)
        self.assertTrue(all([isinstance(node, orm.Data) for node in nodes_sliced]))
        self.assertTrue(all([node.uuid in set(node.uuid for node in nodes) for node in nodes_sliced]))

    def test_description(self):
        """Test the update of the description both for stored and unstored groups."""
        node = orm.Data().store()

        group_01 = orm.Group(label='testgroupdescription1', description='group_01').store()
        group_01.add_nodes(node)

        group_02 = orm.Group(label='testgroupdescription2', description='group_02')

        # Preliminary checks
        self.assertTrue(group_01.is_stored)
        self.assertFalse(group_02.is_stored)
        self.assertEqual(group_01.description, 'group_01')
        self.assertEqual(group_02.description, 'group_02')

        # Change
        group_01.description = 'new1'
        group_02.description = 'new2'

        # Test that the groups remained in their proper stored state and that
        # the description was updated
        self.assertTrue(group_01.is_stored)
        self.assertFalse(group_02.is_stored)
        self.assertEqual(group_01.description, 'new1')
        self.assertEqual(group_02.description, 'new2')

        # Store group_02 and check that the description is OK
        group_02.store()
        self.assertTrue(group_02.is_stored)
        self.assertEqual(group_02.description, 'new2')

    def test_add_nodes(self):
        """Test different ways of adding nodes."""
        node_01 = orm.Data().store()
        node_02 = orm.Data().store()
        node_03 = orm.Data().store()
        nodes = [node_01, node_02, node_03]

        group = orm.Group(label='test_adding_nodes').store()
        # Single node
        group.add_nodes(node_01)
        # List of nodes
        group.add_nodes([node_02, node_03])

        # Check
        self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))

        # Try to add a node that is already present: there should be no problem
        group.add_nodes(node_01)
        self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))

    def test_remove_nodes(self):
        """Test node removal."""
        node_01 = orm.Data().store()
        node_02 = orm.Data().store()
        node_03 = orm.Data().store()
        node_04 = orm.Data().store()
        nodes = [node_01, node_02, node_03]
        group = orm.Group(label='test_remove_nodes').store()

        # Add initial nodes
        group.add_nodes(nodes)
        self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))

        # Remove a node that is not in the group: nothing should happen
        group.remove_nodes(node_04)
        self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))

        # Remove one orm.Node
        nodes.remove(node_03)
        group.remove_nodes(node_03)
        self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))

        # Remove a list of Nodes and check
        nodes.remove(node_01)
        nodes.remove(node_02)
        group.remove_nodes([node_01, node_02])
        self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))

    def test_name_desc(self):
        """Test Group description."""
        group = orm.Group(label='testgroup2', description='some desc')
        self.assertEqual(group.label, 'testgroup2')
        self.assertEqual(group.description, 'some desc')
        self.assertTrue(group.is_user_defined)
        group.store()

        # Same checks after storing
        self.assertEqual(group.label, 'testgroup2')
        self.assertTrue(group.is_user_defined)
        self.assertEqual(group.description, 'some desc')

        # To avoid to find it in further tests
        orm.Group.objects.delete(group.pk)

    def test_delete(self):
        """Test Group deletion."""
        node = orm.Data().store()
        group = orm.Group(label='testgroup3', description='some other desc').store()

        group_copy = orm.Group.get(label='testgroup3')
        self.assertEqual(group.uuid, group_copy.uuid)

        group.add_nodes(node)
        self.assertEqual(len(group.nodes), 1)

        orm.Group.objects.delete(group.pk)

        with self.assertRaises(exceptions.NotExistent):
            # The group does not exist anymore
            orm.Group.get(label='testgroup3')

    def test_rename(self):
        """Test the renaming of a Group."""
        label_original = 'groupie'
        label_changed = 'nogroupie'

        group = orm.Group(label=label_original, description='I will be renamed')

        # Check name changes work before storing
        self.assertEqual(group.label, label_original)
        group.label = label_changed
        self.assertEqual(group.label, label_changed)

        # Revert the name to its original and store it
        group.label = label_original
        group.store()

        # Check name changes work after storing
        self.assertEqual(group.label, label_original)
        group.label = label_changed
        self.assertEqual(group.label, label_changed)

    def test_rename_existing(self):
        """Test that renaming to an already existing name is not permitted."""
        label_group_a = 'group_a'
        label_group_b = 'group_b'

        orm.Group(label=label_group_a, description='I am the Original G').store()

        # Before storing everything should be fine
        group_b = orm.Group(label=label_group_a, description='They will try to rename me')

        # Storing for duplicate group name should trigger UniquenessError
        with self.assertRaises(exceptions.IntegrityError):
            group_b.store()

        # Reverting to unique name before storing
        group_b.label = label_group_b
        group_b.store()

        # After storing name change to existing should raise
        with self.assertRaises(exceptions.IntegrityError):
            group_b.label = label_group_a

    def test_group_uuid_hashing_for_querybuidler(self):
        """QueryBuilder results should be reusable and shouldn't brake hashing."""
        group = orm.Group(label='test_group')
        group.store()

        # Search for the UUID of the stored group
        builder = orm.QueryBuilder()
        builder.append(orm.Group, project=['uuid'], filters={'label': {'==': 'test_group'}})
        [uuid] = builder.first()

        # Look the node with the previously returned UUID
        builder = orm.QueryBuilder()
        builder.append(orm.Group, project=['id'], filters={'uuid': {'==': uuid}})

        # Check that the query doesn't fail
        builder.all()

        # And that the results are correct
        self.assertEqual(builder.count(), 1)
        self.assertEqual(builder.first()[0], group.id)
