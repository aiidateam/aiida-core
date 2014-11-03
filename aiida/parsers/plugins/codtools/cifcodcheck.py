# -*- coding: utf-8 -*-
"""
Plugin to parse outputs from the scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
from aiida.parsers.plugins.codtools import CodtoolsParser
from aiida.orm.data.parameter import ParameterData

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class CifcodcheckParser(CodtoolsParser):
    """
    Specific parser for the output of cif_cod_tools script.
    """
    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        import re

        messages = []
        if output_path is not None:
            with open(output_path) as f:
                content = f.readlines()
            lines = [x.strip('\n') for x in content]
            if re.search( ' OK$', lines[0] ) is not None:
                lines.pop(0)
            messages.extend(lines)

        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            lines = [x.strip('\n') for x in content]
            messages.extend(lines)

        output_nodes = []
        output_nodes.append(('messages',
                             ParameterData(dict={'output_messages':
                                                 messages})))
        return output_nodes
