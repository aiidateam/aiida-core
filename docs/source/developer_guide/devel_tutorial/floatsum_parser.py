# -*- coding: utf-8 -*-

from aiida.orm.calculation.job.floatsum import FloatsumCalculation
from aiida.parsers.parser import Parser
from aiida.parsers.exceptions import OutputParsingError
from aiida.orm.data.float import FloatData
import json

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE " \
                u"(Theory and Simulation of Materials (THEOS) and National Centre " \
                u"for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), " \
                u"Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"

class FloatsumParser(Parser):
    """
    This class is the implementation of the Parser class for Sum.
    """    
    _outarray_name = 'output_data'
    
    def __init__(self,calculation):
        """
        Initialize the instance of SumParser
        """
        super(FloatsumParser, self).__init__(calculation)
        # check for valid input
        if not isinstance(calculation, FloatsumCalculation):
            raise OutputParsingError("Input must calc must be a FloatsumCalculation")
        self._calc = calculation
            
    def parse_with_retrieved(self, retrieved):
        """
        Parses the datafolder, stores results.
        This parser for this simple code does simply store in the DB a node
        representing the file of forces in real space
        """
      
        successful = True
        # select the folder object
        # Check that the retrieved folder is there 
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            self.logger.error("No retrieved folder found")
            return False, ()
        
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
        output_data = FloatData()
        output_data.value = out_dict["sum"]
        linkname = 'output_data'
        new_nodes_list = [(linkname,output_data)]
        
        return successful, new_nodes_list


