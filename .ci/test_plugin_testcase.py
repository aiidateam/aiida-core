# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Test the plugin test case

This must be in a standalone script because it would clash with other tests,
Since the dbenv gets loaded on the temporary profile.
"""
import os
import sys
import unittest
import tempfile
import shutil

from aiida.utils.fixtures import PluginTestCase, TestRunner
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
from aiida import is_dbenv_loaded


def determine_backend():
    return BACKEND_DJANGO if os.environ.get('TEST_AIIDA_BACKEND', BACKEND_DJANGO) == BACKEND_DJANGO else BACKEND_SQLA


class PluginTestCase1(PluginTestCase):
    """
    Test the PluginTestCase from utils.fixtures
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data = self.get_data()
        self.data_pk = self.data.pk
        self.computer = self.get_computer(temp_dir=self.temp_dir)

    @staticmethod
    def get_data():
        """
        Return some ParameterData
        """
        from aiida.orm.utils import DataFactory
        data = DataFactory('parameter')(dict={'data': 'test'})
        data.store()
        return data

    @staticmethod
    def get_computer(temp_dir):
        """
        Create and store a new computer, and return it
        """
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
        """
        Check that the data is indeed in the DB when calling load_node
        """
        from aiida.orm import Computer
        from aiida.orm.utils import load_node
        self.assertTrue(is_dbenv_loaded())
        self.assertEqual(load_node(self.data_pk).uuid, self.data.uuid)
        self.assertEqual(Computer.get('localhost').uuid, self.computer.uuid)

    def test_tear_down(self):
        """
        Check that after tearing down, the previously stored nodes
        are not there anymore. Then remove the temporary folder.
        """
        from aiida.orm import load_node
        super(PluginTestCase1, self).tearDown()
        with self.assertRaises(Exception):
            load_node(self.data_pk)
        shutil.rmtree(self.temp_dir)


class PluginTestCase2(PluginTestCase):
    """
    Second PluginTestCase.
    """

    def test_stupid(self):
        """
        Dummy test for 2nd plugin testcase class.

        Just making sure that setup/teardown is safe for
        multiple testcase classes (this was broken in #1425).
        """
        super(PluginTestCase2, self).tearDown()


if __name__ == '__main__':
    MODULE = sys.modules[__name__]
    SUITE = unittest.defaultTestLoader.loadTestsFromModule(MODULE)
    TestRunner().run(SUITE, backend=determine_backend())
