# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.calculation.job.aseplugins.ase import AseCalculation
from aiida.orm.data.folder import FolderData
from aiida.parsers.parser import Parser
from aiida.common.datastructures import calc_states
from aiida.parsers.exceptions import OutputParsingError
from aiida.common.exceptions import UniquenessError
import numpy
from aiida.orm.data.array import ArrayData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
import json


class AseParser(Parser):
    """
    This class is the implementation of the Parser class for Ase calculators.
    """

    _outarray_name = 'output_array'
    _outdict_name = 'output_parameters'
    _outstruc_name = 'output_structure'

    def __init__(self,calculation):
        """
        Initialize the instance of AseParser
        """
        # check for valid input
        if not isinstance(calculation,AseCalculation):
            raise OutputParsingError("Input calculation must be a AseCalculation")
        self._calc = calculation

    def parse_from_calc(self):
        """
        Parses the datafolder, stores results.
        This parser for this simple code does simply store in the DB a node
        representing the file of forces in real space
        """
        from aiida.common.exceptions import InvalidOperation
        from aiida.common import aiidalogger
        from aiida.djsite.utils import get_dblogger_extra

        import ase, ase.io

        parserlogger = aiidalogger.getChild('aseparser')
        logger_extra = get_dblogger_extra(self._calc)

        # suppose at the start that the job is successful
        successful = True

        # check that calculation is in the right state
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )

        # select the folder object
        out_folder = self._calc.get_retrieved_node()

        # check what is inside the folder
        list_of_files = out_folder.get_folder_list()

        # at least the stdout should exist
        if not self._calc._OUTPUT_FILE_NAME in list_of_files:
            successful = False
            parserlogger.error("Standard output not found",extra=logger_extra)
            return successful,()

        # output structure
        has_out_atoms = True if self._calc._output_aseatoms in list_of_files else False
        if has_out_atoms:
            out_atoms = ase.io.read( out_folder.get_abs_path( self._calc._output_aseatoms ) )
            out_structure = StructureData().set_ase(out_atoms)

        # load the results dictionary
        json_outfile = out_folder.get_abs_path( self._calc._OUTPUT_FILE_NAME )
        with open(json_outfile,'r') as f:
            json_params = json.load(f)

        # extract arrays from json_params
        dictionary_array = {}
        for k,v in list(json_params.iteritems()):
            if isinstance(v, (list,tuple)):
                dictionary_array[k] = json_params.pop(k)

        # look at warnings
        warnings = []
        with open(out_folder.get_abs_path( self._calc._SCHED_ERROR_FILE )) as f:
            errors = f.read()
        if errors:
            warnings = [errors]
        json_params['warnings'] = warnings

        # save the outputs
        new_nodes_list= []

        # save the arrays
        if dictionary_array:
            array_data = ArrayData()
            for k,v in dictionary_array.iteritems():
                array_data.set_array(k,numpy.array(v))
            new_nodes_list.append( (self._outarray_name, array_data) )

        # save the parameters
        if json_params:
            parameter_data = ParameterData( dict=json_params )
            new_nodes_list.append( (self._outdict_name, parameter_data) )

        if has_out_atoms:
            structure_data = StructureData()
            new_nodes_list.append( (self._outstruc_name, structure_data) )

        return successful,new_nodes_list

