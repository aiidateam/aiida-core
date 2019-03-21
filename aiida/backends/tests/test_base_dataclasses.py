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

import operator

from six.moves import range, zip

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm import load_node, List, Bool, Float, Int, Str, NumericType
from aiida.orm.nodes.data.bool import get_true_node, get_false_node


class TestList(AiidaTestCase):

    def test_creation(self):
        node = List()
        self.assertEqual(len(node), 0)
        with self.assertRaises(IndexError):
            node[0]

    def test_append(self):
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
        lst = [1, 2, 3]

        def do_checks(node):
            self.assertEqual(len(node), len(lst))
            # Do an element wise comparison
            for x, y in zip(lst, node):
                self.assertEqual(x, y)

        node = List()
        node.extend(lst)
        do_checks(node)
        # Further extend
        node.extend(lst)
        self.assertEqual(len(node), len(lst) * 2)

        # Do an element wise comparison
        for i in range(len(lst)):
            self.assertEqual(lst[i], node[i])
            self.assertEqual(lst[i], node[i % len(lst)])

        # Now try after storing
        node = List()
        node.extend(lst)
        node.store()
        do_checks(node)

    def test_mutability(self):
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

    def test_store_load(self):
        node = List(list=[1, 2, 3])
        node.store()

        node_loaded = load_node(node.pk)
        assert node.get_list() == node_loaded.get_list()


class TestFloat(AiidaTestCase):

    def setUp(self):
        super(TestFloat, self).setUp()
        self.value = Float()
        self.all_types = [Int, Float, Bool, Str]

    def test_create(self):
        a = Float()
        # Check that initial value is zero
        self.assertAlmostEqual(a.value, 0.0)

        f = Float(6.0)
        self.assertAlmostEqual(f.value, 6.)
        self.assertAlmostEqual(f, Float(6.0))

        i = Int()
        self.assertAlmostEqual(i.value, 0)
        i = Int(6)
        self.assertAlmostEqual(i.value, 6)
        self.assertAlmostEqual(f, i)

        b = Bool()
        self.assertAlmostEqual(b.value, False)
        b = Bool(False)
        self.assertAlmostEqual(b.value, False)
        self.assertAlmostEqual(b.value, get_false_node())
        b = Bool(True)
        self.assertAlmostEqual(b.value, True)
        self.assertAlmostEqual(b.value, get_true_node())

        s = Str()
        self.assertAlmostEqual(s.value, "")
        s = Str('Hello')
        self.assertAlmostEqual(s.value, 'Hello')

    def test_load(self):
        for t in self.all_types:
            node = t()
            node.store()
            loaded = load_node(node.pk)
            self.assertAlmostEqual(node, loaded)

    def test_add(self):
        a = Float(4)
        b = Float(5)
        # Check adding two db Floats
        res = a + b
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 9.0)

        # Check adding db Float and native (both ways)
        res = a + 5.0
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 9.0)

        res = 5.0 + a
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 9.0)

        # Inplace
        a = Float(4)
        a += b
        self.assertAlmostEqual(a, 9.0)

        a = Float(4)
        a += 5
        self.assertAlmostEqual(a, 9.0)

    def test_mul(self):
        a = Float(4)
        b = Float(5)
        # Check adding two db Floats
        res = a * b
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 20.0)

        # Check adding db Float and native (both ways)
        res = a * 5.0
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 20)

        res = 5.0 * a
        self.assertIsInstance(res, NumericType)
        self.assertAlmostEqual(res, 20.0)

        # Inplace
        a = Float(4)
        a *= b
        self.assertAlmostEqual(a, 20)

        a = Float(4)
        a *= 5
        self.assertAlmostEqual(a, 20)

    def test_power(self):
        a = Float(4)
        b = Float(2)

        res = a ** b
        self.assertAlmostEqual(res.value, 16.)

    def test_division(self):
        """Test the normal division operator."""
        a = Float(3)
        b = Float(2)

        self.assertAlmostEqual(a / b, 1.5)
        self.assertIsInstance(a / b, Float)

    def test_division_integer(self):
        """Test the integer division operator."""
        a = Float(3)
        b = Float(2)

        self.assertAlmostEqual(a // b, 1.0)
        self.assertIsInstance(a // b, Float)

    def test_modulo(self):
        a = Float(12.0)
        b = Float(10.0)

        self.assertAlmostEqual(a % b, 2.0)
        self.assertIsInstance(a % b, NumericType)
        self.assertAlmostEqual(a % 10.0, 2.0)
        self.assertIsInstance(a % 10.0, NumericType)
        self.assertAlmostEqual(12.0 % b, 2.0)
        self.assertIsInstance(12.0 % b, NumericType)


class TestFloatIntMix(AiidaTestCase):

    def test_operator(self):
        a = Float(2.2)
        b = Int(3)

        for op in [operator.add, operator.mul, operator.pow, operator.lt, operator.le, operator.gt, operator.ge, operator.iadd, operator.imul]:
            for x, y in [(a, b), (b, a)]:
                c = op(x, y)
                c_val = op(x.value, y.value)
                self.assertEqual(c._type, type(c_val))
                self.assertEqual(c, op(x.value, y.value))


class TestInt(AiidaTestCase):

    def test_division(self):
        """Test the normal division operator."""
        a = Int(3)
        b = Int(2)

        self.assertAlmostEqual(a / b, 1.5)
        self.assertIsInstance(a / b, Float)

    def test_division_integer(self):
        """Test the integer division operator."""
        a = Int(3)
        b = Int(2)

        self.assertAlmostEqual(a // b, 1)
        self.assertIsInstance(a // b, Int)

    def test_modulo(self):
        a = Int(12)
        b = Int(10)

        self.assertEqual(a % b, 2)
        self.assertIsInstance(a % b, NumericType)
        self.assertEqual(a % 10, 2)
        self.assertIsInstance(a % 10, NumericType)
        self.assertEqual(12 % b, 2)
        self.assertIsInstance(12 % b, NumericType)
