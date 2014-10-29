# -*- coding: utf-8 -*-
"""
Plugin to parse outputs from the scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
from aiida.parsers.parser import Parser
from aiida.orm.calculation.codtools.ciffilter import CiffilterCalculation
from aiida.common.datastructures import calc_states

class CodtoolsParser(Parser):
    """
    Base parser for scripts from 'cod-tools' package.
    """

    def __init__(self,calc):
        """
        Initialize the instance of CodtoolsParser
        """
        # check for valid input
        if not isinstance(calc, CiffilterCalculation):
            raise ParsingError("Input must calc must be a CiffilterCalculation")
        super(CodtoolsParser, self).__init__(calc)

    def parse_from_calc(self):
        """
        Parses the datafolder, stores results.
        Main functionality of the class.
        """
        from aiida.common.exceptions import InvalidOperation
        import os

        # load the error logger
        from aiida.common import aiidalogger
        from aiida.djsite.utils import get_dblogger_extra
        parserlogger = aiidalogger.getChild('pwparser')
        logger_extra = get_dblogger_extra(self._calc)

        # check in order not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )

        # select the folder object
        out_folder = self._calc.get_retrieved_node()
        if out_folder is None:
            parserlogger.error("No retrieved folder found")
            return False, ()

        # check what is inside the folder
        list_of_files = out_folder.get_folder_list()
        if not self._calc._DEFAULT_OUTPUT_FILE in list_of_files and \
           not self._calc._DEFAULT_ERROR_FILE  in list_of_files:
            parserlogger.error("No output files found",
                               extra=logger_extra)
            return False, ()

        output_path = os.path.join( out_folder.get_abs_path('.'),
                                    self._calc._DEFAULT_OUTPUT_FILE )
        error_path  = os.path.join( out_folder.get_abs_path('.'),
                                    self._calc._DEFAULT_ERROR_FILE )

        cif = None
        if self._calc._DEFAULT_OUTPUT_FILE in list_of_files and \
            os.path.getsize(output_path) > 0:
            cif = CifData(file=output_path)

        messages = None
        if self._calc._DEFAULT_ERROR_FILE in list_of_files:
            with open(error_path) as f:
                content = f.readlines()
            messages = [x.strip('\n') for x in content]
        p = ParameterData(dict={'output_messages': messages})

        output_nodes = []
        if cif is not None:
            output_nodes.append(('cif',cif))
        if messages is not None:
            output_nodes.append(('messages',messages))
        return True, output_nodes
