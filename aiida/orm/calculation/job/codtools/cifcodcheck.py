# -*- coding: utf-8 -*-

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


class CifcodcheckCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_cod_check from cod-tools package.
    """

    def _init_internal_params(self):
        super(CifcodcheckCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifcodcheck'
