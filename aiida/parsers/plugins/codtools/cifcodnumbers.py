# -*- coding: utf-8 -*-

from aiida.parsers.plugins.codtools.baseclass import BaseCodtoolsParser
from aiida.orm.calculation.job.codtools.cifcodnumbers import CifcodnumbersCalculation

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


class CifcodnumbersParser(BaseCodtoolsParser):
    """
    Specific parser for the output of cif_cod_numbers script.
    """

    def __init__(self, calc):
        """
        Initialize the instance of CifcodnumbersParser
        """
        # Check for valid input:
        self._supported_calculation_class = CifcodnumbersCalculation
        super(CifcodnumbersParser, self).__init__(calc)

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        from aiida.orm.data.parameter import ParameterData
        import re

        duplicates = []
        if output_path is not None:
            with open(output_path) as f:
                content = f.readlines()
            lines = [x.strip('\n') for x in content]
            for line in lines:
                fields = re.split('\s+', line)
                count = None
                try:
                    count = int(fields[2])
                except ValueError:
                    pass
                if count:
                    duplicates.append({
                        'formula': fields[0],
                        'codid': fields[1],
                        'count': count,
                    })

        errors = []
        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            lines = [x.strip('\n') for x in content]
            self._check_failed(lines)
            errors.extend(lines)

        output_nodes = []
        output_nodes.append(('output',
                             ParameterData(dict={'duplicates': duplicates,
                                                 'errors': errors})))
        return True, output_nodes
