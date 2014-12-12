# -*- coding: utf-8 -*-
"""
Plugin to parse outputs from the scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
from aiida.parsers.plugins.codtools.ciffilter import CiffilterParser
from aiida.orm.calculation.job.codtools.cifsplitprimitive import CifsplitprimitiveCalculation
from aiida.orm.data.cif import CifData
from aiida.orm.data.parameter import ParameterData

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class CifsplitprimitiveParser(CiffilterParser):
    """
    Specific parser for the output of cif_split_primitive script.
    """
    def _check_calc_compatibility(self,calc):
        from aiida.common.exceptions import ParsingError
        if not isinstance(calc,CifsplitprimitiveCalculation):
            raise ParsingError("Input calc must be a CifsplitprimitiveCalculation")

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        import os

        out_folder = self._calc.get_retrieved_node()

        output_nodes = []
        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            content = [x.strip('\n') for x in content]
            for filename in content:
                path = os.path.join( out_folder.get_abs_path('.'), filename )
                output_nodes.append(('cif', CifData(file=path)))

        if output_path is not None:
            with open(output_path) as f:
                content = f.readlines()
            content = [x.strip('\n') for x in content]
            output_nodes.append(('messages',
                                  ParameterData(dict={'output_messages':
                                                      content})))

        return output_nodes
