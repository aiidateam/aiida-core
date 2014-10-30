# -*- coding: utf-8 -*-
"""
Plugin to parse outputs from the scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
from aiida.parsers.parser import Parser
from aiida.orm.calculation.codtools import CodtoolsCalculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import calc_states

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class CodtoolsParser(Parser):
    """
    Base parser for scripts from 'cod-tools' package.
    """

    def __init__(self,calc):
        """
        Initialize the instance of CodtoolsParser
        """
        # check for valid input
        if not isinstance(calc, CodtoolsCalculation):
            raise ParsingError("Input must calc must be a CodtoolsCalculation")
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

        output_path = None
        error_path  = None
        try:
            output_path, error_path = self._fetch_output_files()
        except InvalidOperation:
            raise
        except IOError as e:
            parserlogger.error(e.message)
            return False, ()

        if output_path is None and error_path is None:
            parserlogger.error("No output files found",
                               extra=logger_extra)
            return False, ()

        cif = None
        if output_path is not None and os.path.getsize(output_path) > 0:
            cif = CifData(file=output_path)

        messages = None
        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            messages = [x.strip('\n') for x in content]

        output_nodes = []
        if cif is not None:
            output_nodes.append(('cif',cif))
        if messages is not None:
            output_nodes.append(('messages',
                                 ParameterData(dict={'output_messages':
                                                     messages})))
        return True, output_nodes

    def _fetch_output_files(self):
        """
        Checks the output folder for standard output and standard error
        files, returns their absolute paths on success.
        """
        from aiida.common.exceptions import InvalidOperation
        import os

        # check in order not to overwrite anything
        state = self._calc.get_state()
        if state != calc_states.PARSING:
            raise InvalidOperation("Calculation not in {} state"
                                   .format(calc_states.PARSING) )

        # select the folder object
        out_folder = self._calc.get_retrieved_node()
        if out_folder is None:
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
