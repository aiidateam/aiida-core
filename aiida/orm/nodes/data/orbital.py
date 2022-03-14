# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin to model an atomic orbital."""
import copy

from aiida.common.exceptions import ValidationError
from aiida.plugins import OrbitalFactory

from .data import Data

__all__ = ('OrbitalData',)


class OrbitalData(Data):
    """
    Used for storing collections of orbitals, as well as
    providing methods for accessing them internally.
    """

    def clear_orbitals(self):
        """
        Remove all orbitals that were added to the class
        Cannot work if OrbitalData has been already stored
        """
        self.base.attributes.set('orbital_dicts', [])

    def get_orbitals(self, **kwargs):
        """
        Returns all orbitals by default. If a site is provided, returns
        all orbitals cooresponding to the location of that site, additional
        arguments may be provided, which act as filters on the retrieved
        orbitals.

        :param site: if provided, returns all orbitals with position of site
        :kwargs: attributes than can filter the set of returned orbitals
        :return list_of_outputs: a list of orbitals
        """

        orbital_dicts = copy.deepcopy(self.base.attributes.get('orbital_dicts', None))
        if orbital_dicts is None:
            raise AttributeError('Orbitals must be set before being retrieved')

        filter_dict = {}
        filter_dict.update(kwargs)
        # prevents KeyError from occuring
        orbital_dicts = [x for x in orbital_dicts if all(y in x for y in filter_dict)]
        orbital_dicts = [x for x in orbital_dicts if all(x[y] == z for y, z in filter_dict.items())]

        list_of_outputs = []
        for orbital_dict in orbital_dicts:
            try:
                orbital_type = orbital_dict.pop('_orbital_type')
            except KeyError:
                raise ValidationError(f'No _orbital_type found in: {orbital_dict}')

            cls = OrbitalFactory(orbital_type)
            orbital = cls(**orbital_dict)
            list_of_outputs.append(orbital)
        return list_of_outputs

    def set_orbitals(self, orbitals):
        """
        Sets the orbitals into the database. Uses the orbital's inherent
        set_orbital_dict method to generate a orbital dict string.

        :param orbital: an orbital or list of orbitals to be set
        """
        if not isinstance(orbitals, list):
            orbitals = [orbitals]
        orbital_dicts = []

        for orbital in orbitals:
            orbital_dict = copy.deepcopy(orbital.get_orbital_dict())
            try:
                _orbital_type = orbital_dict['_orbital_type']
            except KeyError:
                raise ValueError(f'No _orbital_type found in: {orbital_dict}')
            orbital_dicts.append(orbital_dict)
        self.base.attributes.set('orbital_dicts', orbital_dicts)


##########################################################################
#     Here are some ideas for potential future convenience methods
#########################################################################
#     def set_projection_on_site(self, orbital, site, tag=None):
#         """
#         Sets a orbital on a site
#         We prepare the description dictionary, using information `parsed`
#         from the site.
#         """
#         diffusivity = from_site_guess_diffusivity(site) # or 1.
#         position = site.position
#         description = {'somedictionary of the above':''}
#         self.set_projection(orbital=orbital, description=description)

#     def delete_projections_by_attribute(self, selection_attributes):
#         """
#         Deletes all projections whose internal attributes correspond to the
#         selection_attributes
#         """
#         raise NotImplementedError
#
#     def modify_projections(self, key_attributes_to_select_projections, attributes_to_be_modified):
#         """
#         Modifies the projections, as selected by the key_attributes.
#         Overwrites attributes inside these projections, to values stored
#         in attributes_to_be_modified
#         """
#
#    def set_realhydrogenorbitals_from_structure(self, structure, pseudo_family=None):
#        raise NotImplementedError
