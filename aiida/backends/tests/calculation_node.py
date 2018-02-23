# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

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

    def test_calculation_updatable_not_copied(self):
        """
        Check that updatable attributes of Calculation are not copied
        """
        a = Calculation()
        a._set_attr('state', self.stateval)
        a.store()
        b = a.copy()

        # updatable attributes are not copied
        with self.assertRaises(AttributeError):
            b.get_attr('state')

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

        for k, v in attrs_to_set.iteritems():
            a._set_attr(k, v)

        # Check before storing
        self.assertEquals(a.get_attr('state'), self.stateval)

        a.store()

        # Check after storing
        self.assertEquals(a.get_attr('state'), self.stateval)

        # I should be able to mutate the updatable attribute but not the others
        a._set_attr('state', 'FINISHED')
        a._del_attr('state')

        with self.assertRaises(ModificationNotAllowed):
            a._set_attr('bool', False)

        with self.assertRaises(ModificationNotAllowed):
            a._del_attr('bool')

        a.seal()

        # After sealing, even updatable attributes should be immutable
        with self.assertRaises(ModificationNotAllowed):
            a._set_attr('state', 'FINISHED')

        with self.assertRaises(ModificationNotAllowed):
            a._del_attr('state')