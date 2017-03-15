# -*- coding: utf-8 -*-

from aiida.parsers.plugins.codtools.baseclass import BaseCodtoolsParser
from aiida.orm.calculation.job.codtools.ciffilter import CiffilterCalculation



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
