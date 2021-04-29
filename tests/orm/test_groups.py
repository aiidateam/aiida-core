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

        # Removing it as other methods might get a warning instead
        group_pk = group.pk
        del group
        orm.Group.objects.delete(id=group_pk)

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

        # Removing it as other methods might get a warning instead
        group_pk = group.pk
        del group
        orm.Group.objects.delete(id=group_pk)

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
        """Test that querying a data node in a group works."""
        group = orm.Group(label='group').store()
        data = orm.Data().store()

        group.add_nodes([data])

        builder = orm.QueryBuilder().append(orm.Data, filters={
            'id': data.pk
        }, tag='data').append(orm.Group, with_node='data')

        loaded = builder.one()[0]

        assert loaded.pk == group.pk


class TestGroupExtras(AiidaTestCase):
    """Test the property and methods of group extras."""

    def setUp(self):
        super().setUp()
        for group in orm.Group.objects.all():
            orm.Group.objects.delete(group.id)
        self.group = orm.Group('test_extras')

    def test_extras(self):
        """Test the `Group.extras` property."""
        original_extra = {'nested': {'a': 1}}

        self.group.set_extra('key', original_extra)
        group_extras = self.group.extras
        self.assertEqual(group_extras['key'], original_extra)
        group_extras['key']['nested']['a'] = 2

        self.assertEqual(original_extra['nested']['a'], 2)

        # Now store the group and verify that `extras` then returns a deep copy
        self.group.store()
        group_extras = self.group.extras

        # We change the returned group extras but the original extra should remain unchanged
        group_extras['key']['nested']['a'] = 3
        self.assertEqual(original_extra['nested']['a'], 2)

    def test_get_extra(self):
        """Test the `Group.get_extra` method."""
        original_extra = {'nested': {'a': 1}}

        self.group.set_extra('key', original_extra)
        group_extra = self.group.get_extra('key')
        self.assertEqual(group_extra, original_extra)
        group_extra['nested']['a'] = 2

        self.assertEqual(original_extra['nested']['a'], 2)

        default = 'default'
        self.assertEqual(self.group.get_extra('not_existing', default=default), default)
        with self.assertRaises(AttributeError):
            self.group.get_extra('not_existing')

        # Now store the group and verify that `get_extra` then returns a deep copy
        self.group.store()
        group_extra = self.group.get_extra('key')

        # We change the returned group extras but the original extra should remain unchanged
        group_extra['nested']['a'] = 3
        self.assertEqual(original_extra['nested']['a'], 2)

        default = 'default'
        self.assertEqual(self.group.get_extra('not_existing', default=default), default)
        with self.assertRaises(AttributeError):
            self.group.get_extra('not_existing')

    def test_get_extra_many(self):
        """Test the `Group.get_extra_many` method."""
        original_extra = {'nested': {'a': 1}}

        self.group.set_extra('key', original_extra)
        group_extra = self.group.get_extra_many(['key'])[0]
        self.assertEqual(group_extra, original_extra)
        group_extra['nested']['a'] = 2

        self.assertEqual(original_extra['nested']['a'], 2)

        # Now store the group and verify that `get_extra` then returns a deep copy
        self.group.store()
        group_extra = self.group.get_extra_many(['key'])[0]

        # We change the returned group extras but the original extra should remain unchanged
        group_extra['nested']['a'] = 3
        self.assertEqual(original_extra['nested']['a'], 2)

    def test_set_extra(self):
        """Test the `Group.set_extra` method."""
        with self.assertRaises(exceptions.ValidationError):
            self.group.set_extra('illegal.key', 'value')

        self.group.set_extra('valid_key', 'value')
        self.group.store()

        self.group.set_extra('valid_key', 'changed')
        self.assertEqual(orm.load_group(self.group.pk).get_extra('valid_key'), 'changed')

    def test_set_extra_many(self):
        """Test the `Group.set_extra` method."""
        with self.assertRaises(exceptions.ValidationError):
            self.group.set_extra_many({'illegal.key': 'value', 'valid_key': 'value'})

        self.group.set_extra_many({'valid_key': 'value'})
        self.group.store()

        self.group.set_extra_many({'valid_key': 'changed'})
        self.assertEqual(orm.load_group(self.group.pk).get_extra('valid_key'), 'changed')

    def test_reset_extra(self):
        """Test the `Group.reset_extra` method."""
        extras_before = {'extra_one': 'value', 'extra_two': 'value'}
        extras_after = {'extra_three': 'value', 'extra_four': 'value'}
        extras_illegal = {'extra.illegal': 'value', 'extra_four': 'value'}

        self.group.set_extra_many(extras_before)
        self.assertEqual(self.group.extras, extras_before)
        self.group.reset_extras(extras_after)
        self.assertEqual(self.group.extras, extras_after)

        with self.assertRaises(exceptions.ValidationError):
            self.group.reset_extras(extras_illegal)

        self.group.store()

        self.group.reset_extras(extras_after)
        self.assertEqual(orm.load_group(self.group.pk).extras, extras_after)

    def test_delete_extra(self):
        """Test the `Group.delete_extra` method."""
        self.group.set_extra('valid_key', 'value')
        self.assertEqual(self.group.get_extra('valid_key'), 'value')
        self.group.delete_extra('valid_key')

        with self.assertRaises(AttributeError):
            self.group.delete_extra('valid_key')

        # Repeat with stored group
        self.group.set_extra('valid_key', 'value')
        self.group.store()

        self.group.delete_extra('valid_key')
        with self.assertRaises(AttributeError):
            orm.load_group(self.group.pk).get_extra('valid_key')

    def test_delete_extra_many(self):
        """Test the `Group.delete_extra_many` method."""
        extras_valid = {'extra_one': 'value', 'extra_two': 'value'}
        valid_keys = ['extra_one', 'extra_two']
        invalid_keys = ['extra_one', 'invalid_key']

        self.group.set_extra_many(extras_valid)
        self.assertEqual(self.group.extras, extras_valid)

        with self.assertRaises(AttributeError):
            self.group.delete_extra_many(invalid_keys)

        self.group.store()

        self.group.delete_extra_many(valid_keys)
        self.assertEqual(orm.load_group(self.group.pk).extras, {})

    def test_clear_extras(self):
        """Test the `Group.clear_extras` method."""
        extras = {'extra_one': 'value', 'extra_two': 'value'}
        self.group.set_extra_many(extras)
        self.assertEqual(self.group.extras, extras)

        self.group.clear_extras()
        self.assertEqual(self.group.extras, {})

        # Repeat for stored group
        self.group.store()

        self.group.clear_extras()
        self.assertEqual(orm.load_group(self.group.pk).extras, {})

    def test_extras_items(self):
        """Test the `Group.extras_items` generator."""
        extras = {'extra_one': 'value', 'extra_two': 'value'}
        self.group.set_extra_many(extras)
        self.assertEqual(dict(self.group.extras_items()), extras)

    def test_extras_keys(self):
        """Test the `Group.extras_keys` generator."""
        extras = {'extra_one': 'value', 'extra_two': 'value'}
        self.group.set_extra_many(extras)
        self.assertEqual(set(self.group.extras_keys()), set(extras))
