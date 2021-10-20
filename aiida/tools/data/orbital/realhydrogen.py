# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
A module defining hydrogen-like orbitals that are real valued (rather than
complex-valued).
"""
from aiida.common.exceptions import ValidationError

from .orbital import Orbital, validate_float_or_none, validate_len3_list_or_none

__all__ = ('RealhydrogenOrbital',)


def validate_l(value):
    """
    Validate the value of the angular momentum
    """
    if not isinstance(value, int):
        raise ValidationError('angular momentum (l) must be integer')

    if value < -5 or value > 3:
        raise ValidationError('angular momentum (l) must be between -5 and 3')

    return value


def validate_m(value):
    """
    Validate the value of the magnetic number
    """
    if not isinstance(value, int):
        raise ValidationError('magnetic number (m) must be integer')

    # without knowing l we cannot validate the value of m. We will call an additional function
    # in the validate function

    return value


def validate_kind_name(value):
    """
    Validate the value of the kind_name
    """
    if value is not None and not isinstance(value, str):
        raise ValidationError('kind_name must be a string')

    return value


def validate_n(value):
    """
    Validate the value of the number of radial nodes
    """
    if not isinstance(value, int):
        raise ValidationError('number of radial nodes (n) must be integer')

    if value < 0 or value > 2:
        raise ValidationError('number of radial nodes (n) must be between 0 and 2')

    return value


def validate_spin(value):
    """
    Validate the value of the spin
    """
    if not isinstance(value, int):
        raise ValidationError('spin must be integer')

    if value < -1 or value > 1:
        raise ValidationError('spin must be among -1, 1 or 0 (undefined)')

    return value


CONVERSION_DICT = {
    'S': {
        'S': {
            'angular_momentum': 0,
            'magnetic_number': 0
        }
    },
    'P': {
        'PZ': {
            'angular_momentum': 1,
            'magnetic_number': 0
        },
        'PX': {
            'angular_momentum': 1,
            'magnetic_number': 1
        },
        'PY': {
            'angular_momentum': 1,
            'magnetic_number': 2
        },
    },
    'D': {
        'DZ2': {
            'angular_momentum': 2,
            'magnetic_number': 0
        },
        'DXZ': {
            'angular_momentum': 2,
            'magnetic_number': 1
        },
        'DYZ': {
            'angular_momentum': 2,
            'magnetic_number': 2
        },
        'DX2-Y2': {
            'angular_momentum': 2,
            'magnetic_number': 3
        },
        'DXY': {
            'angular_momentum': 2,
            'magnetic_number': 4
        },
    },
    'F': {
        'FZ3': {
            'angular_momentum': 3,
            'magnetic_number': 0
        },
        'FZX2': {
            'angular_momentum': 3,
            'magnetic_number': 1
        },
        'FYZ2': {
            'angular_momentum': 3,
            'magnetic_number': 2
        },
        'FZ(X2-Y2)': {
            'angular_momentum': 3,
            'magnetic_number': 3
        },
        'FXYZ': {
            'angular_momentum': 3,
            'magnetic_number': 4
        },
        'FX(X2-3Y2)': {
            'angular_momentum': 3,
            'magnetic_number': 5
        },
        'FY(3X2-Y2)': {
            'angular_momentum': 3,
            'magnetic_number': 6
        },
    },
    'SP': {
        'SP-1': {
            'angular_momentum': -1,
            'magnetic_number': 0
        },
        'SP-2': {
            'angular_momentum': -1,
            'magnetic_number': 1
        },
    },
    'SP2': {
        'SP2-1': {
            'angular_momentum': -2,
            'magnetic_number': 0
        },
        'SP2-2': {
            'angular_momentum': -2,
            'magnetic_number': 1
        },
        'SP2-3': {
            'angular_momentum': -2,
            'magnetic_number': 2
        },
    },
    'SP3': {
        'SP3-1': {
            'angular_momentum': -3,
            'magnetic_number': 0
        },
        'SP3-2': {
            'angular_momentum': -3,
            'magnetic_number': 1
        },
        'SP3-3': {
            'angular_momentum': -3,
            'magnetic_number': 2
        },
        'SP3-4': {
            'angular_momentum': -3,
            'magnetic_number': 3
        },
    },
    'SP3D': {
        'SP3D-1': {
            'angular_momentum': -4,
            'magnetic_number': 0
        },
        'SP3D-2': {
            'angular_momentum': -4,
            'magnetic_number': 1
        },
        'SP3D-3': {
            'angular_momentum': -4,
            'magnetic_number': 2
        },
        'SP3D-4': {
            'angular_momentum': -4,
            'magnetic_number': 3
        },
        'SP3D-5': {
            'angular_momentum': -4,
            'magnetic_number': 4
        },
    },
    'SP3D2': {
        'SP3D2-1': {
            'angular_momentum': -5,
            'magnetic_number': 0
        },
        'SP3D2-2': {
            'angular_momentum': -5,
            'magnetic_number': 1
        },
        'SP3D2-3': {
            'angular_momentum': -5,
            'magnetic_number': 2
        },
        'SP3D2-4': {
            'angular_momentum': -5,
            'magnetic_number': 3
        },
        'SP3D2-5': {
            'angular_momentum': -5,
            'magnetic_number': 4
        },
        'SP3D2-6': {
            'angular_momentum': -5,
            'magnetic_number': 5
        },
    }
}


class RealhydrogenOrbital(Orbital):
    """
    Orbitals for hydrogen, largely follows the conventions used by wannier90
    Object to handle the generation of real hydrogen orbitals and their
    hybrids, has methods for producing s, p, d, f, and sp, sp2, sp3, sp3d,
    sp3d2 hybrids. This method does not deal with the cannonical hydrogen
    orbitals which contain imaginary components.

    The orbitals described here are chiefly concerned with the symmetric
    aspects of the oribitals without the context of space. Therefore
    diffusitivity, position and atomic labels should be handled in the
    OrbitalData class.

    Following the notation of table 3.1, 3.2 of Wannier90 user guide
    (which can be downloaded from http://www.wannier.org/support/)
    A brief description of what is meant by each of these labels:

    :param radial_nodes: the number of radial nodes (or inflections) if no
                         radial nodes are supplied, defaults to 0
    :param angular_momentum: Angular quantum number, using real orbitals
    :param magnetic_number: Magnetic quantum number, using real orbitals
    :param spin: spin, up (1) down (-1) or unspecified (0)

    The conventions regarding L and M correpsond to those used in
    wannier90 for all L greater than 0 the orbital is not hyrbridized
    see table 3.1 and for L less than 0 the orbital is hybridized see
    table 3.2. M then indexes all the possible orbitals from 0 to 2L for
    L > 0 and from 0 to (-L) for L < 0.
    """
    _base_fields_required = tuple(
        list(Orbital._base_fields_required) +
        [('angular_momentum', validate_l), ('magnetic_number', validate_m), ('radial_nodes', validate_n)]
    )

    _base_fields_optional = tuple(
        list(Orbital._base_fields_optional) + [
            ('kind_name', validate_kind_name, None),
            ('spin', validate_spin, 0),
            ('x_orientation', validate_len3_list_or_none, None),
            ('z_orientation', validate_len3_list_or_none, None),
            ('spin_orientation', validate_len3_list_or_none, None),
            ('diffusivity', validate_float_or_none, None),
        ]
    )

    def __str__(self):
        orb_dict = self.get_orbital_dict()
        try:
            orb_name = self.get_name_from_quantum_numbers(
                orb_dict['angular_momentum'], magnetic_number=orb_dict['magnetic_number']
            )
            position_string = '{:.4f},{:.4f},{:.4f}'.format(
                orb_dict['position'][0], orb_dict['position'][1], orb_dict['position'][2]
            )
            out_string = 'r{} {} orbital {} @ {}'.format(
                orb_dict['radial_nodes'], orb_name,
                "for kind '{}'".format(orb_dict['kind_name']) if orb_dict['kind_name'] else '', position_string
            )
        except KeyError:
            # Should not happen, but we want it not to crash in __str__
            out_string = '(not all parameters properly set)'
        return out_string

    def _validate_keys(self, input_dict):
        """
        Validates the keys otherwise raise ValidationError. Does basic
        validation from the parent followed by validations for the
        quantum numbers. Raises exceptions should the input_dict fail the
        valiation or if it contains any unsupported keywords.

        :param input_dict: the dictionary of keys to be validated
        :return validated_dict: a validated dictionary
        """
        validated_dict = super()._validate_keys(input_dict)

        # Validate m knowing the value of l
        angular_momentum = validated_dict['angular_momentum']  # l quantum number, must be there
        magnetic_number = validated_dict['magnetic_number']  # m quantum number, must be there
        if angular_momentum >= 0:
            accepted_range = [0, 2 * angular_momentum]
        else:
            accepted_range = [0, -angular_momentum]
        if magnetic_number < min(accepted_range) or magnetic_number > max(accepted_range):
            raise ValidationError(
                f'the magnetic number must be in the range [{min(accepted_range)}, {max(accepted_range)}]'
            )

        # Check if it is a known combination
        try:
            self.get_name_from_quantum_numbers(
                validated_dict['angular_momentum'], magnetic_number=validated_dict['magnetic_number']
            )
        except ValidationError:
            raise ValidationError('Invalid angular momentum magnetic number combination')

        return validated_dict

    @classmethod
    def get_name_from_quantum_numbers(cls, angular_momentum, magnetic_number=None):
        """
        Returns the orbital_name correponding to the angular_momentum alone,
        or to both angular_number with magnetic_number. For example using
        angular_momentum=1 and magnetic_number=1 will return "Px"
        """
        orbital_name = [
            orbital for orbital, data in CONVERSION_DICT.items()
            if any(values['angular_momentum'] == angular_momentum for values in data.values())
        ]
        if not orbital_name:
            raise ValueError(f'No orbital name corresponding to the angular_momentum {angular_momentum} could be found')
        if magnetic_number is not None:
            # finds angular momentum
            orbital_name = orbital_name[0]
            orbital_name = [
                x for x in CONVERSION_DICT[orbital_name]
                if CONVERSION_DICT[orbital_name][x]['magnetic_number'] == magnetic_number
            ]

            if not orbital_name:
                raise ValueError(
                    f'No orbital name corresponding to the magnetic_number {magnetic_number} could be found'
                )
        return orbital_name[0]

    @classmethod
    def get_quantum_numbers_from_name(cls, name):
        """
        Returns all the angular and magnetic numbers corresponding to name.
        For example, using "P" as name will return all quantum numbers
        associated with a "P" orbital, while "Px" will return only one set
        of quantum numbers, the ones associated with "Px"
        """
        name = name.upper()
        list_of_dicts = [
            subdata for orbital, data in CONVERSION_DICT.items() for suborbital, subdata in data.items()
            if name in (suborbital, orbital)
        ]
        if not list_of_dicts:
            raise ValueError('Invalid choice of projection name')
        return list_of_dicts


# # Can move these later, but for now I want to have these functions handy
# def cart2sph(x, y, z):
#     """
#     Converts cartesian to unit vector spherical coordinates
#
#     :param x, y, z: absolute cartesian coordinates
#     :return: [r, theta, phi] unit vector in spherical coordinates
#     """
#     import numpy as np
#     coord_cart = np.array([x, y, z])
#     unit_cart = coord_cart/np.linalg.norm(coord_cart)
#     x,y,z = unit_cart # for clarity
#     r = np.linalg.norm(unit_cart)  # should always be 1.0
#     theta = np.arctan2(y,x)
#     phi = np.arctan2(z,r)
#     # note that this method will not return the r value, which is not stored
#     return [theta, phi]

# def sph2cart(theta, phi):
#     """
#     Converts spherical coordinates r, theta, phi to unit vector in cartesian
#     coordinates. r is not accepted as input because only unit vectors are
#     considered here.
#
#     : theta, phi: spherical coordinates vector
#     :return: x, y, z unit vector  in cartesian absolute coordinates
#     """
#     import numpy as np
#     # code is done in a few more steps than necessary, to make logic explicit
#     r = 1
#     x = r*np.cos(theta)*np.sin(phi)
#     y = r*np.sin(theta)*np.sin(phi)
#     z = r*np.cos(theta)
#     x = x/r
#     y = y/r
#     z = z/r
#     return [x, y, z]
