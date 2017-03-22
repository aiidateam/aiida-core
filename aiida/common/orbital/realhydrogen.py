# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.common.orbital import Orbital
from aiida.common.exceptions import ValidationError, InputValidationError
import copy


conversion_dict = {  'S':{'S':{'angular_momentum': 0, 'magnetic_number':0}
                              },
                    'P':{'PZ':{'angular_momentum': 1, 'magnetic_number':0},
                         'PX':{'angular_momentum': 1, 'magnetic_number':1},
                         'PY':{'angular_momentum': 1, 'magnetic_number':2},
                              },
                   'D':{'DZ2':{'angular_momentum': 2, 'magnetic_number':0},
                        'DXZ':{'angular_momentum': 2, 'magnetic_number':1},
                        'DYZ':{'angular_momentum': 2, 'magnetic_number':2},
                     'DX2-Y2':{'angular_momentum': 2, 'magnetic_number':3},
                        'DXY':{'angular_momentum': 2, 'magnetic_number':4},
                              },
                   'F':{'FZ3':{'angular_momentum': 3, 'magnetic_number':0},
                       'FZX2':{'angular_momentum': 3, 'magnetic_number':1},
                       'FYZ2':{'angular_momentum': 3, 'magnetic_number':2},
                  'FZ(X2-Y2)':{'angular_momentum': 3, 'magnetic_number':3},
                       'FXYZ':{'angular_momentum': 3, 'magnetic_number':4},
                 'FX(X2-3Y2)':{'angular_momentum': 3, 'magnetic_number':5},
                 'FY(3X2-Y2)':{'angular_momentum': 3, 'magnetic_number':6},
                              },
                 'SP':{'SP-1':{'angular_momentum':-1, 'magnetic_number':0},
                       'SP-2':{'angular_momentum':-1, 'magnetic_number':1},
                              },
               'SP2':{'SP2-1':{'angular_momentum':-2, 'magnetic_number':0},
                      'SP2-2':{'angular_momentum':-2, 'magnetic_number':1},
                      'SP2-3':{'angular_momentum':-2, 'magnetic_number':2},
                              },
               'SP3':{'SP3-1':{'angular_momentum':-3, 'magnetic_number':0},
                      'SP3-2':{'angular_momentum':-3, 'magnetic_number':1},
                      'SP3-3':{'angular_momentum':-3, 'magnetic_number':2},
                      'SP3-4':{'angular_momentum':-3, 'magnetic_number':3},
                              },
             'SP3D':{'SP3D-1':{'angular_momentum':-4, 'magnetic_number':0},
                     'SP3D-2':{'angular_momentum':-4, 'magnetic_number':1},
                     'SP3D-3':{'angular_momentum':-4, 'magnetic_number':2},
                     'SP3D-4':{'angular_momentum':-4, 'magnetic_number':3},
                     'SP3D-5':{'angular_momentum':-4, 'magnetic_number':4},
                              },
           'SP3D2':{'SP3D2-1':{'angular_momentum':-5, 'magnetic_number':0},
                    'SP3D2-2':{'angular_momentum':-5, 'magnetic_number':1},
                    'SP3D2-3':{'angular_momentum':-5, 'magnetic_number':2},
                    'SP3D2-4':{'angular_momentum':-5, 'magnetic_number':3},
                    'SP3D2-5':{'angular_momentum':-5, 'magnetic_number':4},
                    'SP3D2-6':{'angular_momentum':-5, 'magnetic_number':5},
                      }}

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
    http://www.wannier.org/doc/user_guide.pdf
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

    _default_quantum_number_fields = ('angular_momentum',
                                      'magnetic_number',
                                      'spin',
                                      'radial_nodes')
    _optional_fields = (['kind_name'])

    _default_fields = tuple(list(Orbital._base_fields) +
                            list(_default_quantum_number_fields) +
                            list(_optional_fields))

    def __str__(self):
        orb_dict = self.get_orbital_dict()
        orb_name = self.get_name_from_quantum_numbers(
                        orb_dict['angular_momentum'],
                        magnetic_number=orb_dict['magnetic_number'])
        position_string = "{0:.1f},{0:.1f},{0:.1f}".format(
                                           orb_dict['position'][0],
                                           orb_dict['position'][1],
                                           orb_dict['position'][2])
        out_string = "r{} {} orbital '{}' @ {}".format(
                                           orb_dict['radial_nodes'],
                                           orb_name,
                                           orb_dict['kind_name'],
                                           position_string)
        return out_string

    def _quantum_number_validator(self, value,value_string, value_range):
        """
        Helper function, checks that value is indeed a integer, or None
        (in which case it returns None) and that the value falls within
        the input range. Returns the value if it passes and will raise
        an Exception otherwise

        :param value: the value to be validated
        :param value_string: the label of the value
        :param value_range: range of values the value may fall
        :return value the validated number
        """
        if value is None:
            return None
        if type(value) is not int:
            raise Exception('{} must always be an integer you provided {}'
            'instead'.format(value_string, value))
        if value < min(value_range) or value > max(value_range):
            raise Exception('You supplied {}  of value {} but it must be in'
            'the range {} instead'.format( value_string, value,  value_range))
        return value

    def _validate_keys(self, input_dict):
        """
        Validates the keys otherwise raise ValidationError. Does basic
        validation from the parent followed by validations for the
        quantum numbers. Raises exceptions should the input_dict fail the
        valiation or if it contains any unsupported keywords.

        :param input_dict: the dictionary of keys to be validated
        :return validated_dict a validated dictionary
        """
        validated_dict = super(RealhydrogenOrbital,
                               self)._validate_keys(input_dict)
        # removes all validated items from input_dict
        input_dict = {x: input_dict[x] for x in input_dict
                      if x not in validated_dict}
        # get quantum numbers
        quantum_number_dict = {}
        for key in RealhydrogenOrbital._default_quantum_number_fields:
                quantum_number_dict[key] = input_dict.pop(key, None)
        # state lower and upper limits
        accepted_range = {}
        accepted_range["angular_momentum"] = [-5, 3]
        accepted_range["radial_nodes"] = [0, 2]
        accepted_range["spin"] = [-1, 1]
        l = quantum_number_dict["angular_momentum"]
        if l >= 0:
            accepted_range["magnetic_number"] = [0, 2*l]
        else:
            accepted_range["magnetic_number"] = [0, -l]
        # Here the tests with the limits defined above
        for key in RealhydrogenOrbital._default_quantum_number_fields:
            validated_number = self._quantum_number_validator(
                quantum_number_dict[key], key, accepted_range[key])
            validated_dict[key] = validated_number

        if validated_dict["angular_momentum"] is None:
            raise InputValidationError("Must supply angular_momentum")
        if validated_dict["magnetic_number"] is None:
            raise InputValidationError("Must supply magnetic_number")
        if validated_dict["radial_nodes"] is None:
            validated_dict["radial_nodes"] = 0
        try:
            self.get_name_from_quantum_numbers(
                validated_dict['angular_momentum'],
                magnetic_number=validated_dict['magnetic_number'])
        except InputValidationError:
            raise InputValidationError("Invalid angular momentum magnetic"
                                       " number combination.")

        # Finally checks optional fields
        KindName = input_dict.pop('kind_name', None)
        if KindName:
            if not isinstance(KindName, (basestring, None)):
                raise ValidationError('If kind_name is provided must be string')
            validated_dict['kind_name'] = KindName
        Kind_index = input_dict.pop('kind_index', None)
        if Kind_index:
            if not isinstance(Kind_index, (int, None)):
                raise ValidationError('If kind_index is provided must be int')
            validated_dict['kind_index'] = Kind_index

        if input_dict:
            raise ValidationError("Some unrecognized keys: {}".
                                  format(input_dict.keys()))
        return validated_dict

    @classmethod
    def get_name_from_quantum_numbers(cls, angular_momentum,
                                      magnetic_number=None):
        """
        Returns the orbital_name correponding to the angular_momentum alone,
        or to both angular_number with magnetic_number. For example using
        angular_momentum=1 and magnetic_number=1 will return "Px"
        """
        # importing a copy of the conversion_dict
        convert_ref = copy.deepcopy(conversion_dict)
        orbital_name = [x for x in convert_ref if
                any([convert_ref[x][y]['angular_momentum'] ==
                angular_momentum for y in convert_ref[x]])]
        if len(orbital_name) == 0:
            raise InputValidationError("No orbital name corresponding to the "
            "angular_momentum {} could be found".format(angular_momentum))
        if magnetic_number is not None:
            # finds angu
            orbital_name = orbital_name[0]
            orbital_name = [x for x in convert_ref[orbital_name] if
                            convert_ref[orbital_name][x]['magnetic_number']
                            == magnetic_number]

            if len(orbital_name) == 0:
                raise InputValidationError("No orbital name corresponding to "
                                           "the magnetic_number {} could be "
                                           "found".format(magnetic_number))
        return orbital_name[0]

    @classmethod
    def get_quantum_numbers_from_name(cls, name):
        """
        Returns all the angular and magnetic numbers corresponding to name.
        For example, using "P" as name will return all quantum numbers
        associated with a "P" orbital, while "Px" will return only one set
        of quantum numbers, the ones associated with "Px"
        """
        # importing a copy of the conversion_dict
        convert_ref = copy.deepcopy(conversion_dict)
        if not isinstance(name, basestring):
            raise InputValidationError('Input name must be a string')
        name = name.upper()
        list_of_dicts = [convert_ref[x][y] for x in convert_ref for y in
                         convert_ref[x] if (y == name or x == name)]
        if len(list_of_dicts) == 0:
            raise InputValidationError("Invalid choice of projection name")
        return list_of_dicts

#     @classmethod
#     def generate_orbitals(cls, name=None, spin=0, radial_nodes=0,
#                           site=None, **kwargs):
#         """
#         Return any and all orbitals which match to those used in the
#         conversion dictionary returns a list of real hydrogen orbitals
#         which match, or raises an error if an invalid orbital name was
#         supplied. If a site is supplied, the coordinates will be applied
#         from it.
#
#         :param name: a string corresponding to a projeciton name
#         :param site: if a site is passed, will use the position of that site
#         :param spin: the spin quantum number
#         :param radial_nodes: number of radial nodes
#         :kwargs: additional parameters specifying properties of the orbitals
#         :return list_of_classes: a list of orbitals produced from the input
#         """
#
#         # finding appropriate raw_dict arguments from _conversion_dict
#         if name:
#             list_of_dicts = self.get_quantum_numbers_from_name(name)
#         else:
#             list_of_dicts = [{}]
#
#         # appending site data if possible
#         site_dict = {}
#         if site is not None:
#             site_dict = cls._prep_raw_dict_keys_from_site(site)
#         list_of_classes = []
#         for this_dict in list_of_dicts:
#             this_dict['spin'] = spin
#             this_dict['radial_nodes'] = radial_nodes
#             this_dict.update(kwargs)
#             this_dict.update(site_dict)
#             c = cls()  # intialize and set it
#             c.set_orbital_dict(this_dict)
#             list_of_classes.append(c)
#         return list_of_classes

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

