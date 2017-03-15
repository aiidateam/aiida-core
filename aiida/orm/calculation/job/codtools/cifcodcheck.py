# -*- coding: utf-8 -*-

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation



class CifcodcheckCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_cod_check from cod-tools package.
    """

    def _init_internal_params(self):
        super(CifcodcheckCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifcodcheck'
