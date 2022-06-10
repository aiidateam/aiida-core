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
import cmath
import math

import pytest

from aiida.common import exceptions
from aiida.orm.implementation.utils import FIELD_SEPARATOR, clean_value, validate_attribute_extra_key


class TestOrmImplementationUtils:
    """Test the utility methods in aiida.orm.implementation.utils"""

    def test_invalid_attribute_extra_key(self):
        """Test supplying an invalid key to the `validate_attribute_extra_key` method."""
        non_string_key = 5
        field_separator_key = f'invalid{FIELD_SEPARATOR}key'

        with pytest.raises(exceptions.ValidationError):
            validate_attribute_extra_key(non_string_key)

        with pytest.raises(exceptions.ValidationError):
            validate_attribute_extra_key(field_separator_key)

    def test_invalid_value(self):
        """Test supplying nan and inf values to the `clean_value` method."""
        nan_value = math.nan
        inf_value = math.inf

        with pytest.raises(exceptions.ValidationError):
            clean_value(nan_value)

        with pytest.raises(exceptions.ValidationError):
            clean_value(inf_value)

    def test_invalid_complex_value(self):
        """Test supplying complex nan and inf values to the `clean_value` method."""
        nan_value = cmath.nan
        inf_value = cmath.inf

        with pytest.raises(exceptions.ValidationError):
            clean_value(nan_value)

        with pytest.raises(exceptions.ValidationError):
            clean_value(inf_value)

    def test_reserved_complex_key(self):
        """Test supplying a mapping with the reserved
        `__complex__` key to the `clean_value` method."""
        mapping = {'__complex__': ''}

        with pytest.raises(exceptions.ValidationError):
            clean_value(mapping)
