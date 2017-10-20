"""Test the plugin test case"""
import os

from aiida.utils.fixtures import PluginTestCase
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA


def determine_backend():
    return BACKEND_DJANGO if os.environ.get(
        'TEST_AIIDA_BACKEND', BACKEND_DJANGO) == BACKEND_DJANGO else BACKEND_SQLA


class PluginTestcaseTestCase(PluginTestCase):
    BACKEND = determine_backend()

    def setUp(self):
        from aiida.orm import DataFactory
        self.data = DataFactory('parameter')(dict={'data': 'test'})
        self.data.save()
        self.data_pk = self.data.pk

    def test_data_loaded(self):
        from aiida.orm import load_node
        load_node(self.data_pk)

    def tearDown(self):
        from aiida.orm import load_node
        super(PluginTestCase, self).tearDown()
        with self.assertRaises(Exception):
            load_node(self.data_pk)

