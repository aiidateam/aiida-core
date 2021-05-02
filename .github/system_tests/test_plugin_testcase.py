# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Test the plugin test case

This must be in a standalone script because it would clash with other tests,
Since the dbenv gets loaded on the temporary profile.
"""

import sys
import unittest
import tempfile
import shutil

from aiida.manage.tests.unittest_classes import PluginTestCase, TestRunner


class PluginTestCase1(PluginTestCase):
    """
    Test the PluginTestCase from utils.fixtures
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data = self.get_data()
        self.data_pk = self.data.pk
        self.computer = self.get_computer(temp_dir=self.temp_dir)

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.temp_dir)

    @staticmethod
    def get_data():
        """
        Return some Dict
        """
        from aiida.plugins import DataFactory
        data = DataFactory('dict')(dict={'data': 'test'})
        data.store()
        return data

    @classmethod
    def get_computer(cls, temp_dir):
        """
        Create and store a new computer, and return it
        """
        from aiida import orm

        computer = orm.Computer(
            label='localhost',
            hostname='localhost',
            description='my computer',
            transport_type='local',
            scheduler_type='direct',
            workdir=temp_dir,
            backend=cls.backend
        ).store()
        return computer

    def test_data_loaded(self):
        """
        Check that the data node is indeed in the DB when calling load_node
        """
        from aiida import orm
        self.assertEqual(orm.load_node(self.data_pk).uuid, self.data.uuid)

    def test_computer_loaded(self):
        """
        Check that the computer is indeed in the DB when calling load_node

        Note: Important to have at least two test functions in order to verify things
        work after resetting the DB.
        """
        from aiida import orm
        self.assertEqual(orm.Computer.objects.get(label='localhost').uuid, self.computer.uuid)

    def test_tear_down(self):
        """
        Check that after tearing down, the previously stored nodes
        are not there anymore.
        """
        from aiida.orm import load_node
        super().tearDown()  # reset DB
        with self.assertRaises(Exception):
            load_node(self.data_pk)


class PluginTestCase2(PluginTestCase):
    """
    Second PluginTestCase.
    """

    def test_dummy(self):
        """
        Dummy test for 2nd PluginTestCase class.

        Just making sure that setup/teardown is safe for
        multiple testcase classes (this was broken in #1425).
        """
        super().tearDown()


if __name__ == '__main__':
    MODULE = sys.modules[__name__]
    SUITE = unittest.defaultTestLoader.loadTestsFromModule(MODULE)
    RESULT = TestRunner().run(SUITE)

    EXIT_CODE = int(not RESULT.wasSuccessful())
    sys.exit(EXIT_CODE)
