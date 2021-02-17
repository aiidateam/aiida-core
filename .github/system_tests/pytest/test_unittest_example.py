# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test running unittest test cases through pytest."""
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
