# -*- coding: utf-8 -*-

from aiida.parsers.plugins.codtools.baseclass import BaseCodtoolsParser
from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


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
