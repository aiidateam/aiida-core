# -*- coding: utf-8 -*-
from aiida.orm.calculation.quantumespresso.q2r import Q2rCalculation
from aiida.parsers.plugins.quantumespresso.raw_parser_ph import parse_raw_ph_output
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.folder import FolderData
from aiida.parsers.parser import Parser
from aiida.common.datastructures import calc_states
from aiida.parsers.plugins.quantumespresso import QEOutputParsingError
from aiida.common.exceptions import UniquenessError
from aiida.orm.data.singlefile import SinglefileData

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class Q2rParser(Parser):
    """
    This class is the implementation of the Parser class for PHonon.
    """
    
    _name_matrix = 'output_forces'

    def __init__(self,calculation):
        """
        Initialize the instance of PwParser
        """
        # check for valid input
        if not isinstance(calculation,Q2rCalculation):
            raise QEOutputParsingError("Input must calc must be a Q2rCalculation")
        
        self._calc = calculation
            
    def parse_from_calc(self):
        """
        Parses the datafolder, stores results.
        This parser for this simple code does simply store in the DB a node
        representing the file of forces in real space
        """
        from aiida.common.exceptions import InvalidOperation
        import os
        
        # check if I'm not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )
        
        # load all outputs of type FolderData
        calc_outputs = self._calc.get_outputs(type=FolderData,also_labels=True)
        # look for retrieved files only
        retrieved_files = [i[1] for i in calc_outputs if i[0]==self._calc.get_linkname_retrieved()]
        if len(retrieved_files)!=1:
            raise UniquenessError("Output folder should be found once, "
                                  "found it instead {} times"
                                  .format(len(retrieved_files)) )
        # select the folder object
        out_folder = calc_outputs[0][1]
        
        # check what is inside the folder
        list_of_files = out_folder.get_path_list()
        # at least the stdout should exist
        if not self._calc.OUTPUT_FILE_NAME in list_of_files:
            #TODO add log and set calculation to failed
            raise QEOutputParsingError("Standard output not found")

        # suppose at the start that the job is successful
        successful = True

        # check that the file has finished (i.e. JOB DONE is inside the file)
        filpath = os.path.join(out_folder.get_abs_path('.'),
                               self._calc.OUTPUT_FILE_NAME)
        with open(filpath,'r') as fil:
            lines = fil.read()
        if "JOB DONE" not in lines:
            successful = False
        
        # check that the real space force constant matrix is present
        the_outputs = self._calc.get_outputs(also_labels=True)
        the_files = [i[1] for i in the_outputs if 
                     i[0]==self._calc.get_linkname_force_matrix()]
        
        if len(the_files) != 1:
            successful = False
            # add log for failure
        
        return successful

