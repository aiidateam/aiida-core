# -*- coding: utf-8 -*-
from aiida.parsers.plugins.nwchem import BasenwcParser
from aiida.orm.calculation.job.nwchem.nwcpymatgen import NwcpymatgenCalculation
from aiida.orm.data.parameter import ParameterData

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."

class NwcpymatgenParser(BasenwcParser):
    """
    Parser for the output of NWChem, using pymatgen.
    """
    def __init__(self, calc):
        """
        Initialize the instance of NwcpymatgenParser
        """
        # check for valid input
        self._check_calc_compatibility(calc)
        super(NwcpymatgenParser, self).__init__(calc)

    def _check_calc_compatibility(self, calc):
        from aiida.common.exceptions import ParsingError
        if not isinstance(calc, NwcpymatgenCalculation):
            raise ParsingError("Input calc must be a NwcpymatgenCalculation")

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        from pymatgen.io.nwchemio import NwOutput
        from aiida.orm.data.structure import StructureData
        from aiida.orm.data.array.trajectory import TrajectoryData

        ret_dict = []
        nwo = NwOutput(output_path)
        for out in nwo.data:
            molecules = out.pop('molecules', None)
            structures = out.pop('structures', None)
            if molecules:
                structlist = [StructureData(pymatgen_molecule=m)
                              for m in molecules]
                ret_dict.append(('trajectory',
                                 TrajectoryData(structurelist=structlist)))
            if structures:
                structlist = [StructureData(pymatgen_structure=s)
                              for s in structures]
                ret_dict.append(('trajectory',
                                 TrajectoryData(structurelist=structlist)))
            ret_dict.append(('output', ParameterData(dict=out)))

        # Since ParameterData rewrites it's properties (using _set_attr())
        # with keys from the supplied dictionary, ``source`` has to be
        # moved to another key. See issue #9 for details:
        # (https://bitbucket.org/epfl_theos/aiida_epfl/issues/9)
        nwo.job_info['program_source'] = nwo.job_info.pop('source', None)
        ret_dict.append(('job_info', ParameterData(dict=nwo.job_info)))
        
        return ret_dict
