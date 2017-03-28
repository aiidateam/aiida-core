# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import copy
import numpy as np
import re
from aiida.parsers.parser import Parser  # ParserParamManager
from aiida.parsers.plugins.quantumespresso import QEOutputParsingError
from aiida.parsers.plugins.quantumespresso import parse_raw_out_basic
from aiida.common.exceptions import InvalidOperation
from aiida.orm.data.parameter import ParameterData
from aiida.common.orbital import OrbitalFactory
from aiida.orm.calculation.job.quantumespresso.projwfc import ProjwfcCalculation
from aiida.orm.data.array.projection import ProjectionData
from aiida.orm.data.array.bands import BandsData
from aiida.common.datastructures import calc_states
from aiida.orm.data.array.xy import XyData
import fnmatch


def find_orbitals_from_statelines(out_info_dict):
    """
    This function reads in all the state_lines, that is, the lines describing
    which atomic states, taken from the pseudopotential, are used for the
    projection. Then it converts these state_lines into a set of orbitals

    :param out_info_dict: contains various technical internals useful in parsing
    :return: orbitals, a list of orbitals suitable for setting ProjectionData
    """
    out_file = out_info_dict["out_file"]
    atomnum_re = re.compile(r"atom (.*?)\(")
    element_re = re.compile(r"\((.*?)\)")
    lnum_re = re.compile(r"l=(.*?)m=")
    mnum_re = re.compile(r"m=(.*?)\)")
    wfc_lines = out_info_dict["wfc_lines"]
    state_lines = [out_file[wfc_line] for wfc_line in wfc_lines]
    state_dicts = []
    for state_line in state_lines:
        try:
            state_dict = {}
            state_dict["atomnum"] = int(atomnum_re.findall(state_line)[0])
            state_dict["atomnum"] -= 1 # to keep with orbital indexing
            state_dict["kind_name"] = element_re.findall(state_line)[0].strip()
            state_dict["angular_momentum"] = int(lnum_re.findall(state_line)[0])
            state_dict["magnetic_number"] = int(mnum_re.findall(state_line)[0])
            state_dict["magnetic_number"] -= 1 # to keep with orbital indexing
        except ValueError:
            raise QEOutputParsingError("State lines are not formatted "
            "in a standard way.")
        state_dicts.append(state_dict)

    # here is some logic to figure out the value of radial_nodes to use
    new_state_dicts = []
    for i in range(len(state_dicts)):
        radial_nodes = 0
        state_dict = state_dicts[i].copy()
        for j in range(i-1, -1, -1):
            if state_dict == state_dicts[j]:
                radial_nodes += 1
        state_dict["radial_nodes"] = radial_nodes
        new_state_dicts.append(state_dict)
    state_dicts = new_state_dicts

    # here is some logic to assign positions based on the atom_index
    structure = out_info_dict["structure"]
    for state_dict in state_dicts:
        site_index = state_dict.pop("atomnum")
        state_dict["position"] = structure.sites[site_index].position

    # here we set the resulting state_dicts to a new set of orbitals
    orbitals = []
    realh = OrbitalFactory("realhydrogen")
    for state_dict in state_dicts:
        this_orb = realh()
        this_orb.set_orbital_dict(state_dict)
        orbitals.append(this_orb)
    return orbitals

# def find_dicts_from_pdos_atm_filenames(out_info_dict):
#     """
#     Finds dicts that can be later matched
#     :param out_info_dict: dictionary of paramters used for the parsing
#     :return: pdos_atm_dicts a list of dicts describing the pdos_atm files
#     """
#     pdos_atm_array_dict = out_info_dict["pdos_atm_array_dict"]
#     pdos_atm_names = [k for k in pdos_atm_array_dict]
#     pdos_atm_names.sort()
#     def extract_pdosatm_labeltag(pdos_name):
#         """
#         Extracts dictionary information from the pdos_name suitable for
#         setting or matching to an orbital
#         :param pdos_name: the pdos_atm file name to parse dict info from
#         :return: pdos_labeldict a dict containing key orbital parameters
#         """
#         pdos_labeldict = {}
#         spdf_dict = {'s':0,'p':1,'d':2,'f':3}
#         num_re = re.compile('\d') #Finds all numbers in a string
#         bracket_re = re.compile(r"\(([A-Za-z0-9_]+)\)") #finds bracket-enclosed
#         nums = num_re.findall(pdos_name)       # all the numbers in name
#         brackets = bracket_re.findall(pdos_name) #all bracket enclosed in name
#         pdos_labeldict['atomnum'] = int(nums[0]) - 1
#         pdos_labeldict['kind_name'] = brackets[0]
#         pdos_labeldict['angular_momentum'] = int(spdf_dict[brackets[1]])
#         # pdos_labeldict['filename'] = pdos_name # not needed, sorted filename
#         return pdos_labeldict
#
#     pdos_namedicts = [extract_pdosatm_labeltag(name) for name
#                           in pdos_atm_names]
#
#     # here is some logic to figure out the value of radial_nodes to use
#     new_pdos_namedicts = []
#     k1 = "angular_momentum"
#     k2 = "atomnum"
#     for i in range(len(pdos_namedicts)):
#         radial_nodes = 0
#         state_dict = pdos_namedicts[i].copy()
#         for j in range(i-1, -1, -1):
#             if state_dict[k1] == pdos_namedicts[j][k1] and (
#                state_dict[k2] == pdos_namedicts[j][k2]):
#                 radial_nodes += 1
#         state_dict["radial_nodes"] = radial_nodes
#         new_pdos_namedicts.append(state_dict)
#     pdos_namedicts = new_pdos_namedicts
#
#     # here is some logic to assign positions based on the atom_index
#     structure = out_info_dict["structure"]
#     for state_dict in state_dicts:
#         site_index = state_dict.pop("atomnum")
#         state_dict["position"] = structure.sites[site_index].position
#     return pdos_atm_namedicts


def spin_dependent_subparcer(out_info_dict):
    """
    This find the projection and bands arrays from the out_file and
    out_info_dict. Used to handle the different possible spin-cases in
    a convenient manner.

    :param out_info_dict: contains various technical internals useful in parsing
    :return: ProjectionData, BandsData parsed from out_file
    """

    out_file = out_info_dict["out_file"]
    spin_down = out_info_dict["spin_down"]
    od = out_info_dict #using a shorter name for convenience
    #   regular expressions needed for later parsing
    WaveFraction1_re = re.compile(r"\=(.*?)\*")  # state composition 1
    WaveFractionremain_re = re.compile(r"\+(.*?)\*")  # state comp 2
    FunctionId_re = re.compile(r"\#(.*?)\]")  # state identity
    # primes arrays for the later parsing
    num_wfc = len(od["wfc_lines"])
    bands = np.zeros([od["k_states"], od["num_bands"]])
    projection_arrays = np.zeros([od["k_states"], od["num_bands"], num_wfc])

    try:
        for i in range(od["k_states"]):
            if spin_down:
                i += od["k_states"]
            # grabs band energy
            for j in range (i*od["num_bands"],(i+1)*od["num_bands"],1):
                out_ind = od["e_lines"][j]
                val = out_file[out_ind].split()[4]
                bands[i%od["k_states"]][j%od["num_bands"]] = val
                #subloop grabs pdos
                wave_fraction = []
                wave_id = []
                for k in range(od["e_lines"][j]+1,od["psi_lines"][j],1):
                    out_line = out_file[k]
                    wave_fraction += WaveFraction1_re.findall(out_line)
                    wave_fraction += WaveFractionremain_re.findall(out_line)
                    wave_id += FunctionId_re.findall(out_line)
                if len(wave_id) != len(wave_fraction):
                    raise IndexError
                for l in range (len(wave_id)):
                    wave_id[l] = int(wave_id[l])
                    wave_fraction[l] = float(wave_fraction[l])
                    #sets relevant values in pdos_array
                    projection_arrays[i%od["k_states"]][
                        j%od["num_bands"]][wave_id[l]-1] = wave_fraction[l]
    except IndexError:
        raise QEOutputParsingError("the standard out file does not "
                                   "comply with the official "
                                   "documentation.")

    bands_data = BandsData()
    try:
    # Attempts to retrive the kpoints from the parent calc
        parent_calc = out_info_dict["parent_calc"]
        parent_kpoints = parent_calc.get_inputs_dict()['kpoints']
        if len(od['k_vect']) != len(parent_kpoints.get_kpoints()):
            raise AttributeError
        bands_data.set_kpointsdata(parent_kpoints)
    except AttributeError:
        bands_data.set_kpoints(od['k_vect'].astype(float))

    bands_data.set_bands(bands, units='eV')

    orbitals = out_info_dict["orbitals"]
    if len(orbitals) != np.shape(projection_arrays[0,0,:])[0]:
        raise QEOutputParsingError("There was an internal parsing error, "
                                   " the projection array shape does not agree"
                                   " with the number of orbitals")
    projection_data = ProjectionData()
    projection_data.set_reference_bandsdata(bands_data)
    projections = [projection_arrays[:,:,i] for i in range(len(orbitals))]

    # Do the bands_check manually here
    for projection in projections:
        if np.shape(projection) !=  np.shape(bands):
            raise AttributeError("Projections not the same shape as the bands")


    #insert here some logic to assign pdos to the orbitals
    pdos_arrays = spin_dependent_pdos_subparcer(out_info_dict)
    energy_arrays = [out_info_dict["energy"]]*len(orbitals)
    projection_data.set_projectiondata(orbitals,
                                       list_of_projections=projections,
                                       list_of_energy=energy_arrays,
                                       list_of_pdos=pdos_arrays,
                                       bands_check=False)
    # pdos=pdos_arrays
    return bands_data,  projection_data

def spin_dependent_pdos_subparcer(out_info_dict):
    """
    Finds and labels the pdos arrays associated with the out_info_dict

    :param out_info_dict: contains various technical internals useful in parsing
    :return: (pdos_name, pdos_array) tuples for all the specific pdos
    """
    spin = out_info_dict["spin"]
    spin_down = out_info_dict["spin_down"]
    pdos_atm_array_dict = out_info_dict["pdos_atm_array_dict"]
    if spin:
        mult_factor = 2
        if spin_down:
            first_array = 4
        else:
            first_array = 3
    else:
        mult_factor = 1
        first_array = 2
    mf = mult_factor
    fa = first_array
    pdos_file_names = [k for k in pdos_atm_array_dict]
    pdos_file_names.sort()
    out_arrays = []
    # we can keep the pdos in synch with the projections by relying on the fact
    # both are produced in the same order (thus the sorted file_names)
    for name in pdos_file_names:
        this_array = pdos_atm_array_dict[name]
        for i in range(fa, np.shape(this_array)[1]):
            if i % mf == 0:
                out_arrays.append(this_array[:,i])

    return out_arrays





class ProjwfcParser(Parser):
    """
    This class is the implementation of the Parser class for projwfc.x in
    Quantum Espresso. Parses projection arrays that map the projection onto
    each point in the bands structure, as well as pdos arrays, which map
    the projected density of states onto an energy axis.
    """

    def __init__(self, calculation):
        """
        Initialize the instance of ProjwfcParser
        """
        # check for valid input
        if not isinstance(calculation, ProjwfcCalculation):
            raise QEOutputParsingError("Input calc must be a "
                                       "ProjwfcCalculation")
        self._calc = calculation
        super(ProjwfcParser, self).__init__(calculation)

    def parse_with_retrieved(self, retrieved):
            """
            Parses the datafolder, stores results.
            Retrieves projwfc output, and some basic information from the
            out_file, such as warnings and wall_time
            """

            # job is unsuccessful until established otherwise
            successful = False
            new_nodes_list = []

            # check if I'm not to overwrite anything
            state = self._calc.get_state()
            if state != calc_states.PARSING:
               raise InvalidOperation("Calculation not in {} state"
                                      .format(calc_states.PARSING))

            # Check that the retrieved folder is there
            try:
                out_folder = self._calc.get_retrieved_node()
            except KeyError:
                self.logger.error("No retrieved folder found")
                return successful, new_nodes_list


            # Reading all the files produced during the calculation
            # Read standard out
            try:
                filpath = out_folder.get_abs_path(self._calc._OUTPUT_FILE_NAME)
                with open(filpath, 'r') as fil:
                        out_file = fil.readlines()
            except OSError:
                self.logger.error("Standard output file could not be found.")
                successful = False
                return successful, new_nodes_list

            # check that the file has finished i.e. JOB DONE is inside the file
            for i in range(len(out_file)):
                line = out_file[-i]
                if "JOB DONE" in line:
                    successful = True
                    break
            if not successful:
                self.logger.error("Computation did not finish properly")
            parsed_data = parse_raw_out_basic(out_file, "PROJWFC")
            # Adds warnings
            for message in parsed_data['warnings']:
                self.logger.error(message)

            # creating node list, setting initial parameters
            output_params = ParameterData(dict=parsed_data)
            new_nodes_list.append((self.get_linkname_outparams(), output_params))

            # checks and reads pdos_tot file
            out_filenames = out_folder.get_folder_list()
            pdostot_filename = fnmatch.filter(out_filenames,'*pdos_tot*')[0]
            try:
                pdostot_path  = out_folder.get_abs_path(pdostot_filename)
                # Energy(eV), Ldos, Pdos
                pdostot_array = np.genfromtxt(pdostot_path)
                energy = pdostot_array[:,0]
                dos = pdostot_array[:,1]
            except OSError:
                successful = False
                self.logger.error("pdos_tot output file could not found")
                return successful, new_nodes_list

            # checks and reads all of the individual pdos_atm files
            pdos_atm_filenames = fnmatch.filter(out_filenames,'*pdos_atm*')
            pdos_atm_array_dict = {name:np.genfromtxt(out_folder.get_abs_path(
                                   name)) for name in pdos_atm_filenames}

            # finding the bands and projections
            out_info_dict = {}
            out_info_dict["out_file"] = out_file
            out_info_dict["energy"] = energy
            out_info_dict["pdos_atm_array_dict"] = pdos_atm_array_dict
            new_nodes_list += self._parse_bands_and_projections(out_info_dict)

            Dos_out = XyData()
            Dos_out.set_x(energy,"Energy","eV")
            Dos_out.set_y(dos,"Dos","states/eV")
            new_nodes_list += [("Dos",Dos_out)]

            return successful, new_nodes_list


    def _parse_bands_and_projections(self, out_info_dict):
        """
        Function that parsers the standard out into bands and projection
        data.
        :param standard_out: standard out file in form of a list
        :param out_info_dict: used to pass technical internal variables
                              to helper functions in compact form

        :return: append_nodes_list a list containing BandsData and
                 ProjectionData parsed from standard_out
        """
        out_file = out_info_dict["out_file"]
        out_info_dict["k_lines"] = []
        out_info_dict["e_lines"] = []
        out_info_dict["psi_lines"] = []
        out_info_dict["wfc_lines"] = []
        append_nodes_list = []

        for i in range(len(out_file)):
            if "k =" in out_file[i]:
                out_info_dict["k_lines"].append(copy.deepcopy(i))
            if "==== e(" in out_file[i]:
                out_info_dict["e_lines"].append(i)
            if "|psi|^2" in out_file[i]:
                out_info_dict["psi_lines"].append(i)
            if "state #" in out_file[i]:
                out_info_dict["wfc_lines"].append(i)

        #Basic check
        if len(out_info_dict["e_lines"]) != len(out_info_dict["psi_lines"]):
            raise QEOutputParsingError("Not formatted in a manner "
            " that can be handled")
        if len(out_info_dict["psi_lines"]) % len(out_info_dict["k_lines"]) != 0:
            raise QEOutputParsingError("Band Energy Points is not "
            " a multiple of kpoints")
        #calculates the number of bands
        out_info_dict["num_bands"] = len(
            out_info_dict["psi_lines"])/len(out_info_dict["k_lines"])

        # Uses the parent input parameters, and checks if the parent used
        # spin calculations try to replace with a query, if possible.
        parent_remote =  self._calc.get_inputs_dict()['parent_calc_folder']
        parent_calc = parent_remote.get_inputs_dict()['remote_folder']
        out_info_dict["parent_calc"] = parent_calc
        parent_param = parent_calc.get_outputs_dict()['output_parameters']
        try:
            structure = parent_calc.get_inputs_dict()['structure']
        except KeyError:
            raise ValueError("The parent had no structure! Cannot parse"
                             "from this!")
        try :
            nspin = parent_param.get_dict()['number_of_spin_components']
            if nspin != 1:
                spin = True
            else:
                spin = False
        except KeyError:
            spin = False
        out_info_dict["spin"] = spin

        #changes k-numbers to match spin
        #because if spin is on, k points double for up and down
        out_info_dict["k_states"] = len(out_info_dict["k_lines"])
        if spin:
            if out_info_dict["k_states"] % 2 != 0:
                raise ValueError("Internal formatting error regarding spin")
            out_info_dict["k_states"] = out_info_dict["k_states"]/2

        #   adds in the k-vector for each kpoint
        k_vect = [out_file[out_info_dict["k_lines"][i]].split()[2:]
                  for i in range(out_info_dict["k_states"])]
        out_info_dict["k_vect"] = np.array(k_vect)
        out_info_dict["structure"] = structure
        out_info_dict["orbitals"] = find_orbitals_from_statelines(out_info_dict)

        if spin:
            # I had to guess what the ordering of the spin is, because
            # the projwfc.x documentation doesn't say, but looking at the
            # source code I found:
            #
            # DO is=1,nspin
            #   IF (nspin==2) THEN
            #       IF (is==1) filename=trim(filproj)//'.up'
            #       IF (is==2) filename=trim(filproj)//'.down'
            #
            # Which would say that it is reasonable to assume that the
            # spin up states are written first, then spin down
            #
            out_info_dict["spin_down"] = False
            bands_data1, projection_data1 = spin_dependent_subparcer(
                out_info_dict)
            append_nodes_list += [("projections_up", projection_data1),
                                     ("bands_up", bands_data1)]
            out_info_dict["spin_down"] = True
            bands_data2, projection_data2 = spin_dependent_subparcer(
                out_info_dict)
            append_nodes_list += [("projections_down", projection_data2),
                     ("bands_down", bands_data2)]
        else:
            out_info_dict["spin_down"] = False
            bands_data, projection_data = spin_dependent_subparcer(
                out_info_dict)
            append_nodes_list += [("projections", projection_data),
                     ("bands", bands_data)]

        return append_nodes_list

