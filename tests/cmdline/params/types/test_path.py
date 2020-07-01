# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for Path types"""

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.params.types.path import PathOrUrl, _check_timeout_seconds


class TestPath(AiidaTestCase):
    """Tests for `PathOrUrl` and `FileOrUrl`"""

    def test_default_timeout(self):
        """Test the default timeout_seconds value is correct"""
        from aiida.cmdline.params.types.path import URL_TIMEOUT_SECONDS

        import_path = PathOrUrl()

        self.assertEqual(import_path.timeout_seconds, URL_TIMEOUT_SECONDS)

    def test_timeout_checks(self):
        """Test that timeout check handles different values.

         * valid
         * none
         * wrong type
         * outside range
        """
        valid_values = [42, '42']

        for value in valid_values:
            self.assertEqual(_check_timeout_seconds(value), int(value))

        for invalid in [None, 'test']:
            with self.assertRaises(TypeError):
                _check_timeout_seconds(invalid)

        for invalid in [-5, 65]:
            with self.assertRaises(ValueError):
                _check_timeout_seconds(invalid)
