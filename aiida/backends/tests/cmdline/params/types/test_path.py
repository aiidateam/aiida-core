# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for Path types"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types import ImportPath


class TestImportPath(AiidaTestCase):
    """Tests `ImportPath`"""

    def test_default_timeout(self):
        """Test the default timeout_seconds value is correct"""
        from aiida.cmdline.params.types.path import URL_TIMEOUT_SECONDS

        import_path = ImportPath()

        self.assertEqual(import_path.timeout_seconds, URL_TIMEOUT_SECONDS)

    def test_valid_timeout(self):
        """Test a valid timeout_seconds value"""

        valid_values = [42, "42"]

        for value in valid_values:
            import_path = ImportPath(timeout_seconds=value)

            self.assertEqual(import_path.timeout_seconds, int(value))

    def test_none_timeout(self):
        """Test a TypeError is raised when a None value is given for timeout_seconds"""

        with self.assertRaises(TypeError):
            ImportPath(timeout_seconds=None)

    def test_wrong_type_timeout(self):
        """Test a TypeError is raised when wrong type is given for timeout_seconds"""

        with self.assertRaises(TypeError):
            ImportPath(timeout_seconds="test")

    def test_range_timeout(self):
        """Test timeout_seconds defines extrema when out of range
        Range of timeout_seconds is [0;60], extrema included.
        """

        range_timeout = [0, 60]
        lower = range_timeout[0] - 5
        upper = range_timeout[1] + 5

        lower_path = ImportPath(timeout_seconds=lower)
        upper_path = ImportPath(timeout_seconds=upper)

        msg_lower = "timeout_seconds should have been corrected to the lower bound: '{}', but instead it is {}".format(
            range_timeout[0], lower_path.timeout_seconds)
        self.assertEqual(lower_path.timeout_seconds, range_timeout[0], msg_lower)

        msg_upper = "timeout_seconds should have been corrected to the upper bound: '{}', but instead it is {}".format(
            range_timeout[1], upper_path.timeout_seconds)
        self.assertEqual(upper_path.timeout_seconds, range_timeout[1], msg_upper)
