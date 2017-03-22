# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for calculation nodes, attributes and links
"""

from aiida.common.exceptions import ModificationNotAllowed
from aiida.backends.testbase import AiidaTestCase


class TestCalcNode(AiidaTestCase):
    """
    These tests check the features of Calculation nodes that differ from the
    base Node type
    """
    boolval = True
    intval = 123
    floatval = 4.56
    stringval = "aaaa"
    # A recursive dictionary
    dictval = {'num': 3, 'something': 'else', 'emptydict': {},
               'recursive': {'a': 1, 'b': True, 'c': 1.2, 'd': [1, 2, None],
                             'e': {'z': 'z', 'x': None, 'xx': {}, 'yy': []}}}
    listval = [1, "s", True, None]
    emptydict = {}
    emptylist = []

    def test_updatable_not_copied(self):
        """
        Checks the versioning.
        """
        from aiida.orm.test import myNodeWithFields

        # Has 'state' as updatable attribute
        a = myNodeWithFields()
        a._set_attr('state', 267)
        a.store()
        b = a.copy()

        # updatable attributes are not copied
        with self.assertRaises(AttributeError):
            b.get_attr('state')

    def test_delete_updatable_attributes(self):
        """
        Checks the versioning.
        """
        from aiida.orm.test import myNodeWithFields

        # Has 'state' as updatable attribute
        a = myNodeWithFields()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'state': 267,  # updatable
        }

        for k, v in attrs_to_set.iteritems():
            a._set_attr(k, v)

        # Check before storing
        self.assertEquals(267, a.get_attr('state'))

        a.store()

        # Check after storing
        self.assertEquals(267, a.get_attr('state'))

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a.dbnode.nodeversion, 1)

        # I should be able to delete the attribute
        a._del_attr('state')

        # I check increment on new version
        self.assertEquals(a.dbnode.nodeversion, 2)

        with self.assertRaises(AttributeError):
            # I check that I cannot modify this attribute
            _ = a.get_attr('state')

    def test_versioning_and_updatable_attributes(self):
        """
        Checks the versioning.
        """
        from aiida.orm.test import myNodeWithFields

        # Has 'state' as updatable attribute
        a = myNodeWithFields()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'state': 267,
        }

        expected_version = 1

        for k, v in attrs_to_set.iteritems():
            a._set_attr(k, v)

        # Check before storing
        self.assertEquals(267, a.get_attr('state'))

        a.store()

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a.dbnode.nodeversion, expected_version)

        # Sealing ups the version number
        a.seal()
        expected_version += 1
        self.assertEquals(a.dbnode.nodeversion, expected_version)

        # Check after storing
        self.assertEquals(267, a.get_attr('state'))
        self.assertEquals(a.dbnode.nodeversion, expected_version)

        # I check increment on new version
        a.set_extra('a', 'b')
        expected_version += 1
        self.assertEquals(a.dbnode.nodeversion, expected_version)

        # I check that I can set this attribute
        a._set_attr('state', 999)
        expected_version += 1

        # I check increment on new version
        self.assertEquals(a.dbnode.nodeversion, expected_version)

        with self.assertRaises(ModificationNotAllowed):
            # I check that I cannot modify this attribute
            a._set_attr('otherattribute', 222)

        # I check that the counter was not incremented
        self.assertEquals(a.dbnode.nodeversion, expected_version)

        # In both cases, the node version must increase
        a.label = 'test'
        expected_version += 1
        self.assertEquals(a.dbnode.nodeversion, expected_version)

        a.description = 'test description'
        expected_version += 1
        self.assertEquals(a.dbnode.nodeversion, expected_version)

        b = a.copy()
        # updatable attributes are not copied
        with self.assertRaises(AttributeError):
            b.get_attr('state')
