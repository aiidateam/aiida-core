# -*- coding: utf-8 -*-

from aiida.parsers.plugins.codtools.baseclass import BaseCodtoolsParser
from aiida.orm.calculation.job.codtools.cifsplitprimitive import CifsplitprimitiveCalculation

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

class CifsplitprimitiveParser(BaseCodtoolsParser):
    """
    Specific parser for the output of cif_split_primitive script.
    """
    def __init__(self,calc):
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
