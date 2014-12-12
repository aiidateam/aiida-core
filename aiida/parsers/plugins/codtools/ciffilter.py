# -*- coding: utf-8 -*-
"""
Plugin to parse outputs from the scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
from aiida.parsers.parser import Parser
from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import calc_states

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class CiffilterParser(Parser):
    """
    Parser for the output of filter scripts from cod-tools package.
    """
    def __init__(self,calc):
        """
        Initialize the instance of CiffilterParser
        """
        # check for valid input
        self._check_calc_compatibility(calc)
        super(CiffilterParser, self).__init__(calc)

    def _check_calc_compatibility(self,calc):
        from aiida.common.exceptions import ParsingError
        if not isinstance(calc,CiffilterCalculation):
            raise ParsingError("Input calc must be a CiffilterCalculation")

    def parse_with_retrieved(self,retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """       
        from aiida.common.exceptions import InvalidOperation
        import os

        output_path = None
        error_path  = None
        try:
            output_path, error_path = self._fetch_output_files(retrieved)
        except InvalidOperation:
            raise
        except IOError as e:
            self.logger.error(e.message)
            return False, ()

        if output_path is None and error_path is None:
            self.logger.error("No output files found")
            return False, ()

        return True, self._get_output_nodes(output_path, error_path)

    def _fetch_output_files(self, retrieved):
        """
        Checks the output folder for standard output and standard error
        files, returns their absolute paths on success.
        
        :param retrieved: A dictionary of retrieved nodes, as obtained from the
          parser.
        """
        from aiida.common.exceptions import InvalidOperation
        import os

        # check in order not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )

        # Check that the retrieved folder is there 
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            raise IOError("No retrieved folder found")        

        list_of_files = out_folder.get_folder_list()

        output_path = None
        error_path  = None

        if self._calc._DEFAULT_OUTPUT_FILE in list_of_files:
            output_path = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_OUTPUT_FILE )
        if self._calc._DEFAULT_ERROR_FILE in list_of_files:
            error_path  = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_ERROR_FILE )

        return output_path, error_path

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        import os

        cif = None
        if output_path is not None and os.path.getsize(output_path) > 0:
            cif = CifData(file=output_path)

        messages = []
        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            messages = [x.strip('\n') for x in content]

        output_nodes = []
        if cif is not None:
            output_nodes.append(('cif',cif))
        output_nodes.append(('messages',
                             ParameterData(dict={'output_messages':
                                                 messages})))
        return output_nodes
