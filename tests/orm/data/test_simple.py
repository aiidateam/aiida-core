import unittest
from aiida.orm.data.simple import Float, NumericType


class TestFloat(unittest.TestCase):
    def setUp(self):
        self.value = Float()

    def test_create(self):
        a = Float()
        # Check that initial value is zero
        self.assertEqual(a.value, 0.0)

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
