# -*- coding: utf-8 -*-

from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"


class CifcodnumbersCalculation(CiffilterCalculation):
    """
    Specific input plugin for cif_cod_numbers from cod-tools package.
    """

    def _init_internal_params(self):
        super(CifcodnumbersCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifcodnumbers'
