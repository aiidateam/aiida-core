# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Serialization tests"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida import orm
from aiida.orm.utils import serialize
from aiida.backends.testbase import AiidaTestCase

# pylint: disable=missing-docstring


class TestSerialize(AiidaTestCase):

    def test_serialize_round_trip(self):
        """
        Test the serialization of a dictionary with Nodes in various data structure
        Also make sure that the serialized data is json-serializable
        """
        node_a = orm.Data().store()
        node_b = orm.Data().store()

        data = {'test': 1, 'list': [1, 2, 3, node_a], 'dict': {('Si',): node_b, 'foo': 'bar'}, 'baz': 'aar'}

        serialized_data = serialize.serialize(data)
        deserialized_data = serialize.deserialize(serialized_data)

        # For now manual element-for-element comparison until we come up with general
        # purpose function that can equate two node instances properly
        self.assertEqual(data['test'], deserialized_data['test'])
        self.assertEqual(data['baz'], deserialized_data['baz'])
        self.assertEqual(data['list'][:3], deserialized_data['list'][:3])
        self.assertEqual(data['list'][3].uuid, deserialized_data['list'][3].uuid)
        self.assertEqual(data['dict'][('Si',)].uuid, deserialized_data['dict'][('Si',)].uuid)

    def test_serialize_group(self):
        """
        Test that serialization and deserialization of Groups works.
        Also make sure that the serialized data is json-serializable
        """
        group_name = 'groupie'
        group_a = orm.Group(label=group_name).store()

        data = {'group': group_a}

        serialized_data = serialize.serialize(data)
        deserialized_data = serialize.deserialize(serialized_data)

        self.assertEqual(data['group'].uuid, deserialized_data['group'].uuid)
        self.assertEqual(data['group'].label, deserialized_data['group'].label)

    def test_serialize_node_round_trip(self):
        """Test you can serialize and deserialize a node"""
        node = orm.Data().store()
        deserialized = serialize.deserialize(serialize.serialize(node))
        self.assertEqual(node.uuid, deserialized.uuid)

    def test_serialize_group_round_trip(self):
        """Test you can serialize and deserialize a group"""
        group = orm.Group(label='test_serialize_group_round_trip').store()
        deserialized = serialize.deserialize(serialize.serialize(group))

        self.assertEqual(group.uuid, deserialized.uuid)
        self.assertEqual(group.label, deserialized.label)

    def test_serialize_computer_round_trip(self):
        """Test you can serialize and deserialize a computer"""
        computer = self.computer
        deserialized = serialize.deserialize(serialize.serialize(computer))

        # pylint: disable=no-member
        self.assertEqual(computer.uuid, deserialized.uuid)
        self.assertEqual(computer.name, deserialized.name)

    def test_serialize_unstored_node(self):
        """Test that you can't serialize an unstored node"""
        node = orm.Data()

        with self.assertRaises(ValueError):
            serialize.serialize(node)

    def test_serialize_unstored_group(self):
        """Test that you can't serialize an unstored group"""
        group = orm.Group(label='test_serialize_unstored_group')

        with self.assertRaises(ValueError):
            serialize.serialize(group)

    def test_serialize_unstored_computer(self):
        """Test that you can't serialize an unstored node"""
        computer = orm.Computer('test_computer', 'test_host')

        with self.assertRaises(ValueError):
            serialize.serialize(computer)
