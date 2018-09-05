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
import json
from aiida.orm import Group, Node
from aiida.utils.serialize import serialize_data, deserialize_data
from aiida.backends.testbase import AiidaTestCase


class TestSerialize(AiidaTestCase):

    def test_serialize_round_trip(self):
        """
        Test the serialization of a dictionary with Nodes in various data structure
        Also make sure that the serialized data is json-serializable
        """
        node_a = Node().store()
        node_b = Node().store()

        data = {
            'test': 1,
            'list': [1, 2, 3, node_a],
            'dict': {
                ('Si',): node_b,
                'foo': 'bar'
            },
            'baz': 'aar'
        }

        serialized_data = serialize_data(data)
        json_dumped = json.dumps(serialized_data)
        deserialized_data = deserialize_data(serialized_data)

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
        group_a = Group(name=group_name).store()

        data = {
            'group': group_a
        }

        serialized_data = serialize_data(data)
        json_dumped = json.dumps(serialized_data)
        deserialized_data = deserialize_data(serialized_data)

        self.assertEqual(data['group'].uuid, deserialized_data['group'].uuid)
        self.assertEqual(data['group'].name, deserialized_data['group'].name)