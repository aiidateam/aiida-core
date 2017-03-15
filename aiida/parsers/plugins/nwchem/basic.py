# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.parsers.plugins.nwchem import BasenwcParser
from aiida.orm.calculation.job.nwchem.basic import BasicCalculation
from aiida.orm.data.parameter import ParameterData


class BasicParser(BasenwcParser):
    """
    Parser for the output of nwchem.
    """
    def __init__(self,calc):
        """
        Initialize the instance of BasicParser
        """
        # check for valid input
        self._check_calc_compatibility(calc)
        super(BasicParser, self).__init__(calc)

    def _check_calc_compatibility(self,calc):
        from aiida.common.exceptions import ParsingError
        if not isinstance(calc,BasicCalculation):
            raise ParsingError("Input calc must be a BasicCalculation")

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        from aiida.orm.data.array.trajectory import TrajectoryData
        import re

        state = None
        step = None
        scale = None
        with open(output_path) as f:
            lines = [x.strip('\n') for x in f.readlines()]

        result_dict = dict()
        trajectory = None
        for line in lines:
            if state is None and re.match('^\s*NWChem SCF Module\s*$',line):
                state = 'nwchem-scf-module'
                continue
            if state is None and re.match('^\s*NWChem Geometry Optimization\s*$',line):
                state = 'nwchem-geometry-optimisation'
                trajectory = TrajectoryData()
                continue
            if state == 'nwchem-scf-module' and re.match('^\s*Final RHF \s*results\s*$',line):
                state = 'final-rhf-results'
                continue
            if re.match('^\s*\-*\s*$',line):
                continue
            if state == 'final-rhf-results':
                result = re.match('^\s*([^=]+?)\s*=\s*([\-\d\.]+)$',line)
                if result:
                    key = re.sub('[^a-zA-Z0-9]+', '_', result.group(1).lower())
                    result_dict[key] = result.group(2)
                else:
                    state = 'nwchem-scf-module'
            if state == 'nwchem-geometry-optimisation' and re.match('^\s*Step\s+\d+\s*$',line):
                result = re.match('^\s*Step\s+(\d+)\s*$',line)
                step = result.group(1)
                continue
            if state == 'nwchem-geometry-optimisation' and \
                re.match('^\s*Output coordinates in a.u.',line):
                state = 'nwchem-geometry-optimisation-coordinates'
                result = re.match('scale by \s(*[\-\d\.]+)',line)
                scale = result.group(1)
                continue
        return [('parameters', ParameterData(dict=result_dict))]
