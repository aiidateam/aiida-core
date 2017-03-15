# -*- coding: utf-8 -*-

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation



class CifcodnumbersCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_cod_numbers from cod-tools package.
    """

    def _init_internal_params(self):
        super(CifcodnumbersCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifcodnumbers'
