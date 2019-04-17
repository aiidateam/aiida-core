# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the `Orbital` class and subclasses."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

#from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import ValidationError
from aiida.tools.data.orbital import Orbital

from aiida.plugins import OrbitalFactory


class TestOrbital(AiidaTestCase):
    """Test the Orbital base class"""

    def test_required_fields(self):
        """Verify that required fields are validated."""
        # position is required
        with self.assertRaises(ValidationError):
            Orbital()

        # position must be a list of three floats
        with self.assertRaises(ValidationError):
            Orbital(position=(1, 2))
        with self.assertRaises(ValidationError):
            Orbital(position=(1, 2, 'a'))

        orbital = Orbital(position=(1, 2, 3))
        self.assertAlmostEqual(orbital.get_orbital_dict()['position'][0], 1.)
        self.assertAlmostEqual(orbital.get_orbital_dict()['position'][1], 2.)
        self.assertAlmostEqual(orbital.get_orbital_dict()['position'][2], 3.)

    def test_unknown_fields(self):
        """Verify that unkwown fields raise a validation error."""
        # position is required
        # position must be a list of three floats
        with self.assertRaises(ValidationError) as exc:
            Orbital(position=(1, 2, 3), some_strange_key=1)
        self.assertIn("some_strange_key", str(exc.exception))


class TestRealhydrogenOrbital(AiidaTestCase):
    """Test the Orbital base class"""

    def test_required_fields(self):
        """Verify that required fields are validated."""
        RealhydrogenOrbital = OrbitalFactory('realhydrogen')  # pylint: disable=invalid-name
        # Check that the required fields of the base class are not enough
        with self.assertRaises(ValidationError):
            RealhydrogenOrbital(position=(1, 2, 3))

        orbital = RealhydrogenOrbital(**{
            'position': (-1, -2, -3),
            'angular_momentum': 1,
            'magnetic_number': 0,
            'radial_nodes': 2
        })
        self.assertAlmostEqual(orbital.get_orbital_dict()['position'][0], -1.)
        self.assertAlmostEqual(orbital.get_orbital_dict()['position'][1], -2.)
        self.assertAlmostEqual(orbital.get_orbital_dict()['position'][2], -3.)
        self.assertAlmostEqual(orbital.get_orbital_dict()['angular_momentum'], 1)
        self.assertAlmostEqual(orbital.get_orbital_dict()['magnetic_number'], 0)
        self.assertAlmostEqual(orbital.get_orbital_dict()['radial_nodes'], 2)

    def test_validation_for_fields(self):
        """Verify that the values are properly validated"""
        RealhydrogenOrbital = OrbitalFactory('realhydrogen')  # pylint: disable=invalid-name

        with self.assertRaises(ValidationError) as exc:
            RealhydrogenOrbital(**{
                'position': (-1, -2, -3),
                'angular_momentum': 100,
                'magnetic_number': 0,
                'radial_nodes': 2
            })
        self.assertIn("angular_momentum", str(exc.exception))

        with self.assertRaises(ValidationError) as exc:
            RealhydrogenOrbital(**{
                'position': (-1, -2, -3),
                'angular_momentum': 1,
                'magnetic_number': 3,
                'radial_nodes': 2
            })
        self.assertIn("magnetic number must be in the range", str(exc.exception))

        with self.assertRaises(ValidationError) as exc:
            RealhydrogenOrbital(**{
                'position': (-1, -2, -3),
                'angular_momentum': 1,
                'magnetic_number': 0,
                'radial_nodes': 100
            })
        self.assertIn("radial_nodes", str(exc.exception))

    def test_optional_fields(self):
        """
        Testing (some of) the optional parameters to check that the functionality works
        (they are indeed optional but accepted if specified, they are validated, ...)
        """
        RealhydrogenOrbital = OrbitalFactory('realhydrogen')  # pylint: disable=invalid-name

        orbital = RealhydrogenOrbital(**{
            'position': (-1, -2, -3),
            'angular_momentum': 1,
            'magnetic_number': 0,
            'radial_nodes': 2
        })
        # Check that the optional value is there and has its default value
        self.assertEqual(orbital.get_orbital_dict()['spin'], 0)
        self.assertEqual(orbital.get_orbital_dict()['diffusivity'], None)

        orbital = RealhydrogenOrbital(
            **{
                'position': (-1, -2, -3),
                'angular_momentum': 1,
                'magnetic_number': 0,
                'radial_nodes': 2,
                'spin': 1,
                'diffusivity': 3.1
            })
        self.assertEqual(orbital.get_orbital_dict()['spin'], 1)
        self.assertEqual(orbital.get_orbital_dict()['diffusivity'], 3.1)

        with self.assertRaises(ValidationError) as exc:
            RealhydrogenOrbital(
                **{
                    'position': (-1, -2, -3),
                    'angular_momentum': 1,
                    'magnetic_number': 0,
                    'radial_nodes': 2,
                    'spin': 1,
                    'diffusivity': "a"
                })
        self.assertIn("diffusivity", str(exc.exception))

        with self.assertRaises(ValidationError) as exc:
            RealhydrogenOrbital(
                **{
                    'position': (-1, -2, -3),
                    'angular_momentum': 1,
                    'magnetic_number': 0,
                    'radial_nodes': 2,
                    'spin': 5,
                    'diffusivity': 3.1
                })
        self.assertIn("spin", str(exc.exception))

    def test_unknown_fields(self):
        """Verify that unkwown fields raise a validation error."""
        RealhydrogenOrbital = OrbitalFactory('realhydrogen')  # pylint: disable=invalid-name

        with self.assertRaises(ValidationError) as exc:
            RealhydrogenOrbital(
                **{
                    'position': (-1, -2, -3),
                    'angular_momentum': 1,
                    'magnetic_number': 0,
                    'radial_nodes': 2,
                    'some_strange_key': 1
                })
        self.assertIn("some_strange_key", str(exc.exception))

    def test_get_name_from_quantum_numbers(self):
        """
        Test if the function ``get_name_from_quantum_numbers`` works as expected
        """
        RealhydrogenOrbital = OrbitalFactory('realhydrogen')  # pylint: disable=invalid-name

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=1)
        self.assertEqual(name, 'P')

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=0)
        self.assertEqual(name, 'S')

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=0, magnetic_number=0)
        self.assertEqual(name, 'S')

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=1, magnetic_number=1)
        self.assertEqual(name, 'PX')

        name = RealhydrogenOrbital.get_name_from_quantum_numbers(angular_momentum=2, magnetic_number=4)
        self.assertEqual(name, 'DXY')
