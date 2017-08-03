# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.data.array import ArrayData
from aiida.orm.data.orbital import OrbitalData 
from aiida.common.orbital import  Orbital
from aiida.common.exceptions import   ValidationError, NotExistent
import copy
import numpy as np
from aiida.orm import load_node
from aiida.orm.data.array.bands import BandsData


class ProjectionData(OrbitalData, ArrayData): 
    """
    A class to handle arrays of projected wavefunction data. That is projections
    of a orbitals, usually an atomic-hydrogen orbital, onto a
    given bloch wavefunction, the bloch wavefunction being indexed by
    s, n, and k. E.g. the elements are the projections described as
    < orbital | Bloch wavefunction (s,n,k) >
    """
    def _check_projections_bands(self, projection_array):
        """
        Checks to make sure that a reference bandsdata is already set, and that
        projection_array is of the same shape of the bands data

        :param projwfc_arrays: nk x nb x nwfc array, to be
                               checked against bands

        :raise: AttributeError if energy is not already set
        :raise: AttributeError if input_array is not of same shape as
                dos_energy
        """
        try:
            shape_bands = np.shape(self.get_reference_bandsdata())
        except AttributeError:
            raise ValidationError('Bands must be set first, then projwfc')
        # The [0:2] is so that each array, and not collection of arrays
        # is used to make the comparison
        if np.shape(projection_array) != shape_bands:
            raise AttributeError('These arrays are not the same shape as'
                                 ' the bands')
        return None

    def set_reference_bandsdata(self, value):
        """
        Sets a reference bandsdata, creates a uuid link between this data
        object and a bandsdata object, must be set before any projection arrays

        :param value: a BandsData instance, a uuid or a pk
        :raise: NotExistent if there was no BandsData associated with uuid or pk
        """
        if isinstance(value, BandsData):
            uuid = value.uuid 
        else:
            try:
                pk = int(value)
                bands = load_node(pk=pk, type=BandsData)
                uuid = bands.uuid
            except ValueError:
                uuid = str(value)
                try:
                    bands = load_node(uuid=uuid, type=BandsData)
                    uuid = bands.uuid
                except :
                    raise NotExistent("The value passed to "
                                      "set_reference_bandsdata was not "
                                      "associated to any bandsdata")
                    
        self._set_attr('reference_bandsdata_uuid', uuid)

    def get_reference_bandsdata(self):
        """
        Returns the reference BandsData, using the set uuid via
        set_reference_bandsdata

        :return: a BandsData instance
        :raise AttributeError: if the bandsdata has not been set yet
        :raise NotExistent: if the bandsdata uuid did not retrieve bandsdata
        """
        try:
            uuid = self.get_attr('reference_bandsdata_uuid')
        except AttributeError:
            raise AttributeError("BandsData has not been set for this instance")
        try:
            #bands = load_node(uuid=uuid, type=BandsData)
            bands = load_node(uuid=uuid) #TODO switch to above once type
                                         # has been implemented for load_node
        except NotExistent:
            raise NotExistent("The bands referenced to this class have not been "
                              "found in this database.")
        return bands

    def _find_orbitals_and_indices(self, **kwargs):
        """
        Finds all the orbitals and their indicies associated with kwargs
        essential for retrieving the other indexed array parameters

        :param kwargs: kwargs that can call orbitals as in get_orbitals()
        :return: retrieve_indexes, list of indicicies of orbitals corresponding
                 to the kwargs
        :return: all_orbitals, list of orbitals to which the indexes correspond
        """
        # index_and_orbitals = self._get_orbitals_and_index()
        index_and_orbitals = []
        selected_orbitals = self.get_orbitals(**kwargs)
        selected_orb_dicts = [orb.get_orbital_dict() for orb
                              in selected_orbitals]
        all_orbitals = self.get_orbitals()
        all_orb_dicts = [orb.get_orbital_dict() for orb in all_orbitals]
        retrieve_indices = [i for i in range(len(all_orb_dicts))
                            if all_orb_dicts[i] in selected_orb_dicts]
        return  retrieve_indices, all_orbitals

    def get_pdos(self, **kwargs):
        """
        Retrieves all the pdos arrays corresponding to the input kwargs

        :param kwargs: inputs describing the orbitals associated with the pdos
                       arrays
        :return: a list of tuples containing the orbital, energy array and pdos
                 array associated with all orbitals that correspond to kwargs

        """
        retrieve_indices, all_orbitals = self._find_orbitals_and_indices(**kwargs)
        out_list = [(all_orbitals[i],
                    self.get_array("pdos_{}".format(
                    self._from_index_to_arrayname(i))),
                    self.get_array("energy_{}".format(
                    self._from_index_to_arrayname(i))) )
                    for i in retrieve_indices]
        return out_list
    
    def get_projections(self, **kwargs):
        """
        Retrieves all the pdos arrays corresponding to the input kwargs

        :param kwargs: inputs describing the orbitals associated with the pdos
                       arrays
        :return: a list of tuples containing the orbital, and projection arrays
                 associated with all orbitals that correspond to kwargs

        """
        retrieve_indices, all_orbitals = self._find_orbitals_and_indices(**kwargs)
        out_list = [(all_orbitals[i],
                    self.get_array("proj_{}".format(
                    self._from_index_to_arrayname(i))))
                    for i in retrieve_indices]
        return out_list

    def _from_index_to_arrayname(self, index):
        """
        Used internally to determine the array names.
        """
        return "array_{}".format(index)
    
    def set_projectiondata(self,list_of_orbitals, list_of_projections=None,
                             list_of_energy=None, list_of_pdos=None,
                             tags = None, bands_check=True):
        """
        Stores the projwfc_array using the projwfc_label, after validating both.

        :param list_of_orbitals: list of orbitals, of class orbital data.
                                 They should be the ones up on which the
                                 projection array corresponds with.

        :param list_of_projections: list of arrays of projections of a atomic
                              wavefunctions onto bloch wavefunctions. Since the
                              projection is for every bloch wavefunction which
                              can be specified by its spin (if used), band, and
                              kpoint the dimensions must be
                              nspin x nbands x nkpoints for the projwfc array.
                              Or nbands x nkpoints if spin is not used.

        :param energy_axis: list of energy axis for the list_of_pdos

        :param list_of_pdos: a list of projected density of states for the
                             atomic wavefunctions, units in states/eV

        :param tags: A list of tags, not supported currently.

        :param bands_check: if false, skips checks of whether the bands has
                            been already set, and whether the sizes match. For
                            use in parsers, where the BandsData has not yet
                            been stored and therefore get_reference_bandsdata
                            cannot be called
        """
        def single_to_list(item):
            """
            Checks if the item is a list or tuple, and converts it to a list
            if it is not already a list or tuple

            :param item: an object which may or may not be a list or tuple
            :return: item_list: the input item unchanged if list or tuple and
                                [item] otherwise
            """
            if isinstance(item, (list, tuple)):
                return item
            else:
                return [item]
            
        def array_list_checker(array_list, array_name, orb_length):
            """
            Does basic checks over everything in the array_list. Makes sure that
            all the arrays are np.ndarray floats, that the length is same as
            required_length, raises exception using array_name if there is
            a failure
            """
            if not all([isinstance(_,np.ndarray) for _ in array_list]):
                raise ValidationError("{} was not composed "
                                      "entirely of ndarrays".format(array_name))
            if len(array_list) != orb_length:
                raise ValidationError("{} did not have the same length as the "
                                      "list of orbitals".format(array_name))
        
        ##############
        list_of_orbitals = single_to_list(list_of_orbitals)
        list_of_orbitals = copy.deepcopy(list_of_orbitals)

        # validates the input data
        if not list_of_pdos and not list_of_projections:
            raise ValidationError("Must set either pdos or projections")
        if bool(list_of_energy) != bool(list_of_pdos):
            raise ValidationError("list_of_pdos and list_of_energy must always "
                                  "be set together")

        orb_length = len(list_of_orbitals)
        
        # verifies and sets the orbital dicts
        list_of_orbital_dicts = []
        for i in range(len(list_of_orbitals)):
            this_orbital = list_of_orbitals[i]
            orbital_dict = this_orbital.get_orbital_dict()
            OrbitalClass = self._get_orbital_class_from_orbital_dict(
                           orbital_dict)
            test_orbital = OrbitalClass()
            try:
                test_orbital.set_orbital_dict(orbital_dict)
            except ValidationError:
                raise ValueError("The orbital with dict {} "
                                 "failed.".format(orbital_dict))
            list_of_orbital_dicts.append(test_orbital.get_orbital_dict())
        self._set_attr('orbital_dicts', list_of_orbital_dicts)

        # verifies and sets the projections
        if list_of_projections:
            list_of_projections = single_to_list(list_of_projections)
            array_list_checker(list_of_projections, "projections", orb_length)
            for i in range(len(list_of_projections)):
                this_projection = list_of_projections[i]
                array_name = self._from_index_to_arrayname(i)
                if bands_check:
                    self._check_projections_bands(this_projection)
                self.set_array("proj_{}".format(array_name), this_projection)

        # verifies and sets both pdos and energy
        if list_of_pdos:
            list_of_pdos = single_to_list(list_of_pdos)
            list_of_energy = single_to_list(list_of_energy)
            array_list_checker(list_of_pdos, "pdos", orb_length)
            array_list_checker(list_of_energy, "energy", orb_length)
            for i in range(len(list_of_pdos)):
                this_pdos = list_of_pdos[i]
                this_energy = list_of_energy[i]
                array_name = self._from_index_to_arrayname(i)
                if bands_check:
                    self._check_projections_bands(this_projection)
                self.set_array("pdos_{}".format(array_name), this_pdos)
                self.set_array("energy_{}".format(array_name), this_energy)

        # verifies and sets the tags
        if tags is not None:
            try:
                if len(tags) != len(list_of_orbitals):
                    raise ValidationError("must set as many tags as projections")
            except IndexError:
                return ValidationError("tags must be a list")

            if not all([isinstance(_,basestring) for _ in tags]):
                raise ValidationError("Tags must set a list of strings")
            self._set_attr('tags', tags)

    def set_orbitals(self, **kwargs):
        """
        This method is inherited from OrbitalData, but is blocked here.
        If used will raise a NotImplementedError
        """
        raise NotImplementedError("You cannot set orbitals using this class!"
                                  " This class is for setting orbitals and "
                                  " projections only!")
