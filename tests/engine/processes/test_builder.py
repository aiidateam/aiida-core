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
import pytest

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine.processes.builder import ProcessBuilder
from aiida import orm


def test_access_methods():
    """Test for the access methods (setter, getter, delete).

    The setters are used again after calling the delete in order to check that they still work
    after the deletion (including the validation process).
    """
    node_numb = orm.Int(4)
    node_dict = orm.Dict(dict={'value': 4})

    # AS ITEMS
    builder = ProcessBuilder(ArithmeticAddCalculation)

    builder['x'] = node_numb
    assert dict(builder) == {'metadata': {'options': {'stash': {}}}, 'x': node_numb}

    del builder['x']
    assert dict(builder) == {'metadata': {'options': {'stash': {}}}}

    with pytest.raises(ValueError):
        builder['x'] = node_dict

    builder['x'] = node_numb
    assert dict(builder) == {'metadata': {'options': {'stash': {}}}, 'x': node_numb}

    # AS ATTRIBUTES
    del builder
    builder = ProcessBuilder(ArithmeticAddCalculation)

    builder.x = node_numb
    assert dict(builder) == {'metadata': {'options': {'stash': {}}}, 'x': node_numb}

    del builder.x
    assert dict(builder) == {'metadata': {'options': {'stash': {}}}}

    with pytest.raises(ValueError):
        builder.x = node_dict

    builder.x = node_numb
    assert dict(builder) == {'metadata': {'options': {'stash': {}}}, 'x': node_numb}
