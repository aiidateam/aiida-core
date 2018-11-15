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
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm.node.process import ProcessNode


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
        'num': 3, 'something': 'else', 'emptydict': {},
        'recursive': {
            'a': 1, 'b': True, 'c': 1.2, 'd': [1, 2, None],
            'e': {
                'z': 'z', 'x': None, 'xx': {}, 'yy': []
            }
        }
    }
    stateval = 'RUNNING'
    emptydict = {}
    emptylist = []

    @classmethod
    def setUpClass(cls):
        super(TestProcessNode, cls).setUpClass()
        from aiida.orm.node.process import CalcJobNode

        cls.construction_options = {
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }
        }

        cls.calcjob = CalcJobNode()
        cls.calcjob.set_computer(cls.computer)
        cls.calcjob.set_options(cls.construction_options)
        cls.calcjob.store()

    def test_process_state(self):
        """
        Check the properties of a newly created bare ProcessNode
        """
        process_node = ProcessNode()

        self.assertEquals(process_node.is_terminated, False)
        self.assertEquals(process_node.is_excepted, False)
        self.assertEquals(process_node.is_killed, False)
        self.assertEquals(process_node.is_finished, False)
        self.assertEquals(process_node.is_finished_ok, False)
        self.assertEquals(process_node.is_failed, False)

    def test_process_node_updatable_attribute(self):
        """
        Check that updatable attributes and only those can be mutated for a stored but unsealed ProcessNode
        """
        a = ProcessNode()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'state': self.stateval
        }

        for k, v in attrs_to_set.items():
            a._set_attr(k, v)

        # Check before storing
        a._set_attr(ProcessNode.PROCESS_STATE_KEY, self.stateval)
        self.assertEquals(a.get_attr(ProcessNode.PROCESS_STATE_KEY), self.stateval)

        a.store()

        # Check after storing
        self.assertEquals(a.get_attr(ProcessNode.PROCESS_STATE_KEY), self.stateval)

        # I should be able to mutate the updatable attribute but not the others
        a._set_attr(ProcessNode.PROCESS_STATE_KEY, 'FINISHED')
        a._del_attr(ProcessNode.PROCESS_STATE_KEY)

        # Deleting non-existing attribute should raise attribute error
        with self.assertRaises(AttributeError):
            a._del_attr(ProcessNode.PROCESS_STATE_KEY)

        with self.assertRaises(ModificationNotAllowed):
            a._set_attr('bool', False)

        with self.assertRaises(ModificationNotAllowed):
            a._del_attr('bool')

        a.seal()

        # After sealing, even updatable attributes should be immutable
        with self.assertRaises(ModificationNotAllowed):
            a._set_attr(ProcessNode.PROCESS_STATE_KEY, 'FINISHED')

        with self.assertRaises(ModificationNotAllowed):
            a._del_attr(ProcessNode.PROCESS_STATE_KEY)

    def test_calcjob_get_option(self):
        """Verify that options used during process_node construction can be retrieved with `get_option`."""
        for name, attributes in self.calcjob.options.items():

            if name in self.construction_options:
                self.assertEqual(self.calcjob.get_option(name), self.construction_options[name])

    def test_calcjob_get_options_only_actually_set(self):
        """Verify that `get_options only` returns explicitly set options if `only_actually_set=True`."""
        set_options = self.calcjob.get_options(only_actually_set=True)
        self.assertEquals(set(set_options.keys()), set(self.construction_options.keys()))

    def test_calcjob_get_options_defaults(self):
        """Verify that `get_options` returns all options with defaults if `only_actually_set=False`."""
        get_options = self.calcjob.get_options()

        for name, attributes in self.calcjob.options.items():

            # If the option was specified in construction options, verify that `get_options` returns same value
            if name in self.construction_options:
                self.assertEqual(get_options[name], self.construction_options[name])

            # Otherwise, if the option defines a default that is not `None`, verify that that is returned correctly
            elif 'default' in attributes and attributes['default'] is not None:
                self.assertEqual(get_options[name], attributes['default'])
