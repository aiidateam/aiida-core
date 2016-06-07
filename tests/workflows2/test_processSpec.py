
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from unittest import TestCase
from collections import Mapping
from aiida.workflows2.process import ProcessSpec


class TestProcessSpec(TestCase):
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
                "Attribute \"{}\" not found in template".format(attr))

    def _test_template(self, template):
        template.a = 2
        self.assertEqual(template.b, 5)
        with self.assertRaises(ValueError):
            template.c = 6

        # Check that we can unpack
        self.assertEqual(dict(**template)['a'], 2)
