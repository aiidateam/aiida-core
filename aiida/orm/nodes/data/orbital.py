# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
from six.moves import zip

from .data import Data
from .structure import Site as site_class
from aiida.common.exceptions import ValidationError, InputValidationError

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
        self.set_attribute('orbital_dicts', [])

    def _get_orbital_class_from_orbital_dict(self, orbital_dict):
        """
        Gets the orbital class from the orbital dictionary stored in DB

        :param orbital_dict: orbital dictionary associated with the orbital
        :return: an Orbital produced using the module_name
        """
        from aiida.plugins import OrbitalFactory

        try:
            module_name = orbital_dict['module_name']
        except KeyError:
            raise ValidationError("No valid module name found in orbital")
        return OrbitalFactory(module_name)

    @staticmethod
    def _prep_orbital_dict_keys_from_site(site):
        """
        Prepares the position from an input site.

        :param site: a site of site class
        :return out_dict: a dictionary of attributes parsed from the site
                          (currently only position)
        """
        if not isinstance(site, site_class):
            raise InputValidationError('Provided input was not a site')

        out_dict = {}
        try:
            position = site.position
            out_dict.update({'position': position})
        except AttributeError:
            raise InputValidationError('site did not have a position!')
        return out_dict

    def get_orbitals(self, with_tags=False, **kwargs):
        """
        Returns all orbitals by default. If a site is provided, returns
        all orbitals cooresponding to the location of that site, additional
        arguments may be provided, which act as filters on the retrieved
        orbitals.

        :param site: if provided, returns all orbitals with position of site
        :param with_tags: if provided returns all tags stored
        :kwargs: attributes than can filter the set of returned orbitals
        :return list_of_outputs: a list of orbitals and also tags if
                                 with_tags was set to True
        """

        import copy
        orbital_dicts = copy.deepcopy(self.get_attribute('orbital_dicts', None))
        if orbital_dicts is None:
            raise AttributeError('Orbitals must be set before')

        filter_dict = {}
        filter_dict.update(kwargs)
        # prevents KeyError from occuring
        orbital_dicts = [x for x in orbital_dicts if all([y in x for y in filter_dict])]
        orbital_dicts = [x for x in orbital_dicts if
                         all([x[y] == filter_dict[y] for y in filter_dict])]

        list_of_outputs = []
        for orbital_dict in orbital_dicts:
            OrbitalClass = self._get_orbital_class_from_orbital_dict(
                            orbital_dict)
            orbital = OrbitalClass()
            try:
                orbital.set_orbital_dict(orbital_dict)
            except ValidationError:
                raise ValueError("Could not reconstruct orbital from data")
            list_of_outputs.append(orbital)
        if with_tags:
            tags = copy.deepcopy(self.get_attribute('tags', None))
            list_of_outputs.append(tags)
        return list_of_outputs

    def set_orbitals(self, orbital, tag=None):
        """
        Sets the orbitals into the database. Uses the orbital's inherent
        set_orbital_dict method to generate a orbital dict string at is stored
        along with the tags, if provided.

        :param orbital: an orbital or list of orbitals to be set
        :param tag: a list of strings must be of length orbital
        """
        from aiida.tools.data.orbital import Orbital

        # convert everything to lists
        if not isinstance(orbital, list):
            orbital = [orbital]
        if not isinstance(tag, list):
            if tag is None:
                tag = ['']*len(orbital)
            else:
                tag = [tag]
        # check if list length matches
        if len(tag) != len(orbital):
            raise ValueError()
        for input_name, this_input, kind in [['orbital', orbital, Orbital],
                                            ['tag', tag, six.string_types]]:
            if not isinstance(this_input, (list, tuple)):
                raise ValueError
            if any([True for _ in this_input if not isinstance(_, kind)]):
                raise ValueError("{} must be a list of {}"
                                 "".format(input_name, kind))
        list_of_tags_to_be_stored = []
        list_of_orbitaldicts_to_be_stored = []
        for this_projection, this_tag in zip(orbital, tag):
            orbital_dict = this_projection.get_orbital_dict()
            OrbitalClass = self._get_orbital_class_from_orbital_dict(
                           orbital_dict)
            test_orbital = OrbitalClass()
            try:
                test_orbital.set_orbital_dict(orbital_dict)
            except ValidationError:
                raise ValueError("The orbital of tag {} did not"
                                 "pass the validation test".format(this_tag))
            orbital_dict = test_orbital.get_orbital_dict()
            list_of_tags_to_be_stored.append(this_tag)
            list_of_orbitaldicts_to_be_stored.append(orbital_dict)
        self.set_attribute('orbital_dicts', list_of_orbitaldicts_to_be_stored)
        if tag is not None:
            self.set_attribute('tags', list_of_tags_to_be_stored)

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

