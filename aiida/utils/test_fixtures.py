"""Unittests for plugin test fixture manager"""
import unittest

from pgtest import pgtest

from aiida.utils.fixtures import FixtureManager


class FixtureManagerTestCase(unittest.TestCase):
    """Test the FixtureManager class"""

    def setUp(self):
        self.fixture_manager = FixtureManager()

    def test_create_db_cluster(self):
        self.fixture_manager.create_db_cluster()
        self.assertTrue(
            pgtest.is_server_running(self.fixture_manager.pg_cluster.cluster))

    def tearDown(self):
        self.fixture_manager.destroy_all()
