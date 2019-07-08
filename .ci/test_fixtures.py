# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unittests for plugin test fixture manager"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os
import unittest

from pgtest import pgtest

from aiida.manage.fixtures import FixtureManager, FixtureError
from aiida.common.utils import Capturing
from aiida.backends import BACKEND_DJANGO, BACKEND_SQLA


class FixtureManagerTestCase(unittest.TestCase):
    """Test the FixtureManager class"""

    def setUp(self):
        self.fixture_manager = FixtureManager()
        self.backend = BACKEND_DJANGO if os.environ.get('TEST_AIIDA_BACKEND',
                                                        BACKEND_DJANGO) == BACKEND_DJANGO else BACKEND_SQLA
        self.fixture_manager.backend = self.backend

    def test_create_db_cluster(self):
        self.fixture_manager.create_db_cluster()
        self.assertTrue(pgtest.is_server_running(self.fixture_manager.pg_cluster.cluster))

    def test_create_aiida_db(self):
        self.fixture_manager.create_db_cluster()
        self.fixture_manager.create_aiida_db()
        self.assertTrue(self.fixture_manager.postgres.db_exists(self.fixture_manager.db_name))

    def test_create_use_destroy_profile(self):
        """
        Test temporary test profile creation

        * The profile gets created, the dbenv loaded
        * Data can be stored in the db
        * reset_db deletes all data added after profile creation
        * destroy_all removes all traces of the test run
        """
        with Capturing() as output:
            self.fixture_manager.create_profile()

        self.assertTrue(self.fixture_manager.root_dir_ok, msg=output)
        self.assertTrue(self.fixture_manager.config_dir_ok, msg=output)
        self.assertTrue(self.fixture_manager.repo_ok, msg=output)
        from aiida.manage.configuration.settings import AIIDA_CONFIG_FOLDER
        self.assertEqual(AIIDA_CONFIG_FOLDER, self.fixture_manager.config_dir, msg=output)

        from aiida.orm import load_node
        from aiida.plugins import DataFactory
        data = DataFactory('dict')(dict={'key': 'value'})
        data.store()
        data_pk = data.pk
        self.assertTrue(load_node(data_pk))

        with self.assertRaises(FixtureError):
            self.test_create_aiida_db()

        self.fixture_manager.reset_db()
        with self.assertRaises(Exception):
            load_node(data_pk)

        temp_dir = self.fixture_manager.root_dir
        self.fixture_manager.destroy_all()
        with self.assertRaises(Exception):
            self.fixture_manager.postgres.db_exists(self.fixture_manager.db_name)
        self.assertFalse(os.path.exists(temp_dir))
        self.assertIsNone(self.fixture_manager.root_dir)
        self.assertIsNone(self.fixture_manager.pg_cluster)

    def tearDown(self):
        self.fixture_manager.destroy_all()


if __name__ == '__main__':
    unittest.main()
