# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the extended dictionary classes."""
# pylint: disable=pointless-statement,attribute-defined-outside-init
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import copy
import pickle
import unittest

from six import integer_types

from aiida.common import json
from aiida.common import exceptions
from aiida.common import extendeddicts


class TestFFADExample(extendeddicts.FixedFieldsAttributeDict):
    """
    An example class that accepts only the 'alpha', 'beta' and 'gamma' keys/attributes.
    """
    _valid_fields = ('alpha', 'beta', 'gamma')


class TestDFADExample(extendeddicts.DefaultFieldsAttributeDict):
    """
    An example class that has 'alpha', 'beta' and 'gamma' as default keys.
    """
    _default_fields = ('alpha', 'beta', 'gamma')

    @staticmethod
    def validate_alpha(value):
        """Validate a value."""
        # Ok if unset
        if value is None:
            return

        if not isinstance(value, integer_types):
            raise TypeError('expecting integer')
        if value < 0:
            raise ValueError('expecting a positive or zero value')


class TestAttributeDictAccess(unittest.TestCase):
    """
    Try to access the dictionary elements in various ways, copying (shallow and
    deep), check raised exceptions.
    """

    def test_access_dict_to_attr(self):
        """Test dictionary to attribute."""
        dictionary = extendeddicts.AttributeDict()
        dictionary['test'] = 'abc'
        self.assertEqual(dictionary.test, 'abc')

    def test_access_attr_to_dict(self):
        """Test attribute to dictionary."""
        dictionary = extendeddicts.AttributeDict()
        dictionary.test = 'def'
        self.assertEqual(dictionary['test'], 'def')

    def test_access_nonexisting_asattr(self):
        """Test non-existing attribute."""
        dictionary = extendeddicts.AttributeDict()
        with self.assertRaises(AttributeError):
            dictionary.test

    def test_access_nonexisting_askey(self):
        """Test non-existing attribute as key."""
        dictionary = extendeddicts.AttributeDict()
        with self.assertRaises(KeyError):
            dictionary['test']

    def test_del_nonexisting_askey(self):
        """Test deleting non-existing attribute as key."""
        dictionary = extendeddicts.AttributeDict()
        with self.assertRaises(KeyError):
            del dictionary['test']

    def test_del_nonexisting_asattr(self):
        """Test deleting non-existing attribute."""
        dictionary = extendeddicts.AttributeDict()
        with self.assertRaises(AttributeError):
            del dictionary.test

    def test_copy(self):
        """Test copying."""
        dictionary_01 = extendeddicts.AttributeDict()
        dictionary_01.alpha = 'a'
        dictionary_02 = dictionary_01.copy()
        dictionary_02.alpha = 'b'
        self.assertEqual(dictionary_01.alpha, 'a')
        self.assertEqual(dictionary_02.alpha, 'b')

    def test_delete_after_copy(self):
        """Test deleting after copying."""
        dictionary_01 = extendeddicts.AttributeDict()
        dictionary_01.alpha = 'a'
        dictionary_01.beta = 'b'
        dictionary_02 = dictionary_01.copy()
        del dictionary_01.alpha
        del dictionary_01['beta']
        with self.assertRaises(AttributeError):
            _ = dictionary_01.alpha
        with self.assertRaises(KeyError):
            _ = dictionary_01['beta']
        self.assertEqual(dictionary_02['alpha'], 'a')
        self.assertEqual(dictionary_02.beta, 'b')
        self.assertEqual(set(dictionary_01.keys()), set({}))
        self.assertEqual(set(dictionary_02.keys()), set({'alpha', 'beta'}))

    def test_shallowcopy1(self):
        """Test shallow copying."""
        dictionary_01 = extendeddicts.AttributeDict()
        dictionary_01.alpha = [1, 2, 3]
        dictionary_01.beta = 3
        dictionary_02 = dictionary_01.copy()
        dictionary_02.alpha[0] = 4
        dictionary_02.beta = 5
        self.assertEqual(dictionary_01.alpha, [4, 2, 3])  # copy does a shallow copy
        self.assertEqual(dictionary_02.alpha, [4, 2, 3])
        self.assertEqual(dictionary_01.beta, 3)
        self.assertEqual(dictionary_02.beta, 5)

    def test_shallowcopy2(self):
        """Test shallow copying."""
        dictionary_01 = extendeddicts.AttributeDict()
        dictionary_01.alpha = {'a': 'b', 'c': 'd'}
        # dictionary_02 = copy.deepcopy(dictionary_01)
        dictionary_02 = dictionary_01.copy()
        # doesn't work like this, would work as dictionary_02['x']['a']
        # i think that it is because deepcopy on dict actually creates a
        # copy only if the data is changed; but for a nested dict,
        # dictionary_02.alpha returns a dict wrapped in our class and this looses all the
        # information on what should be updated when changed.
        dictionary_02.alpha['a'] = 'ggg'
        self.assertEqual(dictionary_01.alpha['a'], 'ggg')  # copy does a shallow copy
        self.assertEqual(dictionary_02.alpha['a'], 'ggg')

    def test_deepcopy1(self):
        """Test deep copying."""
        dictionary_01 = extendeddicts.AttributeDict()
        dictionary_01.alpha = [1, 2, 3]
        dictionary_02 = copy.deepcopy(dictionary_01)
        dictionary_02.alpha[0] = 4
        self.assertEqual(dictionary_01.alpha, [1, 2, 3])
        self.assertEqual(dictionary_02.alpha, [4, 2, 3])

    def test_shallowcopy3(self):
        """Test shallow copying."""
        dictionary_01 = extendeddicts.AttributeDict()
        dictionary_01.alpha = {'a': 'b', 'c': 'd'}
        dictionary_02 = copy.deepcopy(dictionary_01)
        dictionary_02.alpha['a'] = 'ggg'
        self.assertEqual(dictionary_01.alpha['a'], 'b')  # copy does a shallow copy
        self.assertEqual(dictionary_02.alpha['a'], 'ggg')


class TestAttributeDictNested(unittest.TestCase):
    """
    Test the functionality of nested AttributeDict classes.
    """

    def test_nested(self):
        """Test nested dictionary."""
        dictionary_01 = extendeddicts.AttributeDict({'x': 1, 'y': 2})
        dictionary_02 = extendeddicts.AttributeDict({'z': 3, 'w': 4})
        dictionary_01.nested = dictionary_02
        self.assertEqual(dictionary_01.nested.z, 3)
        self.assertEqual(dictionary_01['nested'].w, 4)
        self.assertEqual(dictionary_01.nested['w'], 4)
        dictionary_02['w'] = 5
        self.assertEqual(dictionary_01['nested'].w, 5)
        self.assertEqual(dictionary_01.nested['w'], 5)

    def test_comparison(self):
        """Test dictionary comparison."""
        dictionary_01 = extendeddicts.AttributeDict({'x': 1, 'y': 2, 'z': extendeddicts.AttributeDict({'w': 3})})
        dictionary_02 = extendeddicts.AttributeDict({'x': 1, 'y': 2, 'z': extendeddicts.AttributeDict({'w': 3})})

        # They compare to the same value but they are different objects
        self.assertFalse(dictionary_01 is dictionary_02)
        self.assertEqual(dictionary_01, dictionary_02)

        dictionary_02.z.w = 4
        self.assertNotEqual(dictionary_01, dictionary_02)

    def test_nested_deepcopy(self):
        """Test nested deepcopy."""
        dictionary_01 = extendeddicts.AttributeDict({'x': 1, 'y': 2})
        dictionary_02 = extendeddicts.AttributeDict({'z': 3, 'w': 4})
        dictionary_01.nested = dictionary_02
        dictionary_01copy = copy.deepcopy(dictionary_01)
        self.assertEqual(dictionary_01copy.nested.z, 3)
        self.assertEqual(dictionary_01copy['nested'].w, 4)
        self.assertEqual(dictionary_01copy.nested['w'], 4)
        dictionary_02['w'] = 5
        self.assertEqual(dictionary_01copy['nested'].w, 4)  # Nothing has changed
        self.assertEqual(dictionary_01copy.nested['w'], 4)  # Nothing has changed
        self.assertEqual(dictionary_01copy.nested.w, 4)  # Nothing has changed

        self.assertEqual(dictionary_01['nested'].w, 5)  # The old one is updated
        self.assertEqual(dictionary_01.nested['w'], 5)  # The old one is updated
        self.assertEqual(dictionary_01.nested.w, 5)  # The old one is updated

        dictionary_01copy.nested.w = 6
        self.assertEqual(dictionary_01copy.nested.w, 6)
        self.assertEqual(dictionary_01.nested.w, 5)
        self.assertEqual(dictionary_02.w, 5)


class TestAttributeDictSerialize(unittest.TestCase):
    """
    Test serialization/deserialization (with json, pickle, ...)
    """

    def test_json(self):
        """Test loading and dumping from json."""
        dictionary_01 = extendeddicts.AttributeDict({'x': 1, 'y': 2})
        dictionary_02 = json.loads(json.dumps(dictionary_01))
        # Note that here I am comparing a dictionary (dictionary_02) with a
        # extendeddicts.AttributeDict (dictionary_02) and they still compare to equal
        self.assertEqual(dictionary_01, dictionary_02)

    def test_json_recursive(self):
        """Test loading and dumping from json recursively."""
        dictionary_01 = extendeddicts.AttributeDict({'x': 1, 'y': 2, 'z': extendeddicts.AttributeDict({'w': 4})})
        dictionary_02 = json.loads(json.dumps(dictionary_01))
        # Note that here I am comparing a dictionary (dictionary_02) with a (recursive)
        # extendeddicts.AttributeDict (dictionary_02) and they still compare to equal
        self.assertEqual(dictionary_01, dictionary_02)

    def test_pickle(self):
        """Test pickling."""
        dictionary_01 = extendeddicts.AttributeDict({'x': 1, 'y': 2})
        dictionary_02 = pickle.loads(pickle.dumps(dictionary_01))
        self.assertEqual(dictionary_01, dictionary_02)

    def test_pickle_recursive(self):
        """Test pickling recursively."""
        dictionary_01 = extendeddicts.AttributeDict({'x': 1, 'y': 2, 'z': extendeddicts.AttributeDict({'w': 4})})
        dictionary_02 = pickle.loads(pickle.dumps(dictionary_01))
        self.assertEqual(dictionary_01, dictionary_02)


class TestFFAD(unittest.TestCase):
    """Test for the fixed fields attribute dictionary."""

    def test_insertion(self):
        """Test insertion."""
        dictionary = TestFFADExample()
        dictionary['alpha'] = 1
        dictionary.beta = 2
        # Not a valid key.
        with self.assertRaises(KeyError):
            dictionary['delta'] = 2
        with self.assertRaises(AttributeError):
            dictionary.epsilon = 5

    def test_insertion_on_init(self):
        """Test insertion in constructor."""
        TestFFADExample({'alpha': 1, 'beta': 2})
        with self.assertRaises(KeyError):
            # 'delta' is not a valid key
            TestFFADExample({'alpha': 1, 'delta': 2})

    def test_pickle(self):
        """Note: pickle works here because self._valid_fields is defined at the class level!"""
        dictionary_01 = TestFFADExample({'alpha': 1, 'beta': 2})
        dictionary_02 = pickle.loads(pickle.dumps(dictionary_01))
        dictionary_02.gamma = 3
        with self.assertRaises(KeyError):
            dictionary_02['delta'] = 2

    def test_class_attribute(self):
        """
        I test that the get_valid_fields() is working as a class method,
        so I don't need to instantiate the class to get the list.
        """
        self.assertEqual(set(TestFFADExample.get_valid_fields()), set(['alpha', 'beta', 'gamma']))


class TestDFAD(unittest.TestCase):
    """Test for the default fields attribute dictionary."""

    def test_insertion_and_retrieval(self):
        """Test insertion and retrieval."""
        dictionary = TestDFADExample()
        dictionary['alpha'] = 1
        dictionary.beta = 2
        dictionary['delta'] = 3
        dictionary.epsilon = 4
        self.assertEqual(dictionary.alpha, 1)
        self.assertEqual(dictionary.beta, 2)
        self.assertEqual(dictionary['delta'], 3)
        self.assertEqual(dictionary['epsilon'], 4)

    def test_keylist_method(self):
        """Test keylist retrieval."""
        dictionary = TestDFADExample()
        dictionary['alpha'] = 1
        dictionary.beta = 2
        dictionary['delta'] = 3
        dictionary.epsilon = 4

        self.assertEqual(set(dictionary.get_default_fields()), set(['alpha', 'beta', 'gamma']))
        self.assertEqual(set(dictionary.keys()), set(['alpha', 'beta', 'delta', 'epsilon']))
        self.assertEqual(set(dictionary.defaultkeys()), set(['alpha', 'beta']))
        self.assertEqual(set(dictionary.extrakeys()), set(['delta', 'epsilon']))
        self.assertIsNone(dictionary.gamma)

    def test_class_attribute(self):
        """
        I test that the get_default_fields() is working as a class method,
        so I don't need to instantiate the class to get the list.
        """
        self.assertEqual(set(TestDFADExample.get_default_fields()), set(['alpha', 'beta', 'gamma']))

    def test_validation(self):
        """Test validation."""
        dictionary = TestDFADExample()

        # Should be ok to have an empty 'alpha' attribute
        dictionary.validate()

        dictionary.alpha = 4
        dictionary.beta = 'text'

        # This should be fine
        dictionary.validate()

        dictionary.alpha = 'string'
        # dictionary.alpha must be a positive integer
        with self.assertRaises(exceptions.ValidationError):
            dictionary.validate()

        dictionary.alpha = -3
        # alpha must be a positive integer
        with self.assertRaises(exceptions.ValidationError):
            dictionary.validate()
