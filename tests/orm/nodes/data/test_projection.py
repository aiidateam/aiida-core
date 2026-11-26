###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `ProjectionData` class."""

import numpy as np
import pytest

from aiida.common import exceptions
from aiida.orm import BandsData, KpointsData, ProjectionData
from aiida.plugins import OrbitalFactory


class TestProjectionData:
    """Test for the `ProjectionData` class."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize test fixtures."""
        self.real_hydrogen_dict = {
            'angular_momentum': -3,
            'diffusivity': None,
            'kind_name': 'As',
            'magnetic_number': 0,
            'position': [-1.42, 1.42, 1.42],
            'radial_nodes': 0,
            'spin': 0,
            'spin_orientation': None,
            'x_orientation': None,
            'z_orientation': None,
        }
        RealHydrogen = OrbitalFactory('core.realhydrogen')  # noqa: N806
        self.orbital = RealHydrogen(**self.real_hydrogen_dict)

    def create_bands_data(self, bands_array=None):
        """Create and store a BandsData instance for testing."""
        if bands_array is None:
            bands_array = np.array([[-5.64, 1.23]])
        kpoints = KpointsData()
        kpoints.set_cell([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        kpoints.set_kpoints([[0.0, 0.0, 0.0]])
        bands_data = BandsData()
        bands_data.set_kpointsdata(kpoints)
        bands_data.set_bands(bands_array, units='eV')
        bands_data.store()
        return bands_data

    def test_projections_with_matching_bands(self):
        """Test setting projections matching the reference bands shape with bands_check=True."""
        bands_array = np.array([[-5.64, 1.23]])
        bands_data = self.create_bands_data(bands_array)

        projection_data = ProjectionData()
        projection_data.set_reference_bandsdata(bands_data)

        # Projections with same shape as bands (1 kpoint, 2 bands)
        proj_array = np.array([[0.8, 0.2]])
        projection_data.set_projectiondata(
            list_of_orbitals=self.orbital,
            list_of_projections=[proj_array],
            bands_check=True,
        )

        projections = projection_data.get_projections()
        assert len(projections) == 1
        np.testing.assert_allclose(projections[0][1], proj_array)

    def test_projections_with_mismatching_bands_raises(self):
        """Test setting projections with mismatching bands shape raises AttributeError."""
        bands_array = np.array([[-5.64, 1.23]])
        bands_data = self.create_bands_data(bands_array)

        projection_data = ProjectionData()
        projection_data.set_reference_bandsdata(bands_data)

        # Projections with shape (1, 3) != bands shape (1, 2)
        proj_array = np.array([[0.8, 0.2, 0.1]])
        with pytest.raises(AttributeError, match='These arrays are not the same shape as the bands'):
            projection_data.set_projectiondata(
                list_of_orbitals=self.orbital,
                list_of_projections=[proj_array],
                bands_check=True,
            )

    def test_projections_without_bands_raises(self):
        """Test setting projections when reference bandsdata is not set raises ValidationError."""
        projection_data = ProjectionData()
        proj_array = np.array([[0.8, 0.2]])

        with pytest.raises(exceptions.ValidationError, match='Bands must be set first, then projwfc'):
            projection_data.set_projectiondata(
                list_of_orbitals=self.orbital,
                list_of_projections=[proj_array],
                bands_check=True,
            )

    def test_projections_with_unstored_bands_raises(self):
        """Test setting projections when reference bandsdata is unstored raises ValidationError."""
        bands_data = BandsData()
        bands_data.set_kpoints([[0.0, 0.0, 0.0]])
        bands_data.set_bands(np.array([[1.0, 2.0]]))
        projection_data = ProjectionData()
        projection_data.set_reference_bandsdata(bands_data)

        proj_array = np.array([[0.8, 0.2]])
        with pytest.raises(exceptions.ValidationError, match='Bands must be set first, then projwfc'):
            projection_data.set_projectiondata(
                list_of_orbitals=self.orbital,
                list_of_projections=[proj_array],
                bands_check=True,
            )

    def test_pdos_without_projections_bands_check_true(self):
        """Test setting pdos and energy with default bands_check=True does not raise UnboundLocalError (#6065)."""
        energy_array = np.array([0.0, 1.0, 2.0])
        pdos_array = np.array([0.1, 0.5, 0.2])

        projection_data = ProjectionData()
        # Should succeed without UnboundLocalError even when list_of_projections is None
        projection_data.set_projectiondata(
            list_of_orbitals=self.orbital,
            list_of_energy=energy_array,
            list_of_pdos=pdos_array,
            bands_check=True,
        )

        pdos_list = projection_data.get_pdos()
        assert len(pdos_list) == 1
        orb, pdos_out, energy_out = pdos_list[0]
        assert orb.get_orbital_dict() == self.orbital.get_orbital_dict()
        np.testing.assert_allclose(pdos_out, pdos_array)
        np.testing.assert_allclose(energy_out, energy_array)

    def test_both_projections_and_pdos(self):
        """Test setting both projections and pdos with bands_check=True."""
        bands_data = self.create_bands_data(np.array([[1.0, 2.0]]))

        projection_data = ProjectionData()
        projection_data.set_reference_bandsdata(bands_data)

        proj_array = np.array([[0.5, 0.5]])
        energy_array = np.array([1.0, 2.0])
        pdos_array = np.array([0.3, 0.7])

        projection_data.set_projectiondata(
            list_of_orbitals=self.orbital,
            list_of_projections=[proj_array],
            list_of_energy=[energy_array],
            list_of_pdos=[pdos_array],
            bands_check=True,
        )

        projections = projection_data.get_projections()
        assert len(projections) == 1
        np.testing.assert_allclose(projections[0][1], proj_array)

        pdos_list = projection_data.get_pdos()
        assert len(pdos_list) == 1
        np.testing.assert_allclose(pdos_list[0][1], pdos_array)
        np.testing.assert_allclose(pdos_list[0][2], energy_array)

    def test_bands_check_false(self):
        """Test setting projections with bands_check=False skips bands shape verification."""
        projection_data = ProjectionData()
        proj_array = np.array([[1.0, 2.0, 3.0]])

        # Skips bands check completely (no reference bandsdata needed)
        projection_data.set_projectiondata(
            list_of_orbitals=self.orbital,
            list_of_projections=[proj_array],
            bands_check=False,
        )
        projections = projection_data.get_projections()
        assert len(projections) == 1
        np.testing.assert_allclose(projections[0][1], proj_array)

    def test_set_orbitals_raises_not_implemented(self):
        """Test that set_orbitals is blocked on ProjectionData."""
        projection_data = ProjectionData()
        with pytest.raises(NotImplementedError):
            projection_data.set_orbitals()

    def test_validation_missing_both_projections_and_pdos(self):
        """Test that ValidationError is raised if neither pdos nor projections is provided."""
        projection_data = ProjectionData()
        with pytest.raises(exceptions.ValidationError, match='Must set either pdos or projections'):
            projection_data.set_projectiondata(list_of_orbitals=self.orbital)

    def test_validation_pdos_without_energy(self):
        """Test that ValidationError is raised if pdos is provided without energy."""
        projection_data = ProjectionData()
        with pytest.raises(
            exceptions.ValidationError, match='list_of_pdos and list_of_energy must always be set together'
        ):
            projection_data.set_projectiondata(
                list_of_orbitals=self.orbital,
                list_of_pdos=np.array([1.0]),
            )

    def test_get_reference_bandsdata(self):
        """Test get_reference_bandsdata when set and when not set."""
        projection_data = ProjectionData()
        with pytest.raises(AttributeError, match='BandsData has not been set for this instance'):
            projection_data.get_reference_bandsdata()

        bands_data = self.create_bands_data()
        projection_data.set_reference_bandsdata(bands_data)
        ref_bands = projection_data.get_reference_bandsdata()
        assert ref_bands.uuid == bands_data.uuid
