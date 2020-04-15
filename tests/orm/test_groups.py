# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the Group ORM class."""
import pytest

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

    def test_clear(self):
        """Test the `clear` method to remove all nodes."""
        node_01 = orm.Data().store()
        node_02 = orm.Data().store()
        node_03 = orm.Data().store()
        nodes = [node_01, node_02, node_03]
        group = orm.Group(label='test_clear_nodes').store()

        # Add initial nodes
        group.add_nodes(nodes)
        self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))

        group.clear()
        self.assertEqual(list(group.nodes), [])

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


class TestGroupsSubclasses(AiidaTestCase):
    """Test rules around creating `Group` subclasses."""

    def setUp(self):
        """Remove all existing Groups."""
        for group in orm.Group.objects.all():
            orm.Group.objects.delete(group.id)

    @staticmethod
    def test_creation_registered():
        """Test rules around creating registered `Group` subclasses."""
        group = orm.AutoGroup('some-label')
        assert isinstance(group, orm.AutoGroup)
        assert group.type_string == 'core.auto'

        group, _ = orm.AutoGroup.objects.get_or_create('some-auto-group')
        assert isinstance(group, orm.AutoGroup)
        assert group.type_string == 'core.auto'

    @staticmethod
    def test_loading():
        """Test that loading instances from the database returns the correct subclass of `Group`."""
        group = orm.Group('normal-group').store()
        loaded = orm.load_group(group.pk)
        assert isinstance(loaded, orm.Group)

        group = orm.AutoGroup('auto-group').store()
        loaded = orm.load_group(group.pk)
        assert isinstance(group, orm.AutoGroup)

    @staticmethod
    def test_creation_unregistered():
        """Test rules around creating `Group` subclasses without a registered entry point."""

        # Defining an unregistered subclas should issue a warning and its type string should be set to `None`
        with pytest.warns(UserWarning):

            class SubGroup(orm.Group):
                pass

        assert SubGroup._type_string is None  # pylint: disable=protected-access

        # Creating an instance is allowed
        instance = SubGroup(label='subgroup')
        assert instance._type_string is None  # pylint: disable=protected-access

        # Storing the instance, however, is forbidden and should raise
        with pytest.raises(exceptions.StoringNotAllowed):
            instance.store()

    @staticmethod
    def test_loading_unregistered():
        """Test rules around loading `Group` subclasses without a registered entry point.

        Storing instances of unregistered subclasses is not allowed so we have to create one sneakily by instantiating
        a normal group and manipulating the type string directly on the database model.
        """
        group = orm.Group(label='group')
        group.backend_entity.dbmodel.type_string = 'unregistered.subclass'
        group.store()

        with pytest.warns(UserWarning):
            loaded = orm.load_group(group.pk)

        assert isinstance(loaded, orm.Group)

    @staticmethod
    def test_explicit_type_string():
        """Test that passing explicit `type_string` to `Group` constructor is still possible despite being deprecated.

        Both constructing a group while passing explicit `type_string` as well as loading a group with unregistered
        type string should emit a warning, but it should be possible.
        """
        type_string = 'data.potcar'  # An unregistered custom type string

        with pytest.warns(UserWarning):
            group = orm.Group(label='group', type_string=type_string)

        group.store()
        assert group.type_string == type_string

        with pytest.warns(UserWarning):
            loaded = orm.Group.get(label=group.label, type_string=type_string)

        assert isinstance(loaded, orm.Group)
        assert loaded.pk == group.pk
        assert loaded.type_string == group.type_string

        queried = orm.QueryBuilder().append(orm.Group, filters={'id': group.pk, 'type_string': type_string}).one()[0]
        assert isinstance(queried, orm.Group)
        assert queried.pk == group.pk
        assert queried.type_string == group.type_string

    @staticmethod
    def test_querying():
        """Test querying for groups with and without subclassing."""
        orm.Group(label='group').store()
        orm.AutoGroup(label='auto-group').store()

        # Fake a subclass by manually setting the type string
        group = orm.Group(label='custom-group')
        group.backend_entity.dbmodel.type_string = 'custom.group'
        group.store()

        assert orm.QueryBuilder().append(orm.AutoGroup).count() == 1
        assert orm.QueryBuilder().append(orm.AutoGroup, subclassing=False).count() == 1
        assert orm.QueryBuilder().append(orm.Group, subclassing=False).count() == 1
        assert orm.QueryBuilder().append(orm.Group).count() == 3
        assert orm.QueryBuilder().append(orm.Group, filters={'type_string': 'custom.group'}).count() == 1

    @staticmethod
    def test_querying_node_subclasses():
        """Test querying for groups with multiple types for nodes it contains."""
        group = orm.Group(label='group').store()
        data_int = orm.Int().store()
        data_str = orm.Str().store()
        data_bool = orm.Bool().store()

        group.add_nodes([data_int, data_str, data_bool])

        builder = orm.QueryBuilder().append(orm.Group, tag='group')
        builder.append((orm.Int, orm.Str), with_group='group', project='id')
        results = [entry[0] for entry in builder.iterall()]

        assert len(results) == 2
        assert data_int.pk in results
        assert data_str.pk in results
        assert data_bool.pk not in results

    @staticmethod
    def test_query_with_group():
        """Docs."""
        group = orm.Group(label='group').store()
        data = orm.Data().store()

        group.add_nodes([data])

        builder = orm.QueryBuilder().append(orm.Data, filters={
            'id': data.pk
        }, tag='data').append(orm.Group, with_node='data')

        loaded = builder.one()[0]

        assert loaded.pk == group.pk
