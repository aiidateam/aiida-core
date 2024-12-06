###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for StructureData-related functions."""

import pytest

from aiida.orm.nodes.data.structure import StructureData, get_formula


def test_get_formula_hill():
    """Make sure 'hill' and 'hill_compact' modes actually sort according to hill notation

    Wikipedia reference for the Hill system:
    https://en.wikipedia.org/wiki/Chemical_formula#Hill_system
    """
    symbol_lists = [
        (['F', 'H', 'O', 'N', 'Zn', 'C', 'H', 'C'], 'C2 H2 F N O Zn'),
        (['F', 'O', 'N', 'Zn'], 'F N O Zn'),
        (['F', 'O', 'N', 'C', 'Zn', 'C'], 'C2 F N O Zn'),
        (['F', 'H', 'O', 'N', 'Zn', 'H'], 'F H2 N O Zn'),
    ]
    for symbol_list, expected_result in symbol_lists:
        assert get_formula(symbol_list, mode='hill', separator=' ') == expected_result
        assert get_formula(symbol_list, mode='hill_compact', separator=' ') == expected_result


@pytest.mark.parametrize(
    'mode, expected',
    (
        ('full', {'Ba': 2, 'Zr': 2, 'O': 6}),
        ('reduced', {'Ba': 1, 'Zr': 1, 'O': 3}),
        ('fractional', {'Ba': 0.2, 'Zr': 0.2, 'O': 0.6}),
    ),
)
def test_get_composition(mode, expected):
    """Test the ``mode`` argument of ``StructureData.get_composition``."""
    symbols = ['Ba', 'Ba', 'Zr', 'Zr', 'O', 'O', 'O', 'O', 'O', 'O']
    structure = StructureData()

    for symbol in symbols:
        structure.append_atom(name=symbol, symbols=[symbol], position=[0, 0, 0])

    assert structure.get_composition(mode=mode) == expected
