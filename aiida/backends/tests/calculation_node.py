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
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm.calculation import Calculation


class TestCalcNode(AiidaTestCase):
    """
    These tests check the features of Calculation nodes that differ from the
    base Node type
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
        super(TestCalcNode, cls).setUpClass()
        from aiida.orm import JobCalculation

        cls.construction_options = {
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }
        }

        cls.job_calculation = JobCalculation()
        cls.job_calculation.set_computer(cls.computer)
        cls.job_calculation.set_options(cls.construction_options)
        cls.job_calculation.store()

    def test_process_state(self):
        """
        Check the properties of a newly created bare Calculation
        """
        calculation = Calculation()

        self.assertEquals(calculation.is_terminated, False)
        self.assertEquals(calculation.is_excepted, False)
        self.assertEquals(calculation.is_killed, False)
        self.assertEquals(calculation.is_finished, False)
        self.assertEquals(calculation.is_finished_ok, False)
        self.assertEquals(calculation.is_failed, False)

    def test_calculation_updatable_attribute(self):
        """
        Check that updatable attributes and only those can be mutated for a stored but unsealed Calculation
        """
        a = Calculation()
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
        a._set_attr(Calculation.PROCESS_STATE_KEY, self.stateval)
        self.assertEquals(a.get_attr(Calculation.PROCESS_STATE_KEY), self.stateval)

        a.store()

        # Check after storing
        self.assertEquals(a.get_attr(Calculation.PROCESS_STATE_KEY), self.stateval)

        # I should be able to mutate the updatable attribute but not the others
        a._set_attr(Calculation.PROCESS_STATE_KEY, 'FINISHED')
        a._del_attr(Calculation.PROCESS_STATE_KEY)

        # Deleting non-existing attribute should raise attribute error
        with self.assertRaises(AttributeError):
            a._del_attr(Calculation.PROCESS_STATE_KEY)

        with self.assertRaises(ModificationNotAllowed):
            a._set_attr('bool', False)

        with self.assertRaises(ModificationNotAllowed):
            a._del_attr('bool')

        a.seal()

        # After sealing, even updatable attributes should be immutable
        with self.assertRaises(ModificationNotAllowed):
            a._set_attr(Calculation.PROCESS_STATE_KEY, 'FINISHED')

        with self.assertRaises(ModificationNotAllowed):
            a._del_attr(Calculation.PROCESS_STATE_KEY)

    def test_job_calculation_get_option(self):
        """Verify that options used during calculation construction can be retrieved with `get_option`."""
        for name, attributes in self.job_calculation.options.items():

            if name in self.construction_options:
                self.assertEqual(self.job_calculation.get_option(name), self.construction_options[name])

    def test_job_calculation_get_options_only_actually_set(self):
        """Verify that `get_options only` returns explicitly set options if `only_actually_set=True`."""
        set_options = self.job_calculation.get_options(only_actually_set=True)
        self.assertEquals(set(set_options.keys()), set(self.construction_options.keys()))

    def test_job_calculation_get_options_defaults(self):
        """Verify that `get_options` returns all options with defaults if `only_actually_set=False`."""
        get_options = self.job_calculation.get_options()

        for name, attributes in self.job_calculation.options.items():

            # If the option was specified in construction options, verify that `get_options` returns same value
            if name in self.construction_options:
                self.assertEqual(get_options[name], self.construction_options[name])

            # Otherwise, if the option defines a default that is not `None`, verify that that is returned correctly
            elif 'default' in attributes and attributes['default'] is not None:
                self.assertEqual(get_options[name], attributes['default'])
