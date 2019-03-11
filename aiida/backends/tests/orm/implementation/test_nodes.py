# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the BackendNode and BackendNodeCollection classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from datetime import datetime
from uuid import UUID

from aiida.backends.testbase import AiidaTestCase
from aiida.common import timezone


class TestBackendNode(AiidaTestCase):
    """Test BackendNode."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestBackendNode, cls).setUpClass(*args, **kwargs)
        cls.computer = cls.computer.backend_entity  # Unwrap the `Computer` instance to `BackendComputer`
        cls.user = cls.backend.users.create(email='tester@localhost').store()

    def setUp(self):
        super(TestBackendNode, self).setUp()
        self.node_type = ''
        self.node_label = 'label'
        self.node_description = 'description'
        self.node = self.backend.nodes.create(
            node_type=self.node_type,
            user=self.user,
            computer=self.computer,
            label=self.node_label,
            description=self.node_description)

    def test_creation(self):
        """Test creation of a BackendNode and all its properties."""
        node = self.backend.nodes.create(
            node_type=self.node_type, user=self.user, label=self.node_label, description=self.node_description)

        # Before storing
        self.assertIsNone(node.id)
        self.assertIsNone(node.pk)
        self.assertTrue(isinstance(node.uuid, str))
        self.assertTrue(isinstance(node.ctime, datetime))
        self.assertIsNone(node.mtime)
        self.assertIsNone(node.process_type)
        self.assertEqual(node.public, False)
        self.assertEqual(node.version, 1)
        self.assertEqual(node.attributes, dict())
        self.assertEqual(node.extras, dict())
        self.assertEqual(node.node_type, self.node_type)
        self.assertEqual(node.label, self.node_label)
        self.assertEqual(node.description, self.node_description)

        # Store the node.ctime before the store as a reference
        now = timezone.now()
        node_ctime_before_store = node.ctime
        self.assertTrue(now > node.ctime, '{} is not smaller than now {}'.format(node.ctime, now))

        node.store()
        node_ctime = node.ctime
        node_mtime = node.mtime

        # The node.ctime should have been unchanged, but the node.mtime should have changed
        self.assertEqual(node.ctime, node_ctime_before_store)
        self.assertIsNotNone(node.mtime)
        self.assertTrue(now < node.mtime, '{} is not larger than now {}'.format(node.mtime, now))

        # After storing
        self.assertTrue(isinstance(node.id, int))
        self.assertTrue(isinstance(node.pk, int))
        self.assertTrue(isinstance(node.uuid, str))
        self.assertTrue(isinstance(node.ctime, datetime))
        self.assertTrue(isinstance(node.mtime, datetime))
        self.assertIsNone(node.process_type)
        self.assertEqual(node.public, False)
        self.assertEqual(node.version, 1)
        self.assertEqual(node.attributes, dict())
        self.assertEqual(node.extras, dict())
        self.assertEqual(node.node_type, self.node_type)
        self.assertEqual(node.label, self.node_label)
        self.assertEqual(node.description, self.node_description)

        # Try to construct a UUID from the UUID value to prove that it has a valid UUID
        UUID(node.uuid)

        # Change a column, which should trigger the save, update the mtime and version, but leave the ctime untouched
        node.label = 'test'
        self.assertEqual(node.ctime, node_ctime)
        self.assertTrue(node.mtime > node_mtime)
        self.assertEqual(node.version, 2)

    def test_creation_with_time(self):
        """
        Test creation of a BackendNode when passing the mtime and the ctime. The passed ctime and mtime
        should be respected since it is important for the correct import of nodes at the AiiDA import/export.
        """
        from aiida.orm.importexport import deserialize_attributes

        ctime = deserialize_attributes('2019-02-27T16:20:12.245738', 'date')
        mtime = deserialize_attributes('2019-02-27T16:27:14.798838', 'date')

        node = self.backend.nodes.create(
            node_type=self.node_type,
            user=self.user,
            label=self.node_label,
            description=self.node_description,
            mtime=mtime,
            ctime=ctime)

        # Check that the ctime and mtime are the given ones
        self.assertEqual(node.ctime, ctime)
        self.assertEqual(node.mtime, mtime)

        node.store()

        # Check that the given values remain even after storing
        self.assertEqual(node.ctime, ctime)
        self.assertEqual(node.mtime, mtime)

    def test_clone(self):
        """Test the `clone` method."""
        node = self.node.store()
        clone = node.clone()

        # Check that the clone is unstored, i.e. has *no* id, has a different UUID, but all other props are the same
        self.assertIsNone(clone.id)
        self.assertNotEqual(clone.uuid, node.uuid)
        self.assertEqual(clone.label, node.label)
        self.assertEqual(clone.description, node.description)
        self.assertEqual(clone.user.id, node.user.id)
        self.assertEqual(clone.computer.id, node.computer.id)
        self.assertEqual(clone.attributes, node.attributes)
        self.assertEqual(clone.extras, node.extras)

    def test_property_setters(self):
        """Test the property setters of a BackendNode."""
        label = 'new label'
        description = 'new description'

        self.node.label = label
        self.node.description = description

        self.assertEqual(self.node.label, label)
        self.assertEqual(self.node.description, description)

    def test_computer_methods(self):
        """Test the computer methods of a BackendNode."""
        new_computer = self.backend.computers.create(name='localhost2', hostname='localhost').store()
        self.assertEqual(self.node.computer.id, self.computer.id)
        self.node.computer = new_computer
        self.assertEqual(self.node.computer.id, new_computer.id)

    def test_user_methods(self):
        """Test the user methods of a BackendNode."""
        new_user = self.backend.users.create(email='newuser@localhost').store()
        self.assertEqual(self.node.user.id, self.user.id)
        self.node.user = new_user
        self.assertEqual(self.node.user.id, new_user.id)

    def test_attributes(self):
        """Test the attribute properties of a BackendNode."""
        attribute_name = 'attribute'
        attribute_value = 'nobatnight'

        with self.assertRaises(AttributeError):
            self.node.get_attribute(attribute_name)

        self.assertEqual(self.node.attributes, dict())

        self.node.store()
        self.node.set_attribute(attribute_name, attribute_value)
        self.assertEqual(self.node.get_attribute(attribute_name), attribute_value)

        self.node.delete_attribute(attribute_name)

        with self.assertRaises(AttributeError):
            self.node.get_attribute(attribute_name)

    def test_extras(self):
        """Test the extra properties of a BackendNode."""
        extra_name = 'extra'
        extra_value = 'nobatnight'

        with self.assertRaises(AttributeError):
            self.node.get_extra(extra_name)

        self.node.store()
        self.node.set_extra(extra_name, extra_value)
        self.assertEqual(self.node.get_extra(extra_name), extra_value)

        self.node.delete_extra(extra_name)

        with self.assertRaises(AttributeError):
            self.node.get_extra(extra_name)
