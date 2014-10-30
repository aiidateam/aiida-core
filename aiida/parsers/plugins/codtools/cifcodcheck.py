# -*- coding: utf-8 -*-
"""
Plugin to parse outputs from the scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
from aiida.parsers.plugins.codtools import CodtoolsParser
from aiida.orm.calculation.codtools import CodtoolsCalculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData
from aiida.common.datastructures import calc_states

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class CifcodcheckParser(CodtoolsParser):
    """
    Specific parser for the output of cif_cod_tools script.
    """
    def parse_from_calc(self):
        """
        Parses the datafolder, stores results.
        Main functionality of the class.
        """
        from aiida.common.exceptions import InvalidOperation
        import os
        import re

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

        messages = []
        if output_path is not None:
            with open(output_path) as f:
                content = f.readlines()
            lines = [x.strip('\n') for x in content]
            if re.search( ' OK$', lines[0] ) is not None:
                lines.pop(0)
            messages.extend( lines )

        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            lines = [x.strip('\n') for x in content]
            messages.extend( lines )

        output_nodes = []
        output_nodes.append(('messages',
                             ParameterData(dict={'output_messages':
                                                 messages})))
        return True, output_nodes
