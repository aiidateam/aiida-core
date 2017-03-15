# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.common.exceptions import ValidationError, MissingPluginError
import math


class Orbital(object):
    """
    Base class for Orbitals. Can handle certain basic fields, their setting
    and validation. More complex Orbital objects should then inherit from
    this class

    :param position: the absolute position (three floats) units in angstrom
    :param x_orientation: x,y,z unit vector defining polar angle theta
                          in spherical coordinates unitless
    :param z_orientation: x,y,z unit vector defining azimuthal angle phi
                          in spherical coordinates unitless
    :param orientation_spin: x,y,z unit vector defining the spin orientation
                             unitless
    :param diffusivity: Float controls the radial term in orbital equation
                        units are reciprocal Angstrom.
    :param module_name: internal parameter, stores orbital type

    """
    #NOTE x_orientation, z_orientation, spin_orientation, diffusivity might
    #all need to be moved to RealHydrogenOrbital

    _base_fields = ('position',
                    'x_orientation',
                    'z_orientation',
                    'spin_orientation',
                    'diffusivity',
                    'module_name', # Actually, this one is system reserved
                    )

    def __init__(self):
        self._orbital_dict = {}

    def __repr__(self):
        module_name = self.get_orbital_dict()['module_name']
        return '<{}: {}>'.format(module_name, str(self))

    def __str__(self):
        raise NotImplementedError

    def _validate_keys(self, input_dict):
        """
        Checks all the input_dict and tries to validate them , to ensure
        that they have been properly set raises Exceptions indicating any
        problems that should arise during the validation

        :param input_dict: a dictionary of inputs
        :return: input_dict: the original dictionary with all validated kyes
                 now removed
        :return: validated_dict: a dictionary containing all the input keys
                 which have now been validated.
        """

        validated_dict = {}
        for k in self._base_fields:
            v = input_dict.pop(k, None)
            if k == "module_name":
                if v is None:
                    raise TypeError
                try:
                    OrbitalFactory(v)
                except (MissingPluginError, TypeError):
                    raise ValidationError("The module name {} was found to "
                                          "be invalid".format(v))
            if k == "position":
                if v is None:
                    validated_dict.update({k: v})
                    continue
                try:
                    v = list(float(i) for i in v)
                    if len(v) != 3:
                        raise ValueError
                except (ValueError, TypeError):
                        raise ValueError("Wrong format for position, must be a"
                                         " list of three float numbers.")
            if "orientation" in k :
                if v is None:
                    validated_dict.update({k: v})
                    continue
                try:
                    v = list(float(i) for i in v)
                    if len(v) != 3:
                        raise ValueError
                except (ValueError, TypeError):
                        raise ValueError("Wrong format for {}, must be a"
                                         " list of three float numbers.")
            # From a spherical cooridnate version of orientation
            # try:
            #     v = tuple(float(i) for i in v)
            #     if len(v) != (2):
            #         raise ValueError
            #     if v[0] >= 2*math.pi or v[0] <= 0:
            #         raise ValueError
            #     if v[1] >= math.pi or v[1] <= 0:
            #         raise ValueError
            # except(ValueError, TypeError):
            #     raise ValueError("Wrong format for {}, must be two tuples"
            #                      " each having two floats theta, phi where"
            #                      " 0<=theta<2pi and 0<=phi<=pi.".format(k))
            if k == "diffusivity":
                if v is None:
                    validated_dict.update({k: v})
                    continue
                try:
                    v = float(v)
                except ValueError:
                    raise ValidationError("Diffusivity must always be a float")
            validated_dict.update({k: v})
        return validated_dict

    def set_orbital_dict(self, init_dict):
        """
        Sets the orbital_dict, which can vary depending on the particular
        implementation of this base class.

        :param init_dict: the initialization dictionary
        """
        if not isinstance(init_dict, dict):
            raise Exception('You must supply a dict as an init')
        # Adds the module_name in hard-coded manner
        init_dict.update({"module_name": self._get_module_name()})
        validated_dict = self._validate_keys(init_dict)
        for k, v in validated_dict.iteritems():
            self._orbital_dict[k] = v

    def get_orbital_dict(self):
        """
        returns the internal keys as a dictionary
        """
        output = {}
        for k in self._default_fields:
            try:
                output[k] = self._orbital_dict[k]
            except KeyError:
                pass
        return output

    def _get_module_name(self):
        """
        Sets the module name, or label, to the orbital
        """
        return self.__module__.split('.')[-1]


def OrbitalFactory(module):
    """
    Factory method that returns a suitable Orbital subclass.

    :param module: a valid string recognized as a Orbital subclass
    """
    from aiida.common.pluginloader import BaseFactory

    return BaseFactory(module, Orbital, "aiida.common.orbital")


