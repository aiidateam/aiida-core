# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for postgres database maintenance functionality"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import unittest
import mock

from pgtest.pgtest import PGTest

from aiida.manage.external.postgres import Postgres


def _try_connect_always_fail(**kwargs):  # pylint: disable=unused-argument
    """Always return False"""
    return False


class PostgresTest(unittest.TestCase):
    """Test the public API provided by the `Postgres` class"""

    def setUp(self):
        """Set up a temporary database cluster for testing potentially destructive operations"""
        self.pg_test = PGTest(max_connections=11)  # set to 11 to avoid https://github.com/jamesnunn/pgtest/issues/9
        self.dbuser = 'aiida'
        self.dbpass = 'password'
        self.dbname = 'aiida_db'

    def tearDown(self):
        self.pg_test.close()

    def _setup_postgres(self):
        postgres = Postgres(interactive=False, quiet=True, dbinfo=self.pg_test.dsn)
        postgres.determine_setup()
        return postgres

    def test_determine_setup_fail(self):
        postgres = Postgres(interactive=False, quiet=True, dbinfo={'port': '11111'})
        setup_success = postgres.determine_setup()
        self.assertFalse(setup_success)

    def test_determine_setup_success(self):
        postgres = self._setup_postgres()
        self.assertTrue(postgres.pg_execute)

    def test_setup_fail_callback(self):
        """Make sure `determine_setup` works despite wrong initial values in case of correct callback"""

        def correct_setup(interactive, dbinfo):  # pylint: disable=unused-argument
            return self.pg_test.dsn

        postgres = Postgres(interactive=False, quiet=True, dbinfo={'port': '11111'})
        postgres.set_setup_fail_callback(correct_setup)
        postgres.determine_setup()
        self.assertTrue(postgres.pg_execute)

    @mock.patch('aiida.manage.external.postgres._try_connect_psycopg', new=_try_connect_always_fail)
    @mock.patch('aiida.manage.external.postgres._try_subcmd')
    def test_fallback_on_subcmd(self, try_subcmd):
        """Ensure that accessing postgres via subcommand is tried if psycopg does not work."""
        self._setup_postgres()
        self.assertTrue(try_subcmd.call_count >= 1)

    def test_create_drop_db_user(self):
        """Check creating and dropping a user works"""
        postgres = self._setup_postgres()
        postgres.create_dbuser(self.dbuser, self.dbpass)
        self.assertTrue(postgres.dbuser_exists(self.dbuser))
        postgres.drop_dbuser(self.dbuser)
        self.assertFalse(postgres.dbuser_exists(self.dbuser))

    def test_create_drop_db(self):
        """Check creating & destroying a database"""
        postgres = self._setup_postgres()
        postgres.create_dbuser(self.dbuser, self.dbpass)
        postgres.create_db(self.dbuser, self.dbname)
        self.assertTrue(postgres.db_exists(self.dbname))
        postgres.drop_db(self.dbname)
        self.assertFalse(postgres.db_exists(self.dbname))
