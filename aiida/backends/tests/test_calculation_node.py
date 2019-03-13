# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the CalculationNode and CalcJobNode class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm import CalculationNode, CalcJobNode


class TestProcessNode(AiidaTestCase):
    """
    These tests check the features of process nodes that differ from the base Node type
    """
    boolval = True
    intval = 123
    floatval = 4.56
    stringval = 'aaaa'
    listval = [1, 's', True, None]
    dictval = {
        'num': 3,
        'something': 'else',
        'emptydict': {},
        'recursive': {
            'integer': 1,
            'boolean': True,
            'float': 1.2,
            'list': [1, 2, None],
            'dictionary': {
                'string': 'z',
                'none': None,
                'empty_dictionary': {},
                'empty_list': []
            }
        }
    }
    stateval = 'RUNNING'
    emptydict = {}
    emptylist = []

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestProcessNode, cls).setUpClass(*args, **kwargs)
        cls.computer.configure()  # pylint: disable=no-member
        cls.construction_options = {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}

        cls.calcjob = CalcJobNode()
        cls.calcjob.computer = cls.computer
        cls.calcjob.set_options(cls.construction_options)
        cls.calcjob.store()

    def test_process_state(self):
        """
        Check the properties of a newly created bare CalculationNode
        """
        process_node = CalculationNode()

        self.assertEqual(process_node.is_terminated, False)
        self.assertEqual(process_node.is_excepted, False)
        self.assertEqual(process_node.is_killed, False)
        self.assertEqual(process_node.is_finished, False)
        self.assertEqual(process_node.is_finished_ok, False)
        self.assertEqual(process_node.is_failed, False)

    def test_process_node_updatable_attribute(self):
        """Check that updatable attributes and only those can be mutated for a stored but unsealed CalculationNode."""
        node = CalculationNode()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'state': self.stateval
        }

        for key, value in attrs_to_set.items():
            node.set_attribute(key, value)

        # Check before storing
        node.set_attribute(CalculationNode.PROCESS_STATE_KEY, self.stateval)
        self.assertEqual(node.get_attribute(CalculationNode.PROCESS_STATE_KEY), self.stateval)

        node.store()

        # Check after storing
        self.assertEqual(node.get_attribute(CalculationNode.PROCESS_STATE_KEY), self.stateval)

        # I should be able to mutate the updatable attribute but not the others
        node.set_attribute(CalculationNode.PROCESS_STATE_KEY, 'FINISHED')
        node.delete_attribute(CalculationNode.PROCESS_STATE_KEY)

        # Deleting non-existing attribute should raise attribute error
        with self.assertRaises(AttributeError):
            node.delete_attribute(CalculationNode.PROCESS_STATE_KEY)

        with self.assertRaises(ModificationNotAllowed):
            node.set_attribute('bool', False)

        with self.assertRaises(ModificationNotAllowed):
            node.delete_attribute('bool')

        node.seal()

        # After sealing, even updatable attributes should be immutable
        with self.assertRaises(ModificationNotAllowed):
            node.set_attribute(CalculationNode.PROCESS_STATE_KEY, 'FINISHED')

        with self.assertRaises(ModificationNotAllowed):
            node.delete_attribute(CalculationNode.PROCESS_STATE_KEY)

    def test_get_description(self):
        self.assertEqual(self.calcjob.get_description(), self.calcjob.get_state())

    def test_get_authinfo(self):
        """Test that we can get the AuthInfo object from the calculation instance."""
        from aiida.orm import AuthInfo
        authinfo = self.calcjob.get_authinfo()
        self.assertIsInstance(authinfo, AuthInfo)

    def test_get_transport(self):
        """Test that we can get the Transport object from the calculation instance."""
        from aiida.transports import Transport
        transport = self.calcjob.get_transport()
        self.assertIsInstance(transport, Transport)
