# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import unittest

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm import load_node
from aiida.orm.data.base import (
    NumericType, Float, Str, Bool, Int, get_true_node, get_false_node)
import aiida.orm.data.base as base



class TestList(AiidaTestCase):
    def test_creation(self):
        l = base.List()
        self.assertEqual(len(l), 0)
        with self.assertRaises(IndexError):
            l[0]

    def test_append(self):
        def do_checks(l):
            self.assertEqual(len(l), 1)
            self.assertEqual(l[0], 4)

        l = base.List()
        l.append(4)
        do_checks(l)

        # Try the same after storing
        l = base.List()
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

        l = base.List()
        l.extend(lst)
        do_checks(l)
        # Further extend
        l.extend(lst)
        self.assertEqual(len(l), len(lst) * 2)

        # Do an element wise comparison
        for i in range(0, len(lst)):
            self.assertEqual(lst[i], l[i])
            self.assertEqual(lst[i], l[i % len(lst)])

        # Now try after strogin
        l = base.List()
        l.extend(lst)
        l.store()
        do_checks(l)

    def test_mutability(self):
        l = base.List()
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


class TestFloat(AiidaTestCase):
    def setUp(self):
        super(TestFloat, self).setUp()
        self.value = Float()
        self.all_types = [Int, Float, Bool, Str]

    def test_create(self):
        a = Float()
        # Check that initial value is zero
        self.assertEqual(a.value, 0.0)

        f = Float(6.0)
        self.assertEqual(f.value, 6.)
        self.assertEqual(f, Float(6.0))

        i = Int()
        self.assertEqual(i.value, 0)
        i = Int(6)
        self.assertEqual(i.value, 6)
        self.assertEqual(f, i)

        b = Bool()
        self.assertEqual(b.value, False)
        b = Bool(False)
        self.assertEqual(b.value, False)
        self.assertEqual(b.value, get_false_node())
        b = Bool(True)
        self.assertEqual(b.value, True)
        self.assertEqual(b.value, get_true_node())

        s = Str()
        self.assertEqual(s.value, "")
        s = Str('Hello')
        self.assertEqual(s.value, 'Hello')

    def test_load(self):
        for t in self.all_types:
            node = t()
            node.store()
            loaded = load_node(node.pk)
            self.assertEqual(node, loaded)

    def test_add(self):
        a = Float(4)
        b = Float(5)
        # Check adding two db Floats
        res = a + b
        self.assertIsInstance(res, NumericType)
        self.assertEqual(res, 9.0)

        # Check adding db Float and native (both ways)
        res = a + 5.0
        self.assertIsInstance(res, NumericType)
        self.assertEqual(res, 9.0)

        res = 5.0 + a
        self.assertIsInstance(res, NumericType)
        self.assertEqual(res, 9.0)

        # Inplace
        a = Float(4)
        a += b
        self.assertEqual(a, 9.0)

        a = Float(4)
        a += 5
        self.assertEqual(a, 9.0)

    def test_mul(self):
        a = Float(4)
        b = Float(5)
        # Check adding two db Floats
        res = a * b
        self.assertIsInstance(res, NumericType)
        self.assertEqual(res, 20.0)

        # Check adding db Float and native (both ways)
        res = a * 5.0
        self.assertIsInstance(res, NumericType)
        self.assertEqual(res, 20)

        res = 5.0 * a
        self.assertIsInstance(res, NumericType)
        self.assertEqual(res, 20.0)

        # Inplace
        a = Float(4)
        a *= b
        self.assertEqual(a, 20)

        a = Float(4)
        a *= 5
        self.assertEqual(a, 20)

    def test_power(self):
        a = Float(4)
        b = Float(2)

        res = a ** b
        self.assertEqual(res.value, 16.)
