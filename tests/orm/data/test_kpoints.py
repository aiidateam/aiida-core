# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `KpointsData` class."""

import numpy as np

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import KpointsData, load_node, StructureData


class TestKpoints(AiidaTestCase):
    """Test for the `Kpointsdata` class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        alat = 5.430  # angstrom
        cell = [[
            0.5 * alat,
            0.5 * alat,
            0.,
        ], [
            0.,
            0.5 * alat,
            0.5 * alat,
        ], [0.5 * alat, 0., 0.5 * alat]]
        cls.alat = alat
        structure = StructureData(cell=cell)
        structure.append_atom(position=(0.000 * alat, 0.000 * alat, 0.000 * alat), symbols=['Si'])
        structure.append_atom(position=(0.250 * alat, 0.250 * alat, 0.250 * alat), symbols=['Si'])
        cls.structure = structure
        # Define the expected reciprocal cell
        val = 2. * np.pi / alat
        cls.expected_reciprocal_cell = np.array([[val, val, -val], [-val, val, val], [val, -val, val]])

    def test_reciprocal_cell(self):
        """
        Test the `reciprocal_cell` method.

        This is a regression test for #2749.
        """
        kpt = KpointsData()
        kpt.set_cell_from_structure(self.structure)

        self.assertEqual(np.abs(kpt.reciprocal_cell - self.expected_reciprocal_cell).sum(), 0.)

        # Check also after storing
        kpt.store()
        kpt2 = load_node(kpt.pk)
        self.assertEqual(np.abs(kpt2.reciprocal_cell - self.expected_reciprocal_cell).sum(), 0.)

    def test_get_kpoints(self):
        """Test the `get_kpoints` method."""
        kpt = KpointsData()
        kpt.set_cell_from_structure(self.structure)

        kpoints = [
            [0., 0., 0.],
            [0.5, 0.5, 0.5],
        ]

        cartesian_kpoints = [
            [0., 0., 0.],
            [np.pi / self.alat, np.pi / self.alat, np.pi / self.alat],
        ]

        kpt.set_kpoints(kpoints)
        self.assertEqual(np.abs(kpt.get_kpoints() - np.array(kpoints)).sum(), 0.)
        self.assertEqual(np.abs(kpt.get_kpoints(cartesian=True) - np.array(cartesian_kpoints)).sum(), 0.)

        # Check also after storing
        kpt.store()
        kpt2 = load_node(kpt.pk)
        self.assertEqual(np.abs(kpt2.get_kpoints() - np.array(kpoints)).sum(), 0.)
        self.assertEqual(np.abs(kpt2.get_kpoints(cartesian=True) - np.array(cartesian_kpoints)).sum(), 0.)
