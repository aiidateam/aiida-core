from unittest import TestCase
from aiida.workflows2.process import ProcessSpec


class TestProcessSpec(TestCase):
    def test_get_attributes_template(self):
        s = ProcessSpec()
        s.attribute('a')
        s.attribute('b', default=5)

        self._test_template(s.get_attributes_template())

    def test_get_inputs_template(self):
        s = ProcessSpec()
        s.input('a')
        s.input('b', default=5)

    def _test_template(self, template):
        template.a = 2
        self.assertEqual(template.b, 5)
        with self.assertRaises(ValueError):
            template.c = 6

        # Check that we can unpack
        self.assertEqual(dict(**template)['a'], 2)
