# -*- coding: utf-8 -*-
"""
Plugin to parse outputs from the scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
from aiida.parsers.plugins.codtools.ciffilter import CiffilterParser
from aiida.orm.calculation.codtools.cifcellcontents import CifcellcontentsCalculation
from aiida.orm.data.parameter import ParameterData

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class CifcellcontentsParser(CiffilterParser):
    """
    Specific parser for the output of cif_cell_contents script.
    """
    def _check_calc_compatibility(self,calc):
        from aiida.common.exceptions import ParsingError
        if not isinstance(calc,CifcellcontentsCalculation):
            raise ParsingError("Input calc must be a CifcellcontentsCalculation")

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        import re
        formulae = {}
        if output_path is not None:
            with open(output_path) as f:
                content = f.readlines()
            content = [x.strip('\n') for x in content]
            for line in content:
                datablock,formula = re.split('\s+',line,1)
                formulae[datablock] = formula

        messages = []
        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            messages = [x.strip('\n') for x in content]

        output_nodes = []
        output_nodes.append(('formulae',
                             ParameterData(dict={'formulae':
                                                 formulae})))
        output_nodes.append(('messages',
                             ParameterData(dict={'output_messages':
                                                 messages})))
        return output_nodes
