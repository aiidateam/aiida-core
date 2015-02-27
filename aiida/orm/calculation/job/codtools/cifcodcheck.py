# -*- coding: utf-8 -*-
"""
Plugin to create input for scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
import os

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"

class CifcodcheckCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_cod_check from cod-tools package.
    """
    def _init_internal_params(self):
        super(CifcodcheckCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifcodcheck'
