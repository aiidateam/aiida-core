# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :py:mod:`~aiida.plugins.entry_point` module."""

from aiida.backends.testbase import AiidaTestCase
from aiida.plugins.entry_point import validate_registered_entry_points


class TestEntryPoint(AiidaTestCase):
    """Tests for the :py:mod:`~aiida.plugins.entry_point` module."""

    @staticmethod
    def test_validate_registered_entry_points():
        """Test the `validate_registered_entry_points` function."""
        validate_registered_entry_points()
