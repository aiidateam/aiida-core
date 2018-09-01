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
import unittest
import operator

from six.moves import range, zip

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm import load_node
from aiida.orm.data.numeric import NumericType
from aiida.orm.data.list import List
from aiida.orm.data.bool import Bool, get_true_node, get_false_node
from aiida.orm.data.float import Float
from aiida.orm.data.int import Int
from aiida.orm.data.str import Str


class TestList(AiidaTestCase):
    def test_creation(self):
        l = List()
        self.assertEqual(len(l), 0)
        with self.assertRaises(IndexError):
            l[0]

    def test_append(self):
        def do_checks(l):
            self.assertEqual(len(l), 1)
            self.assertEqual(l[0], 4)

        l = List()
        l.append(4)
        do_checks(l)

        # Try the same after storing
        l = List()
        l.append(4)
        l.store()
        do_checks(l)

    def test_extend(self):
        lst = [1, 2, 3]

        def do_checks(l):
            self.assertEqual(len(l), len(lst))
            # Do an element wise comparison
            for x, y in zip(lst, l):
                self.assertEqual(x, y)

        l = List()
        l.extend(lst)
        do_checks(l)
        # Further extend
        l.extend(lst)
        self.assertEqual(len(l), len(lst) * 2)

        # Do an element wise comparison
        for i in range(len(lst)):
            self.assertEqual(lst[i], l[i])
            self.assertEqual(lst[i], l[i % len(lst)])

        # Now try after strogin
        l = List()
        l.extend(lst)
        l.store()
        do_checks(l)

    def test_mutability(self):
        l = List()
        l.append(5)
        l.store()

        # Test all mutable calls are now disallowed
        with self.assertRaises(ModificationNotAllowed):
            l.append(5)
        with self.assertRaises(ModificationNotAllowed):
            l.extend([5])
        with self.assertRaises(ModificationNotAllowed):
            l.insert(0, 2)
        with self.assertRaises(ModificationNotAllowed):
            l.remove(0)
        with self.assertRaises(ModificationNotAllowed):
            l.pop()
        with self.assertRaises(ModificationNotAllowed):
            l.sort()
        with self.assertRaises(ModificationNotAllowed):
            l.reverse()

    def test_store_load(self):
        l = List(list=[1, 2, 3])
        l.store()

        l_loaded = load_node(l.pk)
        assert l.get_list() == l_loaded.get_list()

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

    def test_modulo(self):
        a = Int(12)
        b = Int(10)

        self.assertEqual(a % b, 2)
        self.assertIsInstance(a % b, NumericType)
        self.assertEqual(a % 10, 2)
        self.assertIsInstance(a % 10, NumericType)
        self.assertEqual(12 % b, 2)
        self.assertIsInstance(12 % b, NumericType)
