"""Test running unittest test cases through pytest."""
from __future__ import absolute_import
import unittest
import pytest


class TestInt(unittest.TestCase):
    """Test integers - Compatible with pytest."""

    @pytest.fixture(autouse=True)
    def setup_temp_dir(self, temp_dir):
        self.temp_dir = temp_dir  # pylint: disable=attribute-defined-outside-init

    def test_int(self):  # pylint: disable=no-self-use
        """Just testing that the database environment is available and working."""
        from aiida import orm
        i = orm.Int(5)
        i.store()

    def test_temp_dir(self):
        """Test that temp dir was set."""
        assert self.temp_dir is not None
