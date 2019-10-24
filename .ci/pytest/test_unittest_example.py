"""Test running unittest test cases through pytest."""
from __future__ import absolute_import
import unittest


class TestInt(unittest.TestCase):
    """Test integers - Compatible with pytest."""

    def test_int(self):  # pylint: disable=no-self-use
        """Just testing that the database environment is available and working."""
        from aiida import orm
        i = orm.Int(5)
        i.store()
