
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from unittest import TestCase
from collections import Mapping
from aiida.workflows2.process import Process, ProcessSpec


class TestProcessSpec(TestCase):
    def setUp(self):
        self.spec = Process.spec()

    def test_get_inputs_template(self):
        s = ProcessSpec()
        s.input('a')
        s.input('b', default=5)

        template = s.get_inputs_template()
        self.assertIsInstance(template, Mapping)
        self._test_template(template)
        for attr in ['b']:
            self.assertTrue(
                attr in template,
                "Attribute '{}' not found in template".format(attr))

    def test_dynamic_input(self):
        from aiida.orm import Node
        from aiida.orm.data import Data

        n = Node()
        d = Data()
        port = self.spec.get_dynamic_input()
        self.assertFalse(port.validate("foo")[0])
        self.assertFalse(port.validate(5)[0])
        self.assertTrue(port.validate(n)[0])
        self.assertTrue(port.validate(d)[0])

    def test_dynamic_output(self):
        from aiida.orm import Node
        from aiida.orm.data import Data

        n = Node()
        d = Data()
        port = self.spec.get_dynamic_output()
        self.assertFalse(port.validate("foo")[0])
        self.assertFalse(port.validate(5)[0])
        self.assertTrue(port.validate(n)[0])
        self.assertTrue(port.validate(d)[0])

    def _test_template(self, template):
        template.a = 2
        self.assertEqual(template.a, 2)
        # Check the default is what we expect
        self.assertEqual(template.b, 5)
        with self.assertRaises(AttributeError):
            template.c = 6

        # Check that we can unpack
        self.assertEqual(dict(**template)['a'], 2)

