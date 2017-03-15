# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation



class CifcellcontentsCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_cell_contents from cod-tools package.
    """

    def _init_internal_params(self):
        super(CifcellcontentsCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifcellcontents'
        self._default_commandline_params = ['--print-datablock-name']
