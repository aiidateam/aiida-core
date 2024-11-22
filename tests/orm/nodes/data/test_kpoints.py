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
import pytest

from aiida.orm import KpointsData, StructureData, load_node
from aiida.orm.nodes.data.structure import has_atomistic

skip_atomistic = pytest.mark.skipif(not has_atomistic(), reason='Unable to import aiida-atomistic')

class TestKpoints:
    """Test for the `Kpointsdata` class."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        alat = 5.430  # angstrom
        cell = [
            [
                0.5 * alat,
                0.5 * alat,
                0.0,
            ],
            [
                0.0,
                0.5 * alat,
                0.5 * alat,
            ],
            [0.5 * alat, 0.0, 0.5 * alat],
        ]
        self.alat = alat
        structure = StructureData(cell=cell)
        structure.append_atom(position=(0.000 * alat, 0.000 * alat, 0.000 * alat), symbols=['Si'])
        structure.append_atom(position=(0.250 * alat, 0.250 * alat, 0.250 * alat), symbols=['Si'])
        self.structure = structure
        # Define the expected reciprocal cell
        val = 2.0 * np.pi / alat
        self.expected_reciprocal_cell = np.array([[val, val, -val], [-val, val, val], [val, -val, val]])

    def test_reciprocal_cell(self):
        """Test the `reciprocal_cell` method.

        This is a regression test for #2749.
        """
        kpt = KpointsData()
        kpt.set_cell_from_structure(self.structure)

        assert np.abs(kpt.reciprocal_cell - self.expected_reciprocal_cell).sum() == 0.0

        # Check also after storing
        kpt.store()
        kpt2 = load_node(kpt.pk)
        assert np.abs(kpt2.reciprocal_cell - self.expected_reciprocal_cell).sum() == 0.0

    def test_get_kpoints(self):
        """Test the `get_kpoints` method."""
        kpt = KpointsData()
        kpt.set_cell_from_structure(self.structure)

        kpoints = [
            [0.0, 0.0, 0.0],
            [0.5, 0.5, 0.5],
        ]

        cartesian_kpoints = [
            [0.0, 0.0, 0.0],
            [np.pi / self.alat, np.pi / self.alat, np.pi / self.alat],
        ]

        kpt.set_kpoints(kpoints)
        assert np.abs(kpt.get_kpoints() - np.array(kpoints)).sum() == 0.0
        assert np.abs(kpt.get_kpoints(cartesian=True) - np.array(cartesian_kpoints)).sum() == 0.0

        # Check also after storing
        kpt.store()
        kpt2 = load_node(kpt.pk)
        assert np.abs(kpt2.get_kpoints() - np.array(kpoints)).sum() == 0.0
        assert np.abs(kpt2.get_kpoints(cartesian=True) - np.array(cartesian_kpoints)).sum() == 0.0

@skip_atomistic
class TestKpointsAtomisticStructureData:
    """Test for the `Kpointsdata` class using the new atomistic StructureData."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        
        from aiida_atomistic import StructureDataMutable
        from aiida_atomistic import StructureData as AtomisticStructureData
        
        alat = 5.430  # angstrom
        cell = [
            [
                0.5 * alat,
                0.5 * alat,
                0.0,
            ],
            [
                0.0,
                0.5 * alat,
                0.5 * alat,
            ],
            [0.5 * alat, 0.0, 0.5 * alat],
        ]
        self.alat = alat
        mutable = StructureDataMutable()
        mutable.set_cell(cell)
        mutable.add_atom(positions=(0.000 * alat, 0.000 * alat, 0.000 * alat), symbols='Si')
        mutable.add_atom(positions=(0.250 * alat, 0.250 * alat, 0.250 * alat), symbols='Si')
        self.structure = AtomisticStructureData.from_mutable(mutable)
        # Define the expected reciprocal cell
        val = 2.0 * np.pi / alat
        self.expected_reciprocal_cell = np.array([[val, val, -val], [-val, val, val], [val, -val, val]])

    def test_reciprocal_cell(self):
        """Test the `reciprocal_cell` method.

        This is a regression test for #2749.
        """
        kpt = KpointsData()
        kpt.set_cell_from_structure(self.structure)

        assert np.abs(kpt.reciprocal_cell - self.expected_reciprocal_cell).sum() == 0.0

        # Check also after storing
        kpt.store()
        kpt2 = load_node(kpt.pk)
        assert np.abs(kpt2.reciprocal_cell - self.expected_reciprocal_cell).sum() == 0.0

    def test_get_kpoints(self):
        """Test the `get_kpoints` method."""
        kpt = KpointsData()
        kpt.set_cell_from_structure(self.structure)

        kpoints = [
            [0.0, 0.0, 0.0],
            [0.5, 0.5, 0.5],
        ]

        cartesian_kpoints = [
            [0.0, 0.0, 0.0],
            [np.pi / self.alat, np.pi / self.alat, np.pi / self.alat],
        ]

        kpt.set_kpoints(kpoints)
        assert np.abs(kpt.get_kpoints() - np.array(kpoints)).sum() == 0.0
        assert np.abs(kpt.get_kpoints(cartesian=True) - np.array(cartesian_kpoints)).sum() == 0.0

        # Check also after storing
        kpt.store()
        kpt2 = load_node(kpt.pk)
        assert np.abs(kpt2.get_kpoints() - np.array(kpoints)).sum() == 0.0
        assert np.abs(kpt2.get_kpoints(cartesian=True) - np.array(cartesian_kpoints)).sum() == 0.0