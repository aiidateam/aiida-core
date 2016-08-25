# -*- coding: utf-8 -*-
import unittest
from aiida.orm.data.simple import make_float, NumericType


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"

class TestFloat(unittest.TestCase):
    def setUp(self):
        self.value = make_float()

    def test_create(self):
        a = make_float()
        # Check that initial value is zero
        self.assertEqual(a.value, 0.0)

    def test_add(self):
        a = make_float(4)
        b = make_float(5)
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
        a = make_float(4)
        a += b
        self.assertEqual(a, 9.0)

        a = make_float(4)
        a += 5
        self.assertEqual(a, 9.0)

    def test_mul(self):
        a = make_float(4)
        b = make_float(5)
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
        a = make_float(4)
        a *= b
        self.assertEqual(a, 20)

        a = make_float(4)
        a *= 5
        self.assertEqual(a, 20)

    def test_power(self):
        a = make_float(4)
        b = make_float(2)

        res = a ** b
        self.assertEqual(res.value, 16.)
