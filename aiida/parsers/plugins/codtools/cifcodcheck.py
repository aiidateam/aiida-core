# -*- coding: utf-8 -*-

from aiida.parsers.plugins.codtools.baseclass import BaseCodtoolsParser
from aiida.orm.calculation.job.codtools.cifcodcheck import CifcodcheckCalculation



class CifcodcheckParser(BaseCodtoolsParser):
    """
    Specific parser for the output of cif_cod_check script.
    """

    def __init__(self, calc):
        """
        Initialize the instance of CifcodcheckParser
        """
        # Check for valid input:
        self._supported_calculation_class = CifcodcheckCalculation
        super(CifcodcheckParser, self).__init__(calc)

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        from aiida.orm.data.parameter import ParameterData
        import re

        messages = []
        if output_path is not None:
            with open(output_path) as f:
                content = f.readlines()
            lines = [x.strip('\n') for x in content]
            if re.search(' OK$', lines[0]) is not None:
                lines.pop(0)
            messages.extend(lines)

        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            lines = [x.strip('\n') for x in content]
            messages.extend(lines)
            self._check_failed(messages)

        output_nodes = []
        output_nodes.append(('messages',
                             ParameterData(dict={'output_messages':
                                                     messages})))
        return True, output_nodes
