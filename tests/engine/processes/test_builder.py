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
import re

from IPython.lib.pretty import pretty
import pytest

from aiida import orm
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine.processes.builder import ProcessBuilder


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


def test_pretty_repr():
    """Test the pretty representation of the ``ProcessBuilder`` class."""
    builder = ProcessBuilder(ArithmeticAddCalculation)

    builder.x = orm.Int(3)
    builder.y = orm.Int(1)
    builder.metadata.options.resources = {'num_machines': 1}  # pylint: disable=no-member

    pretty_repr = \
    """Process class: ArithmeticAddCalculation
    Inputs:
    "metadata": {
        "options": {
            "resources": {
                "num_machines": 1
            },
            "stash": {}
        },
    },
    "x": 3
    "y": 1"""
    pretty_repr = re.sub(r'(?m)^\s{4}', '', pretty_repr)

    assert pretty(builder) == pretty_repr
