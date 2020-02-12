# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for AiiDA base data classes."""
import operator

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm import load_node, List, Bool, Float, Int, Str, NumericType
from aiida.orm.nodes.data.bool import get_true_node, get_false_node


class TestList(AiidaTestCase):
    """Test AiiDA List class."""

    def test_creation(self):
        node = List()
        self.assertEqual(len(node), 0)
        with self.assertRaises(IndexError):
            node[0]  # pylint: disable=pointless-statement

    def test_append(self):
        """Test append() member function."""

        def do_checks(node):
            self.assertEqual(len(node), 1)
            self.assertEqual(node[0], 4)

        node = List()
        node.append(4)
        do_checks(node)

        # Try the same after storing
        node = List()
        node.append(4)
        node.store()
        do_checks(node)

    def test_extend(self):
        """Test extend() member function."""
        lst = [1, 2, 3]

        def do_checks(node):
            self.assertEqual(len(node), len(lst))
            # Do an element wise comparison
            for lst_, node_ in zip(lst, node):
                self.assertEqual(lst_, node_)

        node = List()
        node.extend(lst)
        do_checks(node)
        # Further extend
        node.extend(lst)
        self.assertEqual(len(node), len(lst) * 2)

        # Do an element wise comparison
        for i, _ in enumerate(lst):
            self.assertEqual(lst[i], node[i])
            self.assertEqual(lst[i], node[i % len(lst)])

        # Now try after storing
        node = List()
        node.extend(lst)
        node.store()
        do_checks(node)

    def test_mutability(self):
        """Test list's mutability before and after storage."""
        node = List()
        node.append(5)
        node.store()

        # Test all mutable calls are now disallowed
        with self.assertRaises(ModificationNotAllowed):
            node.append(5)
        with self.assertRaises(ModificationNotAllowed):
            node.extend([5])
        with self.assertRaises(ModificationNotAllowed):
            node.insert(0, 2)
        with self.assertRaises(ModificationNotAllowed):
            node.remove(0)
        with self.assertRaises(ModificationNotAllowed):
            node.pop()
        with self.assertRaises(ModificationNotAllowed):
            node.sort()
        with self.assertRaises(ModificationNotAllowed):
            node.reverse()

    @staticmethod
    def test_store_load():
        """Test load_node on just stored object."""
        node = List(list=[1, 2, 3])
        node.store()

        node_loaded = load_node(node.pk)
        assert node.get_list() == node_loaded.get_list()


class TestFloat(AiidaTestCase):
    """Test Float class."""

    def setUp(self):
        super().setUp()
        self.value = Float()
        self.all_types = [Int, Float, Bool, Str]

    def test_create(self):
        """Creating basic data objects."""
        term_a = Float()
        # Check that initial value is zero
        self.assertAlmostEqual(term_a.value, 0.0)

        float_ = Float(6.0)
        self.assertAlmostEqual(float_.value, 6.)
        self.assertAlmostEqual(float_, Float(6.0))

        int_ = Int()
        self.assertAlmostEqual(int_.value, 0)
        int_ = Int(6)
        self.assertAlmostEqual(int_.value, 6)
        self.assertAlmostEqual(float_, int_)

        bool_ = Bool()
        self.assertAlmostEqual(bool_.value, False)
        bool_ = Bool(False)
        self.assertAlmostEqual(bool_.value, False)
        self.assertAlmostEqual(bool_.value, get_false_node())
        bool_ = Bool(True)
        self.assertAlmostEqual(bool_.value, True)
        self.assertAlmostEqual(bool_.value, get_true_node())

        str_ = Str()
        self.assertAlmostEqual(str_.value, '')
        str_ = Str('Hello')
        self.assertAlmostEqual(str_.value, 'Hello')

    def test_load(self):
        """Test object loading."""
        for typ in self.all_types:
            node = typ()
            node.store()
            loaded = load_node(node.pk)
            self.assertAlmostEqual(node, loaded)

    def test_add(self):
        """Test addition."""
        term_a = Float(4)
        term_b = Float(5)
        # Check adding two db Floats
        res = term_a + term_b
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 9.0)

        # Check adding db Float and native (both ways)
        res = term_a + 5.0
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 9.0)

        res = 5.0 + term_a
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 9.0)

        # Inplace
        term_a = Float(4)
        term_a += term_b
        self.assertAlmostEqual(term_a, 9.0)

        term_a = Float(4)
        term_a += 5
        self.assertAlmostEqual(term_a, 9.0)

    def test_mul(self):
        """Test floats multiplication."""
        term_a = Float(4)
        term_b = Float(5)
        # Check adding two db Floats
        res = term_a * term_b
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 20.0)

        # Check adding db Float and native (both ways)
        res = term_a * 5.0
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 20)

        res = 5.0 * term_a
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 20.0)

        # Inplace
        term_a = Float(4)
        term_a *= term_b
        self.assertAlmostEqual(term_a, 20)

        term_a = Float(4)
        term_a *= 5
        self.assertAlmostEqual(term_a, 20)

    def test_power(self):
        """Test power operator."""
        term_a = Float(4)
        term_b = Float(2)

        res = term_a**term_b
        self.assertAlmostEqual(res.value, 16.)

    def test_division(self):
        """Test the normal division operator."""
        term_a = Float(3)
        term_b = Float(2)

        self.assertAlmostEqual(term_a / term_b, 1.5)
        self.assertIsInstance(term_a / term_b, Float)

    def test_division_integer(self):
        """Test the integer division operator."""
        term_a = Float(3)
        term_b = Float(2)

        self.assertAlmostEqual(term_a // term_b, 1.0)
        self.assertIsInstance(term_a // term_b, Float)

    def test_modulus(self):
        """Test modulus operator."""
        term_a = Float(12.0)
        term_b = Float(10.0)

        self.assertAlmostEqual(term_a % term_b, 2.0)
        self.assertIsInstance(term_a % term_b, NumericType)
        self.assertAlmostEqual(term_a % 10.0, 2.0)
        self.assertIsInstance(term_a % 10.0, NumericType)
        self.assertAlmostEqual(12.0 % term_b, 2.0)
        self.assertIsInstance(12.0 % term_b, NumericType)


class TestFloatIntMix(AiidaTestCase):
    """Test operations between Int and Float objects."""

    def test_operator(self):
        """Test all binary operators."""
        term_a = Float(2.2)
        term_b = Int(3)

        for oper in [
            operator.add, operator.mul, operator.pow, operator.lt, operator.le, operator.gt, operator.ge, operator.iadd,
            operator.imul
        ]:
            for term_x, term_y in [(term_a, term_b), (term_b, term_a)]:
                res = oper(term_x, term_y)
                c_val = oper(term_x.value, term_y.value)
                self.assertEqual(res._type, type(c_val))  # pylint: disable=protected-access
                self.assertEqual(res, oper(term_x.value, term_y.value))


class TestInt(AiidaTestCase):
    """Test Int class."""

    def test_division(self):
        """Test the normal division operator."""
        term_a = Int(3)
        term_b = Int(2)

        self.assertAlmostEqual(term_a / term_b, 1.5)
        self.assertIsInstance(term_a / term_b, Float)

    def test_division_integer(self):
        """Test the integer division operator."""
        term_a = Int(3)
        term_b = Int(2)

        self.assertAlmostEqual(term_a // term_b, 1)
        self.assertIsInstance(term_a // term_b, Int)

    def test_modulo(self):
        """Test modulus operation."""
        term_a = Int(12)
        term_b = Int(10)

        self.assertEqual(term_a % term_b, 2)
        self.assertIsInstance(term_a % term_b, NumericType)
        self.assertEqual(term_a % 10, 2)
        self.assertIsInstance(term_a % 10, NumericType)
        self.assertEqual(12 % term_b, 2)
        self.assertIsInstance(12 % term_b, NumericType)
