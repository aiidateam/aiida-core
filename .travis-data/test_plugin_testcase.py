"""
Test the plugin test case

This must be in a standalone script because it would clash with other tests,
Since the dbenv gets loaded on the temporary profile.
"""
import os
import unittest

from aiida.utils.fixtures import PluginTestCase
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
from aiida import is_dbenv_loaded


def determine_backend():
    return BACKEND_DJANGO if os.environ.get(
        'TEST_AIIDA_BACKEND',
        BACKEND_DJANGO) == BACKEND_DJANGO else BACKEND_SQLA


class PluginTestcaseTestCase(PluginTestCase):
    """Test the PluginTestcase from utils.fixtures"""
    BACKEND = determine_backend()

    def setUp(self):
        from aiida.orm import DataFactory
        self.data = DataFactory('parameter')(dict={'data': 'test'})
        self.data.store()
        self.data_pk = self.data.pk

    def test_data_loaded(self):
        from aiida.orm import load_node
        self.assertTrue(is_dbenv_loaded())
        load_node(self.data_pk)

    def test_tear_down(self):
        from aiida.orm import load_node
        super(PluginTestcaseTestCase, self).tearDown()
        with self.assertRaises(Exception):
            load_node(self.data_pk)


if __name__ == '__main__':
    unittest.main()
