# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unittests for TestManager"""
import os
import sys
import unittest
import warnings

from pgtest import pgtest
import pytest

from aiida.common.utils import Capturing
from aiida.manage.tests import TemporaryProfileManager, TestManagerError, get_test_backend_name


class TemporaryProfileManagerTestCase(unittest.TestCase):
    """Test the TemporaryProfileManager class"""

    def setUp(self):
        if sys.version_info[0] >= 3:
            # tell unittest not to warn about running processes
            warnings.simplefilter('ignore', ResourceWarning)  # pylint: disable=no-member,undefined-variable

        self.backend = get_test_backend_name()
        self.profile_manager = TemporaryProfileManager(backend=self.backend)

    def tearDown(self):
        self.profile_manager.destroy_all()

    def test_create_db_cluster(self):
        self.profile_manager.create_db_cluster()
        self.assertTrue(pgtest.is_server_running(self.profile_manager.pg_cluster.cluster))

    def test_create_aiida_db(self):
        self.profile_manager.create_db_cluster()
        self.profile_manager.create_aiida_db()
        self.assertTrue(self.profile_manager.postgres.db_exists(self.profile_manager.profile_info['database_name']))

    @pytest.mark.filterwarnings('ignore:Creating AiiDA configuration folder')
    def test_create_use_destroy_profile2(self):
        """
        Test temporary test profile creation

        * The profile gets created, the dbenv loaded
        * Data can be stored in the db
        * reset_db deletes all data added after profile creation
        * destroy_all removes all traces of the test run

        Note: This test function loads the dbenv - i.e. you cannot run similar test functions (that create profiles)
        in the same test session. aiida.manage.configuration.reset_profile() was not yet enough, see
        https://github.com/aiidateam/aiida-core/issues/3482
        """
        with Capturing() as output:
            self.profile_manager.create_profile()

        self.assertTrue(self.profile_manager.root_dir_ok, msg=output)
        self.assertTrue(self.profile_manager.config_dir_ok, msg=output)
        self.assertTrue(self.profile_manager.repo_ok, msg=output)
        from aiida.manage.configuration.settings import AIIDA_CONFIG_FOLDER
        self.assertEqual(str(AIIDA_CONFIG_FOLDER), self.profile_manager.config_dir, msg=output)

        from aiida.orm import load_node
        from aiida.plugins import DataFactory
        data = DataFactory('core.dict')(dict={'key': 'value'})
        data.store()
        data_pk = data.pk
        self.assertTrue(load_node(data_pk))

        with self.assertRaises(TestManagerError):
            self.test_create_aiida_db()

        self.profile_manager.clear_profile()
        with self.assertRaises(Exception):
            load_node(data_pk)

        temp_dir = self.profile_manager.root_dir
        self.profile_manager.destroy_all()
        with self.assertRaises(Exception):
            self.profile_manager.postgres.db_exists(self.profile_manager.dbinfo['db_name'])
        self.assertFalse(os.path.exists(temp_dir))
        self.assertIsNone(self.profile_manager.root_dir)
        self.assertIsNone(self.profile_manager.pg_cluster)


if __name__ == '__main__':
    unittest.main()
