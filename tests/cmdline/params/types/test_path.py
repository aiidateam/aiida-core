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
import pytest

from aiida.cmdline.params.types.path import PathOrUrl, check_timeout_seconds


class TestPath:
    """Tests for `PathOrUrl` and `FileOrUrl`"""

    def test_default_timeout(self):
        """Test the default timeout_seconds value is correct"""
        from aiida.cmdline.params.types.path import URL_TIMEOUT_SECONDS

        import_path = PathOrUrl()

        assert import_path.timeout_seconds == URL_TIMEOUT_SECONDS

    def test_timeout_checks(self):
        """Test that timeout check handles different values.

         * valid
         * none
         * wrong type
         * outside range
        """
        valid_values = [42, '42']

        for value in valid_values:
            assert check_timeout_seconds(value) == int(value)

        for invalid in [None, 'test']:
            with pytest.raises(TypeError):
                check_timeout_seconds(invalid)

        for invalid in [-5, 65]:
            with pytest.raises(ValueError):
                check_timeout_seconds(invalid)
