###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for postgres database maintenance functionality"""

from unittest import TestCase

import pytest

from aiida.manage.external.postgres import Postgres


@pytest.mark.requires_psql
class PostgresTest(TestCase):
    """Test the public API provided by the `Postgres` class"""

    def setUp(self):
        """Set up a temporary database cluster for testing potentially destructive operations"""
        from pgtest.pgtest import PGTest

        self.pg_test = PGTest()
        self.dbuser = 'aiida'
        self.dbpass = 'password'
        self.dbname = 'aiida_db'

    def tearDown(self):
        self.pg_test.close()

    def _setup_postgres(self):
        return Postgres(interactive=False, quiet=True, dbinfo=self.pg_test.dsn)

    def test_determine_setup_fail(self):
        """Check that setup fails, if bad port is provided.

        Note: In interactive mode, this would prompt for the connection details.
        """
        postgres = Postgres(interactive=False, quiet=True, dbinfo={'port': '11111'})
        self.assertFalse(postgres.is_connected)

    def test_determine_setup_success(self):
        """Check that setup works with default parameters."""
        postgres = self._setup_postgres()
        self.assertTrue(postgres.is_connected)

    def test_create_drop_db_user(self):
        """Check creating and dropping a user works"""
        postgres = self._setup_postgres()
        postgres.create_dbuser(self.dbuser, self.dbpass)
        self.assertTrue(postgres.dbuser_exists(self.dbuser))

        self.assertTrue(postgres.can_user_authenticate(self.dbuser, self.dbpass))
        self.assertFalse(postgres.can_user_authenticate('non-existent-db-user', self.dbpass))
        # note: connection with wrong password may work, if postgres server is set to trust local connections
        # self.assertFalse(postgres.can_user_connect(self.dbuser, 'wrong-password'))

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

    def test_create_dbuser_db_safe(self):
        """Test creating a database and user in a safe way"""
        postgres = self._setup_postgres()
        user1, db1 = postgres.create_dbuser_db_safe(self.dbname, self.dbuser, self.dbpass)
        assert user1 == self.dbuser
        assert db1 == self.dbname

        # a second try should reuse the database user but create a new database
        user2, db2 = postgres.create_dbuser_db_safe(self.dbname, self.dbuser, self.dbpass)
        assert user2 == self.dbuser
        assert db2 == f'{self.dbname}_1'
