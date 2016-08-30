# -*- coding: utf-8 -*-
import unittest

from aiida.orm import load_node
from aiida.orm.data.base import NumericType, Float, Str, Bool, Int, TRUE, FALSE


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


class TestFloat(unittest.TestCase):
    def setUp(self):
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
        self.assertEqual(b.value, FALSE)
        b = Bool(True)
        self.assertEqual(b.value, True)
        self.assertEqual(b.value, TRUE)

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
