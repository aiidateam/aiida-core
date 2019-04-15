# -*- coding: utf-8 -*-

import unittest
from aiida.common.extendeddicts import DefaultsDict


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

class TestDefaultsDict(unittest.TestCase):
    def setUp(self):
        self.defaults_dict = DefaultsDict(
            valid_keys=['foo', 'bar'],
            defaults={'bar': 'bar_default'})

    def test_setattr(self):
        # Test setting and getting a value
        self.defaults_dict.foo = 'hello'
        self.assertEqual(self.defaults_dict.foo, 'hello')

        # Test setting an invalid attribute
        with self.assertRaises(AttributeError):
            self.defaults_dict.non_existent = None

    def test_defaults(self):
        self.assertEquals(self.defaults_dict.defaults, {'bar': 'bar_default'})

    def test_getattr(self):
        # Test getting an unset value
        with self.assertRaises(AttributeError):
            self.defaults_dict.unset

    def test_delattr(self):
        self.defaults_dict.foo = 'hello'
        del self.defaults_dict.foo
        # Now try deleting it again
        with self.assertRaises(AttributeError):
            del self.defaults_dict.foo

        # Try deleting one that never existed
        with self.assertRaises(AttributeError):
            del self.defaults_dict.foo

    def test_delitem(self):
        self.defaults_dict['foo'] = 'test'
        del self.defaults_dict['foo']
        # Try deleting again
        with self.assertRaises(KeyError):
            del self.defaults_dict['foo']

        # Try deleting on that never existed
        with self.assertRaises(KeyError):
            del self.defaults_dict['non_existent']

    def test_invalid_default(self):
        with self.assertRaises(AssertionError):
            DefaultsDict([], defaults={'foo': 'bar'})

if __name__ == '__main__':
    unittest.main()
