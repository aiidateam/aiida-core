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
from aiida.orm.calculation.job.sum import SumCalculation
from aiida.parsers.parser import Parser
from aiida.parsers.exceptions import OutputParsingError
from aiida.orm.nodes.data.dict import Dict

import json

class SumParser(Parser):
    """
    This class is the implementation of the Parser class for Sum.
    """    
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
            out_folder = retrieved[self._calc.link_label_retrieved]
        except KeyError:
            self.logger.error("No retrieved folder found")
            return False, ()
        
        # check what is inside the folder
        list_of_files = out_folder.get_folder_list()
        # at least the stdout should exist
        if self._calc._DEFAULT_OUTPUT_FILE not in list_of_files:
            successful = False
            self.logger.error("Output json not found")
            return successful,()
        
        try:
            with open( out_folder.get_abs_path(self._calc._DEFAULT_OUTPUT_FILE) ) as f:
                out_dict = json.load(f)
        except ValueError:
            successful=False
            self.logger.error("Error parsing the output json")
            return successful,()
        
        output_data = Dict(dict=out_dict)
        link_name = self.get_linkname_outparams()
        new_nodes_list = [(link_name, output_data)]
                    
        return successful,new_nodes_list


