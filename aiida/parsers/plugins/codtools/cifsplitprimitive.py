# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.parsers.plugins.codtools.baseclass import BaseCodtoolsParser
from aiida.orm.calculation.job.codtools.cifsplitprimitive import CifsplitprimitiveCalculation



class CifsplitprimitiveParser(BaseCodtoolsParser):
    """
    Specific parser for the output of cif_split_primitive script.
    """

    def __init__(self, calc):
        """
        Initialize the instance of CifsplitprimitiveParser
        """
        # Check for valid input:
        self._supported_calculation_class = CifsplitprimitiveCalculation
        super(CifsplitprimitiveParser, self).__init__(calc)

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        from aiida.orm.data.cif import CifData
        from aiida.orm.data.parameter import ParameterData
        import os

        out_folder = self._calc.get_retrieved_node()

        output_nodes = []
        success = False
        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            content = [x.strip('\n') for x in content]
            self._check_failed(content)
            if len(content) > 0:
                success = True
            for filename in content:
                path = os.path.join(out_folder.get_abs_path('.'), filename)
                output_nodes.append(('cif', CifData(file=path)))

        if output_path is not None:
            with open(output_path) as f:
                content = f.readlines()
            content = [x.strip('\n') for x in content]
            output_nodes.append(('messages',
                                 ParameterData(dict={'output_messages':
                                                         content})))

        return success, output_nodes
