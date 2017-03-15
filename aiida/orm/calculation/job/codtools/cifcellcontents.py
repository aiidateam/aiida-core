# -*- coding: utf-8 -*-

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation



class CifcellcontentsCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_cell_contents from cod-tools package.
    """

    def _init_internal_params(self):
        super(CifcellcontentsCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifcellcontents'
        self._default_commandline_params = ['--print-datablock-name']
