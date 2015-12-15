# -*- coding: utf-8 -*-

from aiida.parsers.plugins.codtools.baseclass import BaseCodtoolsParser
from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi, Martin Uhrin"


class CiffilterParser(BaseCodtoolsParser):
    """
    Parser for the output of filter scripts from cod-tools package.
    """

    def __init__(self, calc):
        """
        Initialize the instance of CiffilterParser
        """
        self._supported_calculation_class = CiffilterCalculation
        super(CiffilterParser, self).__init__(calc)
