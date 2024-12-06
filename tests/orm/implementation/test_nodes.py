###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the BackendNode and BackendNodeCollection classes."""

from collections import OrderedDict
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from aiida.common import exceptions, timezone
from aiida.orm.implementation.nodes import BackendNode


class TestBackendNode:
    """Test BackendNode."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost, backend):
        """Initialize the profile."""
        self.backend = backend
        self.computer = aiida_localhost.backend_entity  # Unwrap the `Computer` instance to `BackendComputer`
        self.user = backend.users.create(email=uuid4().hex).store()
        self.node_type = ''
        self.node_label = uuid4().hex
        self.node_description = 'description'
        self.node = backend.nodes.create(
            node_type=self.node_type,
            user=self.user,
            computer=self.computer,
            label=self.node_label,
            description=self.node_description,
        )

    def create_node(self) -> BackendNode:
        return self.backend.nodes.create(node_type=self.node_type, user=self.user)

    def test_creation(self):
        """Test creation of a BackendNode and all its properties."""
        node = self.backend.nodes.create(
            node_type=self.node_type, user=self.user, label=self.node_label, description=self.node_description
        )

        # Before storing
        assert node.id is None
        assert node.pk is None
        assert isinstance(node.uuid, str)
        assert isinstance(node.ctime, datetime)
        assert node.mtime is None
        assert node.process_type is None
        assert node.attributes == {}
        assert node.extras == {}
        assert node.repository_metadata == {}
        assert node.node_type == self.node_type
        assert node.label == self.node_label
        assert node.description == self.node_description

        # Store the node.ctime before the store as a reference
        now = timezone.now()
        node_ctime_before_store = node.ctime
        assert now > node.ctime, f'{node.ctime} is not smaller than now {now}'

        node.store()
        node_ctime = node.ctime
        node_mtime = node.mtime

        # The node.ctime should have been unchanged, but the node.mtime should have changed
        assert node.ctime == node_ctime_before_store
        assert node.mtime is not None
        assert now < node.mtime, f'{node.mtime} is not larger than now {now}'

        # After storing
        assert isinstance(node.id, int)
        assert isinstance(node.pk, int)
        assert isinstance(node.uuid, str)
        assert isinstance(node.ctime, datetime)
        assert isinstance(node.mtime, datetime)
        assert node.process_type is None
        assert node.attributes == {}
        assert node.extras == {}
        assert node.repository_metadata == {}
        assert node.node_type == self.node_type
        assert node.label == self.node_label
        assert node.description == self.node_description

        # Try to construct a UUID from the UUID value to prove that it has a valid UUID
        UUID(node.uuid)

        # Change a column, which should trigger the save, update the mtime but leave the ctime untouched
        node.label = 'test'
        assert node.ctime == node_ctime
        assert node.mtime > node_mtime

    def test_creation_with_time(self):
        """Test creation of a BackendNode when passing the mtime and the ctime. The passed ctime and mtime
        should be respected since it is important for the correct import of nodes at the AiiDA import/export.
        """
        ctime = datetime(2019, 2, 27, 16, 20, 12, 245738, timezone.utc)
        mtime = datetime(2019, 2, 27, 16, 27, 14, 798838, timezone.utc)

        node = self.backend.nodes.create(
            node_type=self.node_type,
            user=self.user,
            label=self.node_label,
            description=self.node_description,
            mtime=mtime,
            ctime=ctime,
        )

        # Check that the ctime and mtime are the given ones
        assert node.ctime == ctime
        assert node.mtime == mtime

        node.store()

        # Check that the given values remain even after storing
        assert node.ctime == ctime
        assert node.mtime == mtime

    def test_mtime(self):
        """Test the `mtime` is automatically updated when a database field is updated."""
        node = self.node.store()
        node_mtime = node.mtime

        node.label = 'changed label'
        assert node.mtime > node_mtime

    def test_clone(self):
        """Test the `clone` method."""
        node = self.node.store()
        clone = node.clone()

        # Check that the clone is unstored, i.e. has *no* id, has a different UUID, but all other props are the same
        assert clone.id is None
        assert clone.uuid != node.uuid
        assert clone.label == node.label
        assert clone.description == node.description
        assert clone.user.id == node.user.id
        assert clone.computer.id == node.computer.id
        assert clone.attributes == node.attributes
        assert clone.extras == node.extras

    def test_property_setters(self):
        """Test the property setters of a BackendNode."""
        label = 'new label'
        description = 'new description'

        self.node.label = label
        self.node.description = description

        assert self.node.label == label
        assert self.node.description == description

    def test_computer_methods(self):
        """Test the computer methods of a BackendNode."""
        new_computer = self.backend.computers.create(label='localhost2', hostname='localhost').store()
        assert self.node.computer.id == self.computer.id
        self.node.computer = new_computer
        assert self.node.computer.id == new_computer.id

    def test_user_methods(self):
        """Test the user methods of a BackendNode."""
        new_user = self.backend.users.create(email='newuser@localhost').store()
        assert self.node.user.id == self.user.id
        self.node.user = new_user
        assert self.node.user.id == new_user.id

    def test_get_set_attribute(self):
        """Test the `get_attribute` and `set_attribute` method of a BackendNode."""
        attribute_1_name = 'a'
        attribute_2_name = 'b'
        attribute_3_name = 'c'
        attribute_1_value = '1'
        attribute_2_value = '2'
        attribute_3_value = '3'

        with pytest.raises(AttributeError):
            self.node.get_attribute(attribute_1_name)

        assert not self.node.is_stored
        self.node.set_attribute(attribute_1_name, attribute_1_value)

        # Check that the attribute is set, but the node is not stored
        assert not self.node.is_stored
        assert self.node.get_attribute(attribute_1_name) == attribute_1_value

        self.node.store()

        # Check that the attribute is set, and the node is stored
        assert self.node.is_stored
        assert self.node.get_attribute(attribute_1_name) == attribute_1_value

        self.node.set_attribute(attribute_2_name, attribute_2_value)
        assert self.node.get_attribute(attribute_1_name) == attribute_1_value
        assert self.node.get_attribute(attribute_2_name) == attribute_2_value

        reloaded = self.backend.nodes.get(self.node.pk)
        assert self.node.get_attribute(attribute_1_name) == attribute_1_value
        assert self.node.get_attribute(attribute_2_name) == attribute_2_value

        reloaded.set_attribute(attribute_3_name, attribute_3_value)
        assert reloaded.get_attribute(attribute_1_name) == attribute_1_value
        assert reloaded.get_attribute(attribute_2_name) == attribute_2_value
        assert reloaded.get_attribute(attribute_3_name) == attribute_3_value

        # Check deletion of a single
        reloaded.delete_attribute(attribute_1_name)

        with pytest.raises(AttributeError):
            reloaded.get_attribute(attribute_1_name)

        assert reloaded.get_attribute(attribute_2_name) == attribute_2_value
        assert reloaded.get_attribute(attribute_3_name) == attribute_3_value

        with pytest.raises(AttributeError):
            self.node.get_attribute(attribute_1_name)

    def test_get_set_extras(self):
        """Test the `get_extras` and `set_extras` method of a BackendNode."""
        extra_1_name = 'a'
        extra_2_name = 'b'
        extra_3_name = 'c'
        extra_1_value = '1'
        extra_2_value = '2'
        extra_3_value = '3'

        with pytest.raises(AttributeError):
            self.node.get_extra(extra_1_name)

        assert not self.node.is_stored
        self.node.set_extra(extra_1_name, extra_1_value)

        # Check that the extra is set, but the node is not stored
        assert not self.node.is_stored
        assert self.node.get_extra(extra_1_name) == extra_1_value

        self.node.store()

        # Check that the extra is set, and the node is stored
        assert self.node.is_stored
        assert self.node.get_extra(extra_1_name) == extra_1_value

        self.node.set_extra(extra_2_name, extra_2_value)
        assert self.node.get_extra(extra_1_name) == extra_1_value
        assert self.node.get_extra(extra_2_name) == extra_2_value

        reloaded = self.backend.nodes.get(self.node.pk)
        assert self.node.get_extra(extra_1_name) == extra_1_value
        assert self.node.get_extra(extra_2_name) == extra_2_value

        reloaded.set_extra(extra_3_name, extra_3_value)
        assert reloaded.get_extra(extra_1_name) == extra_1_value
        assert reloaded.get_extra(extra_2_name) == extra_2_value
        assert reloaded.get_extra(extra_3_name) == extra_3_value

        # Check deletion of a single
        reloaded.delete_extra(extra_1_name)

        with pytest.raises(AttributeError):
            reloaded.get_extra(extra_1_name)

        assert reloaded.get_extra(extra_2_name) == extra_2_value
        assert reloaded.get_extra(extra_3_name) == extra_3_value

        with pytest.raises(AttributeError):
            self.node.get_extra(extra_1_name)

    def test_attributes(self):
        """Test the `BackendNode.attributes` property."""
        node = self.create_node()
        assert node.attributes == {}
        node.set_attribute('attribute', 'value')
        assert node.attributes == {'attribute': 'value'}

        node.store()
        assert node.attributes == {'attribute': 'value'}

    def test_get_attribute(self):
        """Test the `BackendNode.get_attribute` method."""
        node = self.create_node()

        with pytest.raises(AttributeError):
            node.get_attribute('attribute')

        node.set_attribute('attribute', 'value')
        assert node.get_attribute('attribute') == 'value'

        node.store()
        assert node.get_attribute('attribute') == 'value'

    def test_get_attribute_many(self):
        """Test the `BackendNode.get_attribute_many` method."""
        node = self.create_node()

        with pytest.raises(AttributeError):
            node.get_attribute_many(['attribute'])

        node.set_attribute_many({'attribute': 'value', 'another': 'case'})

        with pytest.raises(AttributeError):
            node.get_attribute_many(['attribute', 'unexisting'])

        assert node.get_attribute_many(['attribute', 'another']) == ['value', 'case']

        node.store()
        assert node.get_attribute_many(['attribute', 'another']) == ['value', 'case']

    def test_set_attribute(self):
        """Test the `BackendNode.set_attribute` method."""
        node = self.create_node()

        # When not stored, `set_attribute` will not clean values, so the following should be allowed
        node.set_attribute('attribute_invalid', object())
        node.set_attribute('attribute_valid', 'value')

        # Calling store should cause the values to be cleaned which should raise
        with pytest.raises(exceptions.ValidationError):
            node.store()

        # Replace the original invalid with a valid value
        node.set_attribute('attribute_invalid', 'actually valid')
        node.store()
        assert node.get_attribute_many(['attribute_invalid', 'attribute_valid']) == ['actually valid', 'value']

        # Raises immediately when setting it if already stored
        with pytest.raises(exceptions.ValidationError):
            node.set_attribute('attribute', object())

    def test_set_attribute_many(self):
        """Test the `BackendNode.set_attribute_many` method."""
        # Calling `set_attribute_many` on an unstored node
        node = self.create_node()

        # When not stored, `set_attribute` will not clean values, so the following should be allowed
        node.set_attribute_many({'attribute_invalid': object(), 'attribute_valid': 'value'})

        # Calling store should cause the values to be cleaned which should raise
        with pytest.raises(exceptions.ValidationError):
            node.store()

        # Replace the original invalid with a valid value
        node.set_attribute_many({'attribute_invalid': 'actually valid'})
        node.store()
        assert node.get_attribute_many(['attribute_invalid', 'attribute_valid']) == ['actually valid', 'value']

        attributes = OrderedDict()
        attributes['another_attribute'] = 'value'
        attributes['attribute_invalid'] = object()

        # Raises immediately when setting it if already stored
        with pytest.raises(exceptions.ValidationError):
            node.set_attribute_many(attributes)

        assert 'another_attribute' not in node.attributes

        attributes = {'attribute_one': 1, 'attribute_two': 2}
        # Calling `set_attribute_many` on a stored node
        node = self.create_node()
        node.store()

        node.set_attribute_many(attributes)
        assert node.attributes == attributes

    def test_reset_attributes(self):
        """Test the `BackendNode.reset_attributes` method."""
        node = self.create_node()
        attributes_before = {'attribute_one': 1, 'attribute_two': 2}
        attributes_after = {'attribute_three': 3, 'attribute_four': 4}

        # Reset attributes on an unstored node
        node.set_attribute_many(attributes_before)
        assert node.attributes == attributes_before

        node.reset_attributes(attributes_after)
        assert node.attributes == attributes_after

        # Reset attributes on stored node
        node = self.create_node()
        node.store()

        node.set_attribute_many(attributes_before)
        assert node.attributes == attributes_before

        node.reset_attributes(attributes_after)
        assert node.attributes == attributes_after

    def test_delete_attribute(self):
        """Test the `BackendNode.delete_attribute` method."""
        node = self.create_node()

        with pytest.raises(AttributeError):
            node.delete_attribute('notexisting')

        node.set_attribute('attribute', 'value')
        node.delete_attribute('attribute')
        assert node.attributes == {}

        # Now for a stored node
        node = self.create_node().store()

        with pytest.raises(AttributeError):
            node.delete_attribute('notexisting')

        node.set_attribute('attribute', 'value')
        node.delete_attribute('attribute')
        assert node.attributes == {}

    def test_delete_attribute_many(self):
        """Test the `BackendNode.delete_attribute_many` method."""
        node = self.create_node()
        attributes = {'attribute_one': 1, 'attribute_two': 2}

        with pytest.raises(AttributeError):
            node.delete_attribute_many(['notexisting', 'some'])

        node.set_attribute_many(attributes)

        with pytest.raises(AttributeError):
            node.delete_attribute_many(['attribute_one', 'notexisting'])

        # Because one key failed during delete, none of the attributes should have been deleted
        assert 'attribute_one' in node.attributes

        # Now delete the keys that actually should exist
        node.delete_attribute_many(attributes.keys())
        assert node.attributes == {}

        # Now for a stored node
        node = self.create_node().store()

        with pytest.raises(AttributeError):
            node.delete_attribute_many(['notexisting', 'some'])

        node.set_attribute_many(attributes)

        with pytest.raises(AttributeError):
            node.delete_attribute_many(['attribute_one', 'notexisting'])

        # Because one key failed during delete, none of the attributes should have been deleted
        assert 'attribute_one' in node.attributes

        # Now delete the keys that actually should exist
        node.delete_attribute_many(attributes.keys())
        assert node.attributes == {}

    def test_clear_attributes(self):
        """Test the `BackendNode.clear_attributes` method."""
        node = self.create_node()
        attributes = {'attribute_one': 1, 'attribute_two': 2}
        node.set_attribute_many(attributes)

        assert node.attributes == attributes
        node.clear_attributes()
        assert node.attributes == {}

        # Now for a stored node
        node = self.create_node().store()
        node.set_attribute_many(attributes)

        assert node.attributes == attributes
        node.clear_attributes()
        assert node.attributes == {}

    def test_attribute_items(self):
        """Test the `BackendNode.attribute_items` generator."""
        node = self.create_node()
        attributes = {'attribute_one': 1, 'attribute_two': 2}

        node.set_attribute_many(attributes)
        assert attributes == dict(node.attributes_items())

        # Repeat for a stored node
        node = self.create_node().store()
        attributes = {'attribute_one': 1, 'attribute_two': 2}

        node.set_attribute_many(attributes)
        assert attributes == dict(node.attributes_items())

    def test_attribute_keys(self):
        """Test the `BackendNode.attribute_keys` generator."""
        node = self.create_node()
        attributes = {'attribute_one': 1, 'attribute_two': 2}

        node.set_attribute_many(attributes)
        assert set(attributes) == set(node.attributes_keys())

        # Repeat for a stored node
        node = self.create_node().store()
        attributes = {'attribute_one': 1, 'attribute_two': 2}

        node.set_attribute_many(attributes)
        assert set(attributes) == set(node.attributes_keys())

    def test_attribute_flush_specifically(self):
        """Test that changing `attributes` only flushes that property and does not affect others like extras.

        Regression fix for #3338
        """
        node = self.create_node().store()
        extras = {'extra_one': 1, 'extra_two': 2}
        node.set_extra_many(extras)
        node.store()

        # Load the stored node in memory in another instance and add another extra
        reloaded = self.backend.nodes.get(node.pk)
        reloaded.set_extra('extra_three', 3)

        # The original memory instance should now not include `extra_three`. Changing an attribute should only flush
        # the attributes and not the whole node state, which would override for example also the extras.
        node.set_attribute('attribute_one', 1)

        # Reload the node yet again and verify that the `extra_three` extra is still there
        rereloaded = self.backend.nodes.get(node.pk)
        assert 'extra_three' in rereloaded.extras.keys()

    def test_extras(self):
        """Test the `BackendNode.extras` property."""
        node = self.create_node()
        assert node.extras == {}
        node.set_extra('extra', 'value')
        assert node.extras == {'extra': 'value'}

        node.store()
        assert node.extras == {'extra': 'value'}

    def test_get_extra(self):
        """Test the `BackendNode.get_extra` method."""
        node = self.create_node()

        with pytest.raises(AttributeError):
            node.get_extra('extra')

        node.set_extra('extra', 'value')
        assert node.get_extra('extra') == 'value'

        node.store()
        assert node.get_extra('extra') == 'value'

    def test_get_extra_many(self):
        """Test the `BackendNode.get_extra_many` method."""
        node = self.create_node()

        with pytest.raises(AttributeError):
            node.get_extra_many(['extra'])

        node.set_extra_many({'extra': 'value', 'another': 'case'})

        with pytest.raises(AttributeError):
            node.get_extra_many(['extra', 'unexisting'])

        assert node.get_extra_many(['extra', 'another']) == ['value', 'case']

        node.store()
        assert node.get_extra_many(['extra', 'another']) == ['value', 'case']

    def test_set_extra(self):
        """Test the `BackendNode.set_extra` method."""
        node = self.create_node()

        # When not stored, `set_extra` will not clean values, so the following should be allowed
        node.set_extra('extra_invalid', object())
        node.set_extra('extra_valid', 'value')

        # Calling store should cause the values to be cleaned which should raise
        with pytest.raises(exceptions.ValidationError):
            node.store()

        # Replace the original invalid with a valid value
        node.set_extra('extra_invalid', 'actually valid')
        node.store()
        assert node.get_extra_many(['extra_invalid', 'extra_valid']) == ['actually valid', 'value']

        # Raises immediately when setting it if already stored
        with pytest.raises(exceptions.ValidationError):
            node.set_extra('extra', object())

    def test_set_extra_many(self):
        """Test the `BackendNode.set_extra_many` method."""
        # Calling `set_extra_many` on an unstored node
        node = self.create_node()

        # When not stored, `set_extra` will not clean values, so the following should be allowed
        node.set_extra_many({'extra_invalid': object(), 'extra_valid': 'value'})

        # Calling store should cause the values to be cleaned which should raise
        with pytest.raises(exceptions.ValidationError):
            node.store()

        # Replace the original invalid with a valid value
        node.set_extra_many({'extra_invalid': 'actually valid'})
        node.store()
        assert node.get_extra_many(['extra_invalid', 'extra_valid']) == ['actually valid', 'value']

        extras = OrderedDict()
        extras['another_extra'] = 'value'
        extras['extra_invalid'] = object()

        # Raises immediately when setting it if already stored
        with pytest.raises(exceptions.ValidationError):
            node.set_extra_many(extras)

        assert 'another_extra' not in node.extras

        extras = {'extra_one': 1, 'extra_two': 2}
        # Calling `set_extra_many` on a stored node
        node = self.create_node()
        node.store()

        node.set_extra_many(extras)
        assert node.extras == extras

    def test_reset_extras(self):
        """Test the `BackendNode.reset_extras` method."""
        node = self.create_node()
        extras_before = {'extra_one': 1, 'extra_two': 2}
        extras_after = {'extra_three': 3, 'extra_four': 4}

        # Reset extras on an unstored node
        node.set_extra_many(extras_before)
        assert node.extras == extras_before

        node.reset_extras(extras_after)
        assert node.extras == extras_after

        # Reset extras on stored node
        node = self.create_node()
        node.store()

        node.set_extra_many(extras_before)
        assert node.extras == extras_before

        node.reset_extras(extras_after)
        assert node.extras == extras_after

    def test_delete_extra(self):
        """Test the `BackendNode.delete_extra` method."""
        node = self.create_node()

        with pytest.raises(AttributeError):
            node.delete_extra('notexisting')

        node.set_extra('extra', 'value')
        node.delete_extra('extra')
        assert node.extras == {}

        # Now for a stored node
        node = self.create_node().store()

        with pytest.raises(AttributeError):
            node.delete_extra('notexisting')

        node.set_extra('extra', 'value')
        node.delete_extra('extra')
        assert node.extras == {}

    def test_delete_extra_many(self):
        """Test the `BackendNode.delete_extra_many` method."""
        node = self.create_node()
        extras = {'extra_one': 1, 'extra_two': 2}

        with pytest.raises(AttributeError):
            node.delete_extra_many(['notexisting', 'some'])

        node.set_extra_many(extras)

        with pytest.raises(AttributeError):
            node.delete_extra_many(['extra_one', 'notexisting'])

        # Because one key failed during delete, none of the extras should have been deleted
        assert 'extra_one' in node.extras

        # Now delete the keys that actually should exist
        node.delete_extra_many(extras.keys())
        assert node.extras == {}

        # Now for a stored node
        node = self.create_node().store()

        with pytest.raises(AttributeError):
            node.delete_extra_many(['notexisting', 'some'])

        node.set_extra_many(extras)

        with pytest.raises(AttributeError):
            node.delete_extra_many(['extra_one', 'notexisting'])

        # Because one key failed during delete, none of the extras should have been deleted
        assert 'extra_one' in node.extras

        # Now delete the keys that actually should exist
        node.delete_extra_many(extras.keys())
        assert node.extras == {}

    def test_clear_extras(self):
        """Test the `BackendNode.clear_extras` method."""
        node = self.create_node()
        extras = {'extra_one': 1, 'extra_two': 2}
        node.set_extra_many(extras)

        assert node.extras == extras
        node.clear_extras()
        assert node.extras == {}

        # Now for a stored node
        node = self.create_node().store()
        node.set_extra_many(extras)

        assert node.extras == extras
        node.clear_extras()
        assert node.extras == {}

    def test_extra_items(self):
        """Test the `BackendNode.extra_items` generator."""
        node = self.create_node()
        extras = {'extra_one': 1, 'extra_two': 2}

        node.set_extra_many(extras)
        assert extras == dict(node.extras_items())

        # Repeat for a stored node
        node = self.create_node().store()
        extras = {'extra_one': 1, 'extra_two': 2}

        node.set_extra_many(extras)
        assert extras == dict(node.extras_items())

    def test_extra_keys(self):
        """Test the `BackendNode.extra_keys` generator."""
        node = self.create_node()
        extras = {'extra_one': 1, 'extra_two': 2}

        node.set_extra_many(extras)
        assert set(extras) == set(node.extras_keys())

        # Repeat for a stored node
        node = self.create_node().store()
        extras = {'extra_one': 1, 'extra_two': 2}

        node.set_extra_many(extras)
        assert set(extras) == set(node.extras_keys())

    def test_extra_flush_specifically(self):
        """Test that changing `extras` only flushes that property and does not affect others like attributes.

        Regression fix for #3338
        """
        node = self.create_node().store()
        attributes = {'attribute_one': 1, 'attribute_two': 2}
        node.set_attribute_many(attributes)
        node.store()

        # Load the stored node in memory in another instance and add another attribute
        reloaded = self.backend.nodes.get(node.pk)
        reloaded.set_attribute('attribute_three', 3)

        # The original memory instance should now not include `attribute_three`. Changing an extra should only flush
        # the extras and not the whole node state, which would override for example also the attributes.
        node.set_extra('extra_one', 1)

        # Reload the node yet again and verify that the `attribute_three` attribute is still there
        rereloaded = self.backend.nodes.get(node.pk)
        assert 'attribute_three' in rereloaded.attributes.keys()
