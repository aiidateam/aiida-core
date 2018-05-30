"""Unit tests for plugin parameter type."""
import unittest
import mock

from aiida.cmdline.params.types.plugin import PluginParamType


class TestPluginParamType(unittest.TestCase):
    """Unit tests for plugin parameter type."""

    def setUp(self):
        self.param = PluginParamType(category='calculations')
        self.plugin1 = 'simpleplugins.templatereplacer'
        self.plugin2 = 'simpleplugins.arithmetic.add'

    def test_convert(self):
        param = mock.Mock()
        param.default = None
        self.assertEqual(self.param.convert(self.plugin1, param, None), self.plugin1)

    def test_complete(self):
        options = [item[0] for item in self.param.complete(None, 'simpleplugins')]
        self.assertIn(self.plugin1, options)
        self.assertIn(self.plugin2, options)
