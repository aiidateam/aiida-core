# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.common.extendeddicts import *
import unittest
import copy



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


class TestFFADExample(FixedFieldsAttributeDict):
    """
    An example class that accepts only the 'a', 'b' and 'c' keys/attributes.
    """
    _valid_fields = ('a', 'b', 'c')


class TestDFADExample(DefaultFieldsAttributeDict):
    """
    An example class that has 'a', 'b' and 'c' as default keys.
    """
    _default_fields = ('a', 'b', 'c')

    def validate_a(self, value):
        # Ok if unset
        if value is None:
            return

        if not isinstance(value, (int, long)):
            raise TypeError('expecting integer')
        if value < 0:
            raise ValueError('expecting a positive or zero value')


class TestAttributeDictAccess(unittest.TestCase):
    """
    Try to access the dictionary elements in various ways, copying (shallow and
    deep), check raised exceptions.
    """

    def test_access_dict_to_attr(self):
        d = AttributeDict()
        d['test'] = 'abc'
        self.assertEquals(d.test, 'abc')

    def test_access_attr_to_dict(self):
        d = AttributeDict()
        d.test = 'def'
        self.assertEquals(d['test'], 'def')

    def test_access_nonexisting_asattr(self):
        d = AttributeDict()
        with self.assertRaises(AttributeError):
            a = d.test

    def test_access_nonexisting_askey(self):
        d = AttributeDict()
        with self.assertRaises(KeyError):
            a = d['test']

    def test_del_nonexisting_askey(self):
        d = AttributeDict()
        with self.assertRaises(KeyError):
            del d['test']

    def test_del_nonexisting_asattr(self):
        d = AttributeDict()
        with self.assertRaises(AttributeError):
            del d.test

    def test_copy(self):
        d1 = AttributeDict()
        d1.x = 'a'
        d2 = d1.copy()
        d2.x = 'b'
        self.assertEquals(d1.x, 'a')
        self.assertEquals(d2.x, 'b')

    def test_delete_after_copy(self):
        d1 = AttributeDict()
        d1.x = 'a'
        d1.y = 'b'
        d2 = d1.copy()
        del d1.x
        del d1['y']
        with self.assertRaises(AttributeError):
            _ = d1.x
        with self.assertRaises(KeyError):
            _ = d1['y']
        self.assertEquals(d2['x'], 'a')
        self.assertEquals(d2.y, 'b')
        self.assertEquals(set(d1.keys()), set({}))
        self.assertEquals(set(d2.keys()), set({'x', 'y'}))

    def test_shallowcopy1(self):
        d1 = AttributeDict()
        d1.x = [1, 2, 3]
        d1.y = 3
        d2 = d1.copy()
        d2.x[0] = 4
        d2.y = 5
        self.assertEquals(d1.x, [4, 2, 3])  # copy does a shallow copy
        self.assertEquals(d2.x, [4, 2, 3])
        self.assertEquals(d1.y, 3)
        self.assertEquals(d2.y, 5)

    def test_shallowcopy2(self):
        """
        Also test access at nested levels
        """
        d1 = AttributeDict()
        d1.x = {'a': 'b', 'c': 'd'}
        # d2 = copy.deepcopy(d1)
        d2 = d1.copy()
        # doesn't work like this, would work as d2['x']['a']
        # i think that it is because deepcopy on dict actually creates a
        # copy only if the data is changed; but for a nested dict,
        # d2.x returns a dict wrapped in our class and this looses all the
        # information on what should be updated when changed.
        d2.x['a'] = 'ggg'
        self.assertEquals(d1.x['a'], 'ggg')  # copy does a shallow copy
        self.assertEquals(d2.x['a'], 'ggg')

    def test_deepcopy1(self):
        d1 = AttributeDict()
        d1.x = [1, 2, 3]
        d2 = copy.deepcopy(d1)
        d2.x[0] = 4
        self.assertEquals(d1.x, [1, 2, 3])
        self.assertEquals(d2.x, [4, 2, 3])

    def test_shallowcopy2(self):
        """
        Also test access at nested levels
        """
        d1 = AttributeDict()
        d1.x = {'a': 'b', 'c': 'd'}
        d2 = copy.deepcopy(d1)
        d2.x['a'] = 'ggg'
        self.assertEquals(d1.x['a'], 'b')  # copy does a shallow copy
        self.assertEquals(d2.x['a'], 'ggg')


class TestAttributeDictNested(unittest.TestCase):
    """
    Test the functionality of nested AttributeDict classes.
    """

    def test_nested(self):
        d1 = AttributeDict({'x': 1, 'y': 2})
        d2 = AttributeDict({'z': 3, 'w': 4})
        d1.nested = d2
        self.assertEquals(d1.nested.z, 3)
        self.assertEquals(d1['nested'].w, 4)
        self.assertEquals(d1.nested['w'], 4)
        d2['w'] = 5
        self.assertEquals(d1['nested'].w, 5)
        self.assertEquals(d1.nested['w'], 5)

    def test_comparison(self):
        d1 = AttributeDict({'x': 1, 'y': 2, 'z': AttributeDict({'w': 3})})
        d2 = AttributeDict({'x': 1, 'y': 2, 'z': AttributeDict({'w': 3})})

        # They compare to the same value but they are different objects
        self.assertFalse(d1 is d2)
        self.assertEquals(d1, d2)

        d2.z.w = 4
        self.assertNotEquals(d1, d2)

    def test_nested_deepcopy(self):
        d1 = AttributeDict({'x': 1, 'y': 2})
        d2 = AttributeDict({'z': 3, 'w': 4})
        d1.nested = d2
        d1copy = copy.deepcopy(d1)
        self.assertEquals(d1copy.nested.z, 3)
        self.assertEquals(d1copy['nested'].w, 4)
        self.assertEquals(d1copy.nested['w'], 4)
        d2['w'] = 5
        self.assertEquals(d1copy['nested'].w, 4)  # Nothing has changed
        self.assertEquals(d1copy.nested['w'], 4)  # Nothing has changed
        self.assertEquals(d1copy.nested.w, 4)  # Nothing has changed

        self.assertEquals(d1['nested'].w, 5)  # The old one is updated
        self.assertEquals(d1.nested['w'], 5)  # The old one is updated
        self.assertEquals(d1.nested.w, 5)  # The old one is updated

        d1copy.nested.w = 6
        self.assertEquals(d1copy.nested.w, 6)
        self.assertEquals(d1.nested.w, 5)
        self.assertEquals(d2.w, 5)


class TestAttributeDictSerialize(unittest.TestCase):
    """
    Test serialization/deserialization (with json, pickle, ...)
    """

    def test_json(self):
        import json

        d1 = AttributeDict({'x': 1, 'y': 2})
        d2 = json.loads(json.dumps(d1))
        # Note that here I am comparing a dictionary (d2) with a
        # AttributeDict (d2) and they still compare to equal
        self.assertEquals(d1, d2)

    def test_json_recursive(self):
        import json

        d1 = AttributeDict({'x': 1, 'y': 2, 'z': AttributeDict({'w': 4})})
        d2 = json.loads(json.dumps(d1))
        # Note that here I am comparing a dictionary (d2) with a (recursive)
        # AttributeDict (d2) and they still compare to equal
        self.assertEquals(d1, d2)

    def test_pickle(self):
        import pickle

        d1 = AttributeDict({'x': 1, 'y': 2})
        d2 = pickle.loads(pickle.dumps(d1))
        self.assertEquals(d1, d2)

    def test_pickle_recursive(self):
        import pickle

        d1 = AttributeDict({'x': 1, 'y': 2, 'z': AttributeDict({'w': 4})})
        d2 = pickle.loads(pickle.dumps(d1))
        self.assertEquals(d1, d2)


class TestFFAD(unittest.TestCase):
    def test_insertion(self):
        a = TestFFADExample()
        a['a'] = 1
        a.b = 2
        # Not a valid key.
        with self.assertRaises(KeyError):
            a['d'] = 2
        with self.assertRaises(AttributeError):
            a.e = 5

    def test_insertion_on_init(self):
        a = TestFFADExample({'a': 1, 'b': 2})
        with self.assertRaises(KeyError):
            # 'd' is not a valid key
            a = TestFFADExample({'a': 1, 'd': 2})

    def test_pickle(self):
        """
        Note: pickle works here because self._valid_fields is defined
        at the class level!
        """
        import pickle

        a = TestFFADExample({'a': 1, 'b': 2})
        b = pickle.loads(pickle.dumps(a))
        b.c = 3
        with self.assertRaises(KeyError):
            b['d'] = 2

    def test_class_attribute(self):
        """
        I test that the get_valid_fields() is working as a class method,
        so I don't need to instantiate the class to get the list.
        """
        self.assertEquals(set(TestFFADExample.get_valid_fields()),
                          set(['a', 'b', 'c']))


class TestDFAD(unittest.TestCase):
    def test_insertion_and_retrieval(self):
        a = TestDFADExample()
        a['a'] = 1
        a.b = 2
        a['d'] = 3
        a.e = 4
        self.assertEquals(a.a, 1)
        self.assertEquals(a.b, 2)
        self.assertEquals(a['d'], 3)
        self.assertEquals(a['e'], 4)

    def test_keylist_method(self):
        a = TestDFADExample()
        a['a'] = 1
        a.b = 2
        a['d'] = 3
        a.e = 4

        self.assertEquals(set(a.get_default_fields()), set(['a', 'b', 'c']))
        self.assertEquals(set(a.keys()), set(['a', 'b', 'd', 'e']))
        self.assertEquals(set(a.defaultkeys()), set(['a', 'b']))
        self.assertEquals(set(a.extrakeys()), set(['d', 'e']))
        self.assertIsNone(a.c)

    def test_class_attribute(self):
        """
        I test that the get_default_fields() is working as a class method,
        so I don't need to instantiate the class to get the list.
        """
        self.assertEquals(set(TestDFADExample.get_default_fields()),
                          set(['a', 'b', 'c']))


    def test_validation(self):
        o = TestDFADExample()

        # Should be ok to have an empty 'a' attribute
        o.validate()

        o.a = 4
        o.b = 'text'

        # This should be fine
        o.validate()

        o.a = 'string'
        # o.a must be a positive integer
        with self.assertRaises(ValidationError):
            o.validate()

        o.a = -3
        # a.a must be a positive integer
        with self.assertRaises(ValidationError):
            o.validate()

