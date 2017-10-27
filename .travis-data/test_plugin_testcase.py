"""
Test the plugin test case

This must be in a standalone script because it would clash with other tests,
Since the dbenv gets loaded on the temporary profile.
"""
import os
import unittest
import tempfile
import shutil

from aiida.utils.fixtures import PluginTestCase
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
from aiida import is_dbenv_loaded


def determine_backend():
    return BACKEND_DJANGO if os.environ.get(
        'TEST_AIIDA_BACKEND', BACKEND_DJANGO) == BACKEND_DJANGO else BACKEND_SQLA


class PluginTestcaseTestCase(PluginTestCase):
    BACKEND = determine_backend()

    def setUp(self):
        from aiida.orm import DataFactory
        from aiida.orm import Computer
        self.temp_dir = tempfile.mkdtemp()
        self.data = self.get_data()
        self.data_pk = self.data.pk
        self.computer = self.get_computer(temp_dir=self.temp_dir)

    def get_data(self):
        from aiida.orm import DataFactory
        data = DataFactory('parameter')(dict={'data': 'test'})
        data.store()
        return data

    def get_computer(self, temp_dir):
        from aiida.orm import Computer
        computer = Computer(
            name='localhost',
            description='my computer',
            hostname='localhost',
            workdir=temp_dir,
            transport_type='local',
            scheduler_type='direct',
            enabled_state=True)
        computer.store()
        return computer

    def test_data_loaded(self):
        from aiida.orm import Computer
        from aiida.orm import load_node
        self.assertTrue(is_dbenv_loaded())
        self.assertEqual(load_node(self.data_pk).uuid, self.data.uuid)
        self.assertEqual(Computer.get('localhost').uuid, self.computer.uuid)


    def test_tear_down(self):
        from aiida.orm import load_node
        super(PluginTestcaseTestCase, self).tearDown()
        with self.assertRaises(Exception):
            load_node(self.data_pk)
        shutil.rmtree(self.temp_dir)


if __name__ == '__main__':
    unittest.main()
