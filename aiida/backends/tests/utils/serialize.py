# -*- coding: utf-8 -*-
from aiida.orm import Node
from aiida.utils.serialize import serialize_data, deserialize_data
from aiida.backends.testbase import AiidaTestCase


class TestSerialize(AiidaTestCase):

    def test_serialize_round_trip(self):
        """
        """
        node_a = Node().store()
        node_b = Node().store()

        data = {
            'test': 1,
            'list': (1, 2, 3, node_a),
            'dict': {
                ('Si',): node_b,
                'foo': 'bar'
            },
            'baz': 'aar'
        }

        serialized_data = serialize_data(data)
        deserialized_data = deserialize_data(serialized_data)

        # For now manual element-for-element comparison until we come up with general
        # purpose function that can equate two node instances properly
        self.assertEqual(data['test'], deserialized_data['test'])
        self.assertEqual(data['baz'], deserialized_data['baz'])
        self.assertEqual(data['list'][:3], deserialized_data['list'][:3])
        self.assertEqual(data['list'][3].uuid, deserialized_data['list'][3].uuid)
        self.assertEqual(data['dict'][('Si',)].uuid, deserialized_data['dict'][('Si',)].uuid)
