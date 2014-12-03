from aiida.orm.calculation.sum import SumCalculation
from aiida.parsers.parser import Parser
#from aiida.common.datastructures import calc_states
from aiida.parsers.exceptions import OutputParsingError
import json
from aiida.orm.data.parameter import ParameterData

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class SumParser(Parser):
    """
    This class is the implementation of the Parser class for Sum.
    """    
    _outarray_name = 'output_data'
    
    def __init__(self,calculation):
        """
        Initialize the instance of SumParser
        """
        # check for valid input
        if not isinstance(calculation,SumCalculation):
            raise OutputParsingError("Input must calc must be a SumCalculation")
        self._calc = calculation
            
    def parse_from_calc(self):
        """
        Parses the datafolder, stores results.
        This parser for this simple code does simply store in the DB a node
        representing the file of forces in real space
        """
      
        successful = True
        # select the folder object
        out_folder = self._calc.get_retrieved_node()
        
        # check what is inside the folder
        list_of_files = out_folder.get_folder_list()
        # at least the stdout should exist
        if not self._calc._OUTPUT_FILE_NAME in list_of_files:
            successful = False
            self.logger.error("Output json not found")
            return successful,()
        
        try:
            with open( out_folder.get_abs_path(self._calc._OUTPUT_FILE_NAME) ) as f:
                out_dict = json.load(f)
        except ValueError:
            successful=False
            self.logger.error("Error parsing the output json")
            return successful,()
        
        # save the arrays
        output_data = ParameterData(dict=out_dict)
        linkname = 'output_data'
        new_nodes_list = [(linkname,output_data)]
        
        return successful,new_nodes_list

        
