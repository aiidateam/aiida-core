# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-self-use
"""Unit tests for the backend non-specific utility methods."""
import math

import pytest

from aiida.common import exceptions
from aiida.orm.implementation.utils import FIELD_SEPARATOR, clean_value, validate_attribute_extra_key


class TestOrmImplementationUtils:
    """Test the utility methods in aiida.orm.implementation.utils"""

    @pytest.mark.parametrize(
        'invalid_key',
        (
            5,
            f'invalid{FIELD_SEPARATOR}key',  # Top-level keys
            {
                'a': {
                    5: 'b'
                }
            },
            {
                'a': {
                    f'invalid{FIELD_SEPARATOR}key': 'b'
                }
            }  # Nested keys
        )
    )
    def test_invalid_attribute_extra_key(self, invalid_key):
        """Test supplying an invalid key to the `validate_attribute_extra_key` method."""

        with pytest.raises(exceptions.ValidationError):
            validate_attribute_extra_key(invalid_key)

    @pytest.mark.parametrize('invalid_value', (math.nan, math.inf))
    def test_invalid_value(self, invalid_value):
        """Test supplying nan and inf values to the `clean_value` method."""

        with pytest.raises(exceptions.ValidationError):
            clean_value(invalid_value)
