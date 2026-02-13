###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for StructureData-related functions."""

import numpy as np
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


class TestCellAngles:
    """Tests for ``StructureData.cell_angles`` with zero-length vectors."""

    def test_orthogonal_cell(self):
        """Test angles of an orthogonal cell are all 90 degrees."""
        structure = StructureData(cell=((2.0, 0.0, 0.0), (0.0, 3.0, 0.0), (0.0, 0.0, 4.0)))
        np.testing.assert_allclose(structure.cell_angles, [90.0, 90.0, 90.0])

    def test_non_orthogonal_cell(self):
        """Test angles of a non-orthogonal cell."""
        structure = StructureData(cell=((1.0, 0.0, 0.0), (0.5, 0.5, 0.0), (0.0, 0.0, 1.0)))
        angles = structure.cell_angles
        np.testing.assert_allclose(angles[0], 90.0)  # alpha: angle(b, c)
        np.testing.assert_allclose(angles[1], 90.0)  # beta: angle(a, c)
        np.testing.assert_allclose(angles[2], 45.0)  # gamma: angle(a, b)

    def test_all_zero_vectors_raises(self):
        """Test that all-zero cell vectors raise ``ValueError``."""
        structure = StructureData(cell=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
        with pytest.raises(ValueError, match='all zero-length vectors'):
            structure.cell_angles

    def test_one_zero_vector(self):
        """Test that a single zero-length vector gives ``None`` for affected angles."""
        # First vector (a) is zero -> beta (a,c) and gamma (a,b) are None, alpha (b,c) is valid
        structure = StructureData(cell=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
        angles = structure.cell_angles
        np.testing.assert_allclose(angles[0], 90.0)  # alpha: angle(b, c)
        assert angles[1] is None  # beta: angle(a, c)
        assert angles[2] is None  # gamma: angle(a, b)

    def test_two_zero_vectors(self):
        """Test that two zero-length vectors give ``None`` for all angles."""
        structure = StructureData(cell=((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
        angles = structure.cell_angles
        assert angles[0] is None  # alpha: angle(b, c)
        assert angles[1] is None  # beta: angle(a, c)
        assert angles[2] is None  # gamma: angle(a, b)
