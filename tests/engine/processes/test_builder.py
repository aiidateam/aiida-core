# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `aiida.engine.processes.builder.ProcessBuilder`."""

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine.processes.builder import ProcessBuilder


def test_access_methods():
    """Test for the access methods (setter, getter, delete)."""
    builder = ProcessBuilder(ArithmeticAddCalculation)

    # AS ITEMS
    builder['metadata'] = {'label': 'test'}
    assert dict(builder) == {'metadata': {'label': 'test'}}
    del builder['metadata']
    assert dict(builder) == {}

    # AS ATTRIBUTES
    builder.metadata = {'label': 'test'}
    assert dict(builder) == {'metadata': {'label': 'test'}}
    del builder.metadata
    assert dict(builder) == {}
