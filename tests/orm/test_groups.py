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
import uuid

import pytest

from aiida import orm
from aiida.common import exceptions
from aiida.tools.graph.deletions import delete_nodes


class TestGroups:
    """Test backend entities and their collections"""

    def test_count(self):
        """Test the `count` method."""
        node_00 = orm.Data().store()
        node_01 = orm.Data().store()
        nodes = [node_00, node_01]

        group = orm.Group(label=uuid.uuid4().hex, description='description').store()
        group.add_nodes(nodes)

        assert group.count() == len(nodes)

    def test_creation(self):
        """Test the creation of Groups."""
        node = orm.Data()
        stored_node = orm.Data().store()

        group = orm.Group(label=uuid.uuid4().hex)

        with pytest.raises(exceptions.ModificationNotAllowed):
            # group unstored
            group.add_nodes(node)

        with pytest.raises(exceptions.ModificationNotAllowed):
            # group unstored
            group.add_nodes(stored_node)

        group.store()

        with pytest.raises(ValueError):
            # node unstored
            group.add_nodes(node)

        group.add_nodes(stored_node)

        nodes = list(group.nodes)
        assert len(nodes) == 1
        assert nodes[0].pk == stored_node.pk

    def test_node_iterator(self):
        """Test the indexing and slicing functionality of the node iterator."""
        node_00 = orm.Data().store()
        node_01 = orm.Data().store()
        node_02 = orm.Data().store()
        node_03 = orm.Data().store()
        nodes = [node_00, node_01, node_02, node_03]

        group = orm.Group(label=uuid.uuid4().hex, description='description').store()
        group.add_nodes(nodes)

        # Indexing
        node_indexed = group.nodes[0]
        assert isinstance(node_indexed, orm.Data)
        assert node_indexed.uuid in [node.uuid for node in nodes]

        # Slicing
        nodes_sliced = group.nodes[1:3]
        assert isinstance(nodes_sliced, list)
        assert len(nodes_sliced) == 2
        assert all(isinstance(node, orm.Data) for node in nodes_sliced)
        assert all(node.uuid in set(node.uuid for node in nodes) for node in nodes_sliced)

    def test_entry_point(self):
        """Test the :meth:`aiida.orm.groups.Group.entry_point` property."""
        from aiida.plugins.entry_point import get_entry_point_from_string

        group = orm.Group('label')
        assert group.entry_point == get_entry_point_from_string('aiida.groups:core')
        assert orm.Group.entry_point == get_entry_point_from_string('aiida.groups:core')

        class Custom(orm.Group):
            pass

        group = Custom('label')
        assert group.entry_point is None
        assert Custom.entry_point is None

    def test_description(self):
        """Test the update of the description both for stored and unstored groups."""
        node = orm.Data().store()

        group_01 = orm.Group(label=uuid.uuid4().hex, description='group_01').store()
        group_01.add_nodes(node)

        group_02 = orm.Group(label=uuid.uuid4().hex, description='group_02')

        # Preliminary checks
        assert group_01.is_stored
        assert not group_02.is_stored
        assert group_01.description == 'group_01'
        assert group_02.description == 'group_02'

        # Change
        group_01.description = 'new1'
        group_02.description = 'new2'

        # Test that the groups remained in their proper stored state and that
        # the description was updated
        assert group_01.is_stored
        assert not group_02.is_stored
        assert group_01.description == 'new1'
        assert group_02.description == 'new2'

        # Store group_02 and check that the description is OK
        group_02.store()
        assert group_02.is_stored
        assert group_02.description == 'new2'

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
        assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

        # Try to add a node that is already present: there should be no problem
        group.add_nodes(node_01)
        assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

    def test_remove_nodes(self):
        """Test node removal."""
        node_01 = orm.Data().store()
        node_02 = orm.Data().store()
        node_03 = orm.Data().store()
        node_04 = orm.Data().store()
        nodes = [node_01, node_02, node_03]
        group = orm.Group(label=uuid.uuid4().hex).store()

        # Add initial nodes
        group.add_nodes(nodes)
        assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

        # Remove a node that is not in the group: nothing should happen
        group.remove_nodes(node_04)
        assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

        # Remove one orm.Node
        nodes.remove(node_03)
        group.remove_nodes(node_03)
        assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

        # Remove a list of Nodes and check
        nodes.remove(node_01)
        nodes.remove(node_02)
        group.remove_nodes([node_01, node_02])
        assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

    def test_clear(self):
        """Test the `clear` method to remove all nodes."""
        node_01 = orm.Data().store()
        node_02 = orm.Data().store()
        node_03 = orm.Data().store()
        nodes = [node_01, node_02, node_03]
        group = orm.Group(label=uuid.uuid4().hex).store()

        # Add initial nodes
        group.add_nodes(nodes)
        assert set(_.pk for _ in nodes) == set(_.pk for _ in group.nodes)

        group.clear()
        assert not list(group.nodes)

    def test_name_desc(self):
        """Test Group description."""
        group = orm.Group(label='testgroup2', description='some desc')
        assert group.label == 'testgroup2'
        assert group.description == 'some desc'
        assert group.is_user_defined
        group.store()

        # Same checks after storing
        assert group.label == 'testgroup2'
        assert group.is_user_defined
        assert group.description == 'some desc'

        # To avoid to find it in further tests
        orm.Group.collection.delete(group.pk)

    def test_delete(self):
        """Test Group deletion."""
        node = orm.Data().store()
        group = orm.Group(label='testgroup3', description='some other desc').store()

        group_copy = orm.Group.collection.get(label='testgroup3')
        assert group.uuid == group_copy.uuid

        group.add_nodes(node)
        assert len(group.nodes) == 1

        orm.Group.collection.delete(group.pk)

        with pytest.raises(exceptions.NotExistent):
            # The group does not exist anymore
            orm.Group.collection.get(label='testgroup3')

    def test_delete_node(self):
        """Test deletion of a node that has been assigned to a group."""
        node = orm.Data().store()
        group = orm.Group(label='testgroup', description='some desc').store()
        group.add_nodes(node)
        assert len(group.nodes) == 1
        delete_nodes([node.pk], dry_run=False)
        assert len(group.nodes) == 0

    def test_rename(self):
        """Test the renaming of a Group."""
        label_original = 'groupie'
        label_changed = 'nogroupie'

        group = orm.Group(label=label_original, description='I will be renamed')

        # Check name changes work before storing
        assert group.label == label_original
        group.label = label_changed
        assert group.label == label_changed

        # Revert the name to its original and store it
        group.label = label_original
        group.store()

        # Check name changes work after storing
        assert group.label == label_original
        group.label = label_changed
        assert group.label == label_changed

    def test_rename_existing(self):
        """Test that renaming to an already existing name is not permitted."""
        label_group_a = 'group_a'
        label_group_b = 'group_b'

        orm.Group(label=label_group_a, description='I am the Original G').store()

        # Before storing everything should be fine
        group_b = orm.Group(label=label_group_a, description='They will try to rename me')

        # Storing for duplicate group name should trigger UniquenessError
        with pytest.raises(exceptions.IntegrityError):
            group_b.store()

        # Reverting to unique name before storing
        group_b.label = label_group_b
        group_b.store()

        # After storing name change to existing should raise
        with pytest.raises(exceptions.IntegrityError):
            group_b.label = label_group_a

    def test_group_uuid_hashing_for_querybuidler(self):
        """QueryBuilder results should be reusable and shouldn't brake hashing."""
        group = orm.Group(label='test_group')
        group.store()

        # Search for the UUID of the stored group
        builder = orm.QueryBuilder()
        builder.append(orm.Group, project=['uuid'], filters={'label': {'==': 'test_group'}})
        group_uuid = builder.first(flat=True)

        # Look the node with the previously returned UUID
        builder = orm.QueryBuilder()
        builder.append(orm.Group, project=['id'], filters={'uuid': {'==': group_uuid}})

        # Check that the query doesn't fail
        builder.all()

        # And that the results are correct
        assert builder.count() == 1
        assert builder.first(flat=True) == group.pk


class TestGroupsSubclasses:
    """Test rules around creating `Group` subclasses."""

    @staticmethod
    def test_creation_registered():
        """Test rules around creating registered `Group` subclasses."""
        group = orm.AutoGroup('some-label')
        assert isinstance(group, orm.AutoGroup)
        assert group.type_string == 'core.auto'

        group, _ = orm.AutoGroup.collection.get_or_create('some-auto-group')
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
        instance = SubGroup(label=uuid.uuid4().hex)
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
        group = orm.Group(label=uuid.uuid4().hex)
        group.backend_entity.bare_model.type_string = 'unregistered.subclass'
        group.store()

        with pytest.warns(UserWarning):
            loaded = orm.load_group(group.pk)

        assert isinstance(loaded, orm.Group)

        # Removing it as other methods might get a warning instead
        group_pk = group.pk
        del group
        orm.Group.collection.delete(pk=group_pk)

    @staticmethod
    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_querying():
        """Test querying for groups with and without subclassing."""
        orm.Group(label=uuid.uuid4().hex).store()
        orm.AutoGroup(label=uuid.uuid4().hex).store()

        # Fake a subclass by manually setting the type string
        group = orm.Group(label=uuid.uuid4().hex)
        group.backend_entity.bare_model.type_string = 'custom.group'
        group.store()

        assert orm.QueryBuilder().append(orm.AutoGroup).count() == 1
        assert orm.QueryBuilder().append(orm.AutoGroup, subclassing=False).count() == 1
        assert orm.QueryBuilder().append(orm.Group, subclassing=False).count() == 1
        assert orm.QueryBuilder().append(orm.Group).count() == 3
        assert orm.QueryBuilder().append(orm.Group, filters={'type_string': 'custom.group'}).count() == 1

        # Removing it as other methods might get a warning instead
        group_pk = group.pk
        del group
        orm.Group.collection.delete(pk=group_pk)

    @staticmethod
    def test_querying_node_subclasses():
        """Test querying for groups with multiple types for nodes it contains."""
        group = orm.Group(label=uuid.uuid4().hex).store()
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
        group = orm.Group(label=uuid.uuid4().hex).store()
        data = orm.Data().store()

        group.add_nodes([data])

        builder = orm.QueryBuilder().append(orm.Data, filters={
            'id': data.pk
        }, tag='data').append(orm.Group, with_node='data')

        loaded = builder.one()[0]

        assert loaded.pk == group.pk


class TestGroupExtras:
    """Test the property and methods of group extras."""

    @pytest.fixture(autouse=True)
    def init_profile(self):  # pylint: disable=unused-argument
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init
        self.group = orm.Group(uuid.uuid4().hex)

    def test_extras(self):
        """Test the `Group.base.extras.all` property."""
        original_extra = {'nested': {'a': 1}}

        self.group.base.extras.set('key', original_extra)
        group_extras = self.group.base.extras.all
        assert group_extras['key'] == original_extra
        group_extras['key']['nested']['a'] = 2

        assert original_extra['nested']['a'] == 2

        # Now store the group and verify that `extras` then returns a deep copy
        self.group.store()
        group_extras = self.group.base.extras.all

        # We change the returned group extras but the original extra should remain unchanged
        group_extras['key']['nested']['a'] = 3
        assert original_extra['nested']['a'] == 2

    def test_get_extra(self):
        """Test the `Group.get_extra` method."""
        original_extra = {'nested': {'a': 1}}

        self.group.base.extras.set('key', original_extra)
        group_extra = self.group.base.extras.get('key')
        assert group_extra == original_extra
        group_extra['nested']['a'] = 2

        assert original_extra['nested']['a'] == 2

        default = 'default'
        assert self.group.base.extras.get('not_existing', default=default) == default
        with pytest.raises(AttributeError):
            self.group.base.extras.get('not_existing')

        # Now store the group and verify that `get_extra` then returns a deep copy
        self.group.store()
        group_extra = self.group.base.extras.get('key')

        # We change the returned group extras but the original extra should remain unchanged
        group_extra['nested']['a'] = 3
        assert original_extra['nested']['a'] == 2

        default = 'default'
        assert self.group.base.extras.get('not_existing', default=default) == default
        with pytest.raises(AttributeError):
            self.group.base.extras.get('not_existing')

    def test_get_extra_many(self):
        """Test the `Group.base.extras.get_many` method."""
        original_extra = {'nested': {'a': 1}}

        self.group.base.extras.set('key', original_extra)
        group_extra = self.group.base.extras.get_many(['key'])[0]
        assert group_extra == original_extra
        group_extra['nested']['a'] = 2

        assert original_extra['nested']['a'] == 2

        # Now store the group and verify that `get_extra` then returns a deep copy
        self.group.store()
        group_extra = self.group.base.extras.get_many(['key'])[0]

        # We change the returned group extras but the original extra should remain unchanged
        group_extra['nested']['a'] = 3
        assert original_extra['nested']['a'] == 2

    def test_set_extra(self):
        """Test the `Group.set_extra` method."""
        with pytest.raises(exceptions.ValidationError):
            self.group.base.extras.set('illegal.key', 'value')

        self.group.base.extras.set('valid_key', 'value')
        self.group.store()

        self.group.base.extras.set('valid_key', 'changed')
        assert orm.load_group(self.group.pk).base.extras.get('valid_key') == 'changed'

    def test_set_extra_many(self):
        """Test the `Group.base.extras.set_many` method."""
        with pytest.raises(exceptions.ValidationError):
            self.group.base.extras.set_many({'illegal.key': 'value', 'valid_key': 'value'})

        self.group.base.extras.set_many({'valid_key': 'value'})
        self.group.store()

        self.group.base.extras.set_many({'valid_key': 'changed'})
        assert orm.load_group(self.group.pk).base.extras.get('valid_key') == 'changed'

    def test_reset_extra(self):
        """Test the `Group.base.extras.reset` method."""
        extras_before = {'extra_one': 'value', 'extra_two': 'value'}
        extras_after = {'extra_three': 'value', 'extra_four': 'value'}
        extras_illegal = {'extra.illegal': 'value', 'extra_four': 'value'}

        self.group.base.extras.set_many(extras_before)
        assert self.group.base.extras.all == extras_before
        self.group.base.extras.reset(extras_after)
        assert self.group.base.extras.all == extras_after

        with pytest.raises(exceptions.ValidationError):
            self.group.base.extras.reset(extras_illegal)

        self.group.store()

        self.group.base.extras.reset(extras_after)
        assert orm.load_group(self.group.pk).base.extras.all == extras_after

    def test_delete_extra(self):
        """Test the `Group.base.extras.delete` method."""
        self.group.base.extras.set('valid_key', 'value')
        assert self.group.base.extras.get('valid_key') == 'value'
        self.group.base.extras.delete('valid_key')

        with pytest.raises(AttributeError):
            self.group.base.extras.delete('valid_key')

        # Repeat with stored group
        self.group.base.extras.set('valid_key', 'value')
        self.group.store()

        self.group.base.extras.delete('valid_key')
        with pytest.raises(AttributeError):
            orm.load_group(self.group.pk).base.extras.get('valid_key')

    def test_delete_extra_many(self):
        """Test the `Group.base.extras.delete_many` method."""
        extras_valid = {'extra_one': 'value', 'extra_two': 'value'}
        valid_keys = ['extra_one', 'extra_two']
        invalid_keys = ['extra_one', 'invalid_key']

        self.group.base.extras.set_many(extras_valid)
        assert self.group.base.extras.all == extras_valid

        with pytest.raises(AttributeError):
            self.group.base.extras.delete_many(invalid_keys)

        self.group.store()

        self.group.base.extras.delete_many(valid_keys)
        assert orm.load_group(self.group.pk).base.extras.all == {}

    def test_clear_extras(self):
        """Test the `Group.base.extras.clear` method."""
        extras = {'extra_one': 'value', 'extra_two': 'value'}
        self.group.base.extras.set_many(extras)
        assert self.group.base.extras.all == extras

        self.group.base.extras.clear()
        assert self.group.base.extras.all == {}

        # Repeat for stored group
        self.group.store()

        self.group.base.extras.clear()
        assert orm.load_group(self.group.pk).base.extras.all == {}

    def test_extras_items(self):
        """Test the `Group.base.extras.items` generator."""
        extras = {'extra_one': 'value', 'extra_two': 'value'}
        self.group.base.extras.set_many(extras)
        assert dict(self.group.base.extras.items()) == extras

    def test_extras_keys(self):
        """Test the `Group.base.extras.keys` generator."""
        extras = {'extra_one': 'value', 'extra_two': 'value'}
        self.group.base.extras.set_many(extras)
        assert set(self.group.base.extras.keys()) == set(extras)
