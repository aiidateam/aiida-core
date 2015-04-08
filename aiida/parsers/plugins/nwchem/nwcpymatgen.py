# -*- coding: utf-8 -*-
from aiida.parsers.plugins.nwchem import BasenwcParser
from aiida.orm.calculation.job.nwchem.nwcpymatgen import NwcpymatgenCalculation
from aiida.orm.data.parameter import ParameterData

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

class NwcpymatgenParser(BasenwcParser):
    """
    Parser for the output of NWChem, using pymatgen.
    """
    def __init__(self,calc):
        """
        Initialize the instance of NwcpymatgenParser
        """
        # check for valid input
        self._check_calc_compatibility(calc)
        super(NwcpymatgenParser, self).__init__(calc)

    def _check_calc_compatibility(self,calc):
        from aiida.common.exceptions import ParsingError
        if not isinstance(calc,NwcpymatgenCalculation):
            raise ParsingError("Input calc must be a NwcpymatgenCalculation")

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        from pymatgen.io.nwchemio import NwOutput

        ret_dict = []
        nwo = NwOutput(output_path)
        for out in nwo.data:
            out.pop('molecules',None)  # TODO: implement extraction of
            out.pop('structures',None) # Structure- and TrajectoryData
            ret_dict.append(('output',ParameterData(dict=out)))
        ret_dict.append(('job_info',ParameterData(dict=nwo.job_info)))
        
        return ret_dict
