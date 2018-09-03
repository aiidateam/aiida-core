# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import NotExistent
from aiida.orm import Group, Node
from aiida.orm.utils import load_group, load_node


class TestOrmUtils(AiidaTestCase):

    def test_load_group(self):
        """
        Test the functionality of load_group
        """
        name = 'groupie'
        group = Group(name=name).store()

        # Load through uuid
        loaded_group = load_group(group.uuid)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through pk
        loaded_group = load_group(group.pk)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through uuid explicitly
        loaded_group = load_group(uuid=group.uuid)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through pk explicitly
        loaded_group = load_group(pk=group.pk)
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through partial uuid
        loaded_group = load_group(uuid=group.uuid[:2])
        self.assertEquals(loaded_group.uuid, group.uuid)

        # Load through partial uuid
        loaded_group = load_group(uuid=group.uuid[:10])
        self.assertEquals(loaded_group.uuid, group.uuid)

        with self.assertRaises(NotExistent):
            load_group('non-existent-uuid')

    def test_load_node(self):
        """
        Test the functionality of load_node
        """
        node = Node().store()

        # Load through uuid
        loaded_node = load_node(node.uuid)
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through pk
        loaded_node = load_node(node.pk)
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through uuid explicitly
        loaded_node = load_node(uuid=node.uuid)
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through pk explicitly
        loaded_node = load_node(pk=node.pk)
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through partial uuid
        loaded_node = load_node(uuid=node.uuid[:2])
        self.assertEquals(loaded_node.uuid, node.uuid)

        # Load through partial uuid
        loaded_node = load_node(uuid=node.uuid[:10])
        self.assertEquals(loaded_node.uuid, node.uuid)

        with self.assertRaises(NotExistent):
            load_group('non-existent-uuid')
