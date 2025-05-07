###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Test for the `Orbital` class and subclasses."""

import pytest

from aiida.common.exceptions import ValidationError
from aiida.plugins import OrbitalFactory
from aiida.tools.data.orbital import Orbital


class TestOrbital:
    """Test the Orbital base class"""

    def test_orbital_str(self):
        """ "Test the output of __str__ method"""
        orbital = Orbital(position=(1, 2, 3))
        expected_output = 'Orbital @ 1.0000,2.0000,3.0000'

        assert str(orbital) == expected_output

    def test_required_fields(self):
        """Verify that required fields are validated."""
        # position is required
        with pytest.raises(ValidationError):
            Orbital()

        # position must be a list of three floats
        with pytest.raises(ValidationError):
            Orbital(position=(1, 2))
        with pytest.raises(ValidationError):
            Orbital(position=(1, 2, 'a'))

        orbital = Orbital(position=(1, 2, 3))
        assert round(abs(orbital.get_orbital_dict()['position'][0] - 1.0), 7) == 0
        assert round(abs(orbital.get_orbital_dict()['position'][1] - 2.0), 7) == 0
        assert round(abs(orbital.get_orbital_dict()['position'][2] - 3.0), 7) == 0

    def test_unknown_fields(self):
        """Verify that unkwown fields raise a validation error."""
        # position is required
        # position must be a list of three floats
        with pytest.raises(ValidationError, match='some_strange_key'):
            Orbital(position=(1, 2, 3), some_strange_key=1)


class TestRealhydrogenOrbital:
    """Test the Orbital base class"""

    def test_required_fields(self):
        """Verify that required fields are validated."""
        RealhydrogenOrbital = OrbitalFactory('core.realhydrogen')
        # Check that the required fields of the base class are not enough
        with pytest.raises(ValidationError):
            RealhydrogenOrbital(position=(1, 2, 3))

        orbital = RealhydrogenOrbital(
            **{'position': (-1, -2, -3), 'angular_momentum': 1, 'magnetic_number': 0, 'radial_nodes': 2}
        )
        assert round(abs(orbital.get_orbital_dict()['position'][0] - -1.0), 7) == 0
        assert round(abs(orbital.get_orbital_dict()['position'][1] - -2.0), 7) == 0
        assert round(abs(orbital.get_orbital_dict()['position'][2] - -3.0), 7) == 0
        assert round(abs(orbital.get_orbital_dict()['angular_momentum'] - 1), 7) == 0
        assert round(abs(orbital.get_orbital_dict()['magnetic_number'] - 0), 7) == 0
        assert round(abs(orbital.get_orbital_dict()['radial_nodes'] - 2), 7) == 0

    def test_validation_for_fields(self):
        """Verify that the values are properly validated"""
        RealhydrogenOrbital = OrbitalFactory('core.realhydrogen')

        with pytest.raises(ValidationError, match='angular_momentum'):
            RealhydrogenOrbital(
                **{'position': (-1, -2, -3), 'angular_momentum': 100, 'magnetic_number': 0, 'radial_nodes': 2}
            )

        with pytest.raises(ValidationError, match='magnetic number must be in the range'):
            RealhydrogenOrbital(
                **{'position': (-1, -2, -3), 'angular_momentum': 1, 'magnetic_number': 3, 'radial_nodes': 2}
            )

        with pytest.raises(ValidationError, match='radial_nodes'):
            RealhydrogenOrbital(
                **{'position': (-1, -2, -3), 'angular_momentum': 1, 'magnetic_number': 0, 'radial_nodes': 100}
            )

    def test_optional_fields(self):
        """Testing (some of) the optional parameters to check that the functionality works
        (they are indeed optional but accepted if specified, they are validated, ...)
        """
        RealhydrogenOrbital = OrbitalFactory('core.realhydrogen')

        orbital = RealhydrogenOrbital(
            **{'position': (-1, -2, -3), 'angular_momentum': 1, 'magnetic_number': 0, 'radial_nodes': 2}
        )
        # Check that the optional value is there and has its default value
        assert orbital.get_orbital_dict()['spin'] == 0
        assert orbital.get_orbital_dict()['diffusivity'] is None

        orbital = RealhydrogenOrbital(
            **{
                'position': (-1, -2, -3),
                'angular_momentum': 1,
                'magnetic_number': 0,
                'radial_nodes': 2,
                'spin': 1,
                'diffusivity': 3.1,
            }
        )
        assert orbital.get_orbital_dict()['spin'] == 1
        assert orbital.get_orbital_dict()['diffusivity'] == 3.1

        with pytest.raises(ValidationError, match='diffusivity'):
            RealhydrogenOrbital(
                **{
                    'position': (-1, -2, -3),
                    'angular_momentum': 1,
                    'magnetic_number': 0,
                    'radial_nodes': 2,
                    'spin': 1,
                    'diffusivity': 'a',
                }
            )

        with pytest.raises(ValidationError, match='spin'):
            RealhydrogenOrbital(
                **{
                    'position': (-1, -2, -3),
                    'angular_momentum': 1,
                    'magnetic_number': 0,
                    'radial_nodes': 2,
                    'spin': 5,
                    'diffusivity': 3.1,
                }
            )

    def test_unknown_fields(self):
        """Verify that unkwown fields raise a validation error."""
        RealhydrogenOrbital = OrbitalFactory('core.realhydrogen')

        with pytest.raises(ValidationError, match='some_strange_key'):
            RealhydrogenOrbital(
                **{
                    'position': (-1, -2, -3),
                    'angular_momentum': 1,
                    'magnetic_number': 0,
                    'radial_nodes': 2,
                    'some_strange_key': 1,
                }
            )

    def test_get_name_from_quantum_numbers(self):
        """Test if the function ``get_name_from_quantum_numbers`` works as expected"""
        RealhydrogenOrbital = OrbitalFactory('core.realhydrogen')

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=1)
        assert name == 'P'

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=0)
        assert name == 'S'

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=0, magnetic_number=0)
        assert name == 'S'

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=1, magnetic_number=1)
        assert name == 'PX'

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=2, magnetic_number=4)
        assert name == 'DXY'
