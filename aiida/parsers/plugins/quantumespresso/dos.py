# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.calculation.job.quantumespresso.dos import DosCalculation
from aiida.orm.data.parameter import ParameterData
from aiida.parsers.parser import Parser
from aiida.parsers.plugins.quantumespresso import QEOutputParsingError
from aiida.parsers.plugins.quantumespresso import parse_raw_out_basic
from aiida.orm.data.array.xy import XyData
import numpy as np
from aiida.common.exceptions import InvalidOperation
from aiida.common.datastructures import calc_states

class DosParser(Parser):
    """
    This class is the implementation of the Parser class for Dos.
    """
    _dos_name = 'output_dos'
    _units_name = 'output_units'

    def __init__(self, calculation):
        """
        Initialize the instance of DosParser
        """
        # check for valid input
        if not isinstance(calculation, DosCalculation):
            raise QEOutputParsingError("Input calc must be a DosCalculation")

        self._calc = calculation

        super(DosParser, self).__init__(calculation)

    def get_linkname_dos(self):
        """
        Returns the name of the link of dos
        """
        return self._dos_name

    def get_linkname_units(self):
        """
        Returns the name of the link of units
        """
        return self._units_name

    def parse_with_retrieved(self, retrieved):
        """
        Parses the datafolder, stores results.
        Retrieves dos output, and some basic information from the
        out_file, such as warnings and wall_time
        """

        # suppose at the start that the job is successful
        successful = True
        new_nodes_list = []

        # check if I'm not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
           raise InvalidOperation("Calculation not in {} state")

        try:
            out_folder = self._calc.get_retrieved_node()
        except KeyError:
            self.logger.error("No retrieved folder found")
            return successful, new_nodes_list

        # Read standard out
        try:
            filpath = out_folder.get_abs_path(self._calc._OUTPUT_FILE_NAME)
            with open(filpath, 'r') as fil:
                    out_file = fil.readlines()
        except OSError:
            self.logger.error("Standard output file could not be found.")
            successful = False
            return successful, new_nodes_list

        successful = False
        for i in range(len(out_file)):
            line = out_file[-i]
            if "JOB DONE" in line:
                successful = True
                break
        if not successful:
            self.logger.error("Computation did not finish properly")
            return successful, new_nodes_list

        # check that the dos file is present, if it is, read it
        try:
            dos_path = out_folder.get_abs_path(self._calc._DOS_FILENAME)
            with open(dos_path, 'r') as fil:
                    dos_file = fil.readlines()
        except OSError:
            successful = False
            self.logger.error("Dos output file could not found")
            return successful, new_nodes_list

        # end of initial checks

        array_names = [[], []]
        array_units = [[], []]
        array_names[0] = ['dos_energy', 'dos',
                          'integrated_dos']  # When spin is not displayed
        array_names[1] = ['dos_energy', 'dos_spin_up', 'dos_spin_down',
                          'integrated_dos']  # When spin is displayed
        array_units[0] = ['eV', 'states/eV',
                          'states']  # When spin is not displayed
        array_units[1] = ['eV', 'states/eV', 'states/eV',
                          'states']  # When spin is displayed

        # grabs parsed data from aiida.dos
        array_data, spin = parse_raw_dos(dos_file, array_names, array_units)
        
        energy_units = 'eV'
        dos_units = 'states/eV'
        int_dos_units = 'states'        
        xy_data = XyData()
        xy_data.set_x(array_data["dos_energy"],"dos_energy", energy_units)
        y_arrays = []
        y_names = []
        y_units = []
        y_arrays  += [array_data["integrated_dos"]]
        y_names += ["integrated_dos"]
        y_units += ["states"]
        if spin:
            y_arrays  += [array_data["dos_spin_up"]]
            y_arrays  += [array_data["dos_spin_down"]]
            y_names += ["dos_spin_up"]
            y_names += ["dos_spin_down"]
            y_units += ["states/eV"]*2
        else:
            y_arrays  += [array_data["dos"]]
            y_names += ["dos"]
            y_units += ["states/eV"]
        xy_data.set_y(y_arrays,y_names,y_units)

        # grabs the parsed data from aiida.out
        parsed_data = parse_raw_out_basic(out_file, "DOS")
        output_params = ParameterData(dict=parsed_data)
        # Adds warnings
        for message in parsed_data['warnings']:
            self.logger.error(message)
        # Create New Nodes List
        new_nodes_list = [(self.get_linkname_outparams(), output_params),
                          (self.get_linkname_dos(), xy_data)]
        return successful,new_nodes_list



def parse_raw_dos(dos_file, array_names, array_units):
    """
    This function takes as input the dos_file as a list of filelines along
    with information on how to give labels and units to the parsed data
    
    :param dos_file: dos file lines in the form of a list
    :type dos_file: list
    :param array_names: list of all array names, note that array_names[0]
                        is for the case with non spin-polarized calculations
                        and array_names[1] is for the case with spin-polarized
                        calculation
    :type array_names: list
    :param array_units: list of all array units, note that array_units[0] is
                        for the case with non spin-polarized calculations and
                        array_units[1] is for the case with spin-polarized
                        calculation
    :type array_units: list
    
    :return array_data: narray, a dictionary for ArrayData type, which contains
                        all parsed dos output along with labels and units
    :return spin: boolean, indicates whether the parsed results are spin
                  polarized 
    """

    dos_header = dos_file[0]
    try:
        dos_data = np.genfromtxt(dos_file)
    except ValueError:
        raise QEOutputParsingError('dosfile could not be loaded '
        ' using genfromtxt')
    if len(dos_data) == 0:
        raise QEOutputParsingError("Dos file is empty.")
    if np.isnan(dos_data).any():
        raise QEOutputParsingError("Dos file contains non-numeric elements.")

    # Checks the number of columns, essentially to see whether spin was used
    if len(dos_data[0]) == 3:
        # spin is not used
        array_names = array_names[0]
        array_units = array_units[0]
        spin = False
    elif len(dos_data[0]) == 4:
        # spin is used
        array_names = array_names[1]
        array_units = array_units[1]
        spin = True 
    else:
        raise QEOutputParsingError("Dos file in format that the parser is not "
                                   "designed to handle.")

    i = 0
    array_data = {}
    array_data['header'] = np.array(dos_header)
    while i < len(array_names):
        array_data[array_names[i]] = dos_data[:, i]
        array_data[array_names[i]+'_units'] = np.array(array_units[i])
        i += 1
    return array_data,spin
