# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import NotExistent
from aiida.orm import Node, Group, Data
from aiida.orm.utils import load_entity, load_code, load_computer, load_group, load_node
from aiida.orm.utils.loaders import NodeEntityLoader


class TestOrmUtils(AiidaTestCase):

    def test_load_entiy(self):
        """Test the functionality of load_entity which is the base function for the other loader functions."""
        entity_loader = NodeEntityLoader

        with self.assertRaises(TypeError):
            load_entity(entity_loader=None)

        # No identifier keyword arguments specified
        with self.assertRaises(ValueError):
            load_entity(entity_loader)

        # More than one identifier keyword arguments specified
        with self.assertRaises(ValueError):
            load_entity(entity_loader, identifier='a', pk=1)

        with self.assertRaises(TypeError):
            load_entity(entity_loader, pk='1')

        with self.assertRaises(TypeError):
            load_entity(entity_loader, uuid=1)

        with self.assertRaises(TypeError):
            load_entity(entity_loader, label=1)

    def test_load_code(self):
        """Test the functionality of load_code."""
        from aiida.orm import Code

        label = 'compy'
        code = Code()
        code.label = label
        code.set_remote_computer_exec((self.computer, '/x.x'))
        code.store()

        # Load through full label
        loaded_code = load_code(code.full_label)
        self.assertEquals(loaded_code.uuid, code.uuid)

        # Load through label
        loaded_code = load_code(code.label)
        self.assertEquals(loaded_code.uuid, code.uuid)

        # Load through uuid
        loaded_code = load_code(code.uuid)
        self.assertEquals(loaded_code.uuid, code.uuid)

        # Load through pk
        loaded_code = load_code(code.pk)
        self.assertEquals(loaded_code.uuid, code.uuid)

        # Load through full label explicitly
        loaded_code = load_code(label=code.full_label)
        self.assertEquals(loaded_code.uuid, code.uuid)

        # Load through label explicitly
        loaded_code = load_code(label=code.label)
        self.assertEquals(loaded_code.uuid, code.uuid)

        # Load through uuid explicitly
        loaded_code = load_code(uuid=code.uuid)
        self.assertEquals(loaded_code.uuid, code.uuid)

        # Load through pk explicitly
        loaded_code = load_code(pk=code.pk)
        self.assertEquals(loaded_code.uuid, code.uuid)

        # Load through partial uuid without a dash
        loaded_code = load_code(uuid=code.uuid[:8])
        self.assertEquals(loaded_code.uuid, code.uuid)

        # Load through partial uuid including a dash
        loaded_code = load_code(uuid=code.uuid[:10])
        self.assertEquals(loaded_code.uuid, code.uuid)

        with self.assertRaises(NotExistent):
            load_code('non-existent-uuid')

    def test_load_computer(self):
        """Test the functionality of load_group."""
        computer = self.computer

        # Load through label
        loaded_computer = load_computer(computer.label)
        self.assertEquals(loaded_computer.uuid, computer.uuid)

        # Load through uuid
        loaded_computer = load_computer(computer.uuid)
        self.assertEquals(loaded_computer.uuid, computer.uuid)

        # Load through pk
        loaded_computer = load_computer(computer.pk)
        self.assertEquals(loaded_computer.uuid, computer.uuid)

        # Load through label explicitly
        loaded_computer = load_computer(label=computer.label)
        self.assertEquals(loaded_computer.uuid, computer.uuid)

        # Load through uuid explicitly
        loaded_computer = load_computer(uuid=computer.uuid)
        self.assertEquals(loaded_computer.uuid, computer.uuid)

        # Load through pk explicitly
        loaded_computer = load_computer(pk=computer.pk)
        self.assertEquals(loaded_computer.uuid, computer.uuid)

        # Load through partial uuid without a dash
        loaded_computer = load_computer(uuid=computer.uuid[:8])
        self.assertEquals(loaded_computer.uuid, computer.uuid)

        # Load through partial uuid including a dash
        loaded_computer = load_computer(uuid=computer.uuid[:10])
        self.assertEquals(loaded_computer.uuid, computer.uuid)

        with self.assertRaises(NotExistent):
            load_computer('non-existent-uuid')

    def test_load_group(self):
        """Test the functionality of load_group."""
        name = 'groupie'
        group = Group(label=name).store()

        # Load through label
        loaded_group = load_group(group.label)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through uuid
        loaded_group = load_group(group.uuid)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through pk
        loaded_group = load_group(group.pk)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through label explicitly
        loaded_group = load_group(label=group.label)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through uuid explicitly
        loaded_group = load_group(uuid=group.uuid)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through pk explicitly
        loaded_group = load_group(pk=group.pk)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through partial uuid without a dash
        loaded_group = load_group(uuid=group.uuid[:8])
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through partial uuid including a dash
        loaded_group = load_group(uuid=group.uuid[:10])
        self.assertEquals(loaded_group.uuid, group.uuid)

        with self.assertRaises(NotExistent):
            load_group('non-existent-uuid')

    def test_load_node(self):
        """Test the functionality of load_node."""
        node = Data().store()

        # Load through uuid
        loaded_node = load_node(node.uuid)
        self.assertIsInstance(loaded_node, Node)
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through pk
        loaded_node = load_node(node.pk)
        self.assertIsInstance(loaded_node, Node)
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through uuid explicitly
        loaded_node = load_node(uuid=node.uuid)
        self.assertIsInstance(loaded_node, Node)
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through pk explicitly
        loaded_node = load_node(pk=node.pk)
        self.assertIsInstance(loaded_node, Node)
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through partial uuid without a dash
        loaded_node = load_node(uuid=node.uuid[:8])
        self.assertIsInstance(loaded_node, Node)
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through partial uuid including a dashs
        loaded_node = load_node(uuid=node.uuid[:10])
        self.assertIsInstance(loaded_node, Node)
        self.assertEquals(loaded_node.uuid, node.uuid)

        with self.assertRaises(NotExistent):
            load_group('non-existent-uuid')
