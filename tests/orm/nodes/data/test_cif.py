###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for cif related functions."""

import pytest

from aiida.orm.nodes.data.cif import parse_formula


def test_parse_formula():
    """Test the `parse_formula` utility function."""
    assert parse_formula('C H') == {'C': 1, 'H': 1}
    assert parse_formula('C5 H1') == {'C': 5, 'H': 1}
    assert parse_formula('Ca5 Ho') == {'Ca': 5, 'Ho': 1}
    assert parse_formula('H0.5 O') == {'H': 0.5, 'O': 1}
    assert parse_formula('C0 O0') == {'C': 0, 'O': 0}
    assert parse_formula('C1 H1 ') == {'C': 1, 'H': 1}
    assert parse_formula(' C1 H1') == {'C': 1, 'H': 1}
    assert parse_formula('CaHClO') == {'Ca': 1, 'H': 1, 'Cl': 1, 'O': 1}
    assert parse_formula('C70 H108 Al4 La4 N4 O10') == {'C': 70, 'H': 108, 'Al': 4, 'La': 4, 'N': 4, 'O': 10}
    assert parse_formula('C70H108Al4Li4N4O10') == {'C': 70, 'H': 108, 'Al': 4, 'Li': 4, 'N': 4, 'O': 10}
    assert parse_formula('C36 H59LiN2 O3 Si') == {'C': 36, 'H': 59, 'Li': 1, 'N': 2, 'O': 3, 'Si': 1}
    assert parse_formula('C63.5H83.5Li2N2O3.25P2') == {'C': 63.5, 'H': 83.5, 'Li': 2, 'N': 2, 'O': 3.25, 'P': 2}
    assert parse_formula('Fe Li0.667 O4 P1') == {'Fe': 1, 'Li': 0.667, 'O': 4, 'P': 1}
    assert parse_formula('Fe2.05Ni0.05O4 Zn0.9') == {'Fe': 2.05, 'Ni': 0.05, 'O': 4, 'Zn': 0.9}
    assert parse_formula('Li3O6(Al0.23Li0.77)2(Li0.07Te0.93)') == {'Li': 4.61, 'O': 6, 'Al': 0.46, 'Te': 0.93}
    assert parse_formula('Li2{Cr0.05Li0.95X0.00}{Cr0.24Li0.76}2{Li0.02Te0.98}O6') == {
        'Li': 4.49,
        'Cr': 0.53,
        'X': 0,
        'Te': 0.98,
        'O': 6,
    }
    assert parse_formula('C[NH2]3NO3') == {'C': 1, 'N': 4, 'H': 6, 'O': 3}
    assert parse_formula('H80 C104{C0.50 X0.50}8N8 Cl4(Cl0.50X0.50)8.0O8') == {
        'H': 80,
        'C': 108.0,
        'X': 8.0,
        'N': 8,
        'Cl': 8.0,
        'O': 8,
    }
    assert parse_formula('Na1.28[NH]0.28{N H2}0.72') == {'Na': 1.28, 'N': 1.0, 'H': 1.72}

    for test_formula in ('H0.5.2 O', 'Fe2.05Ni0.05.4', 'Na1.28[NH]0.28.3{NH2}0.72'):
        with pytest.raises(ValueError):
            parse_formula(test_formula)
