# -*- coding: utf-8 -*-

from aiida.parsers.plugins.codtools.ciffilter import CiffilterParser
from aiida.orm.calculation.job.codtools.cifcoddeposit import CifcoddepositCalculation

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Giovanni Pizzi"

class CifcoddepositParser(CiffilterParser):
    """
    Specific parser for the output of cif_cod_deposit script.
    """
    def __init__(self,calc):
        """
        Initialize the instance of CiffilterParser
        """
        self._supported_calculation_class = CifcoddepositCalculation
        super(CifcoddepositParser, self).__init__(calc)

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """
        from aiida.orm.data.parameter import ParameterData

        status = 'unknown'
        messages = []

        if output_path is not None:
            content = None
            with open(output_path) as f:
                content = f.read()
            status,message = CifcoddepositParser._deposit_result(content)
            messages.extend(message.split("\n"))

        if error_path is not None:
            with open(error_path) as f:
                content = f.readlines()
            lines = [x.strip('\n') for x in content]
            messages.extend(lines)

        output_nodes = []
        output_nodes.append(('messages',
                             ParameterData(dict={'output_messages':
                                                 messages,
                                                 'status': status})))
        return output_nodes

    @classmethod
    def _deposit_result(cls,output):
        import re
        status  = 'unknown'
        message = ''

        output = re.sub('^[^:]*cif-deposit\.pl:\s+','',output)
        output = re.sub('\n$','',output)

        dep = re.search('^(structures .+ were successfully deposited '
                        'into .?COD)$', output)
        dup = re.search('^(the following structures seem to be already '
                        'in .?COD):', output, re.IGNORECASE)
        red = re.search('^(redeposition of structure is unnecessary)',
                        output)
        lgn = re.search('<p class="error"[^>]*>[^:]+: (.*)',
                        output, re.IGNORECASE)

        if   dep is not None:
            status  = 'success'
            message = dep.group(1)
        elif dup is not None:
            status = 'duplicate'
            message = dup.group(1)
        elif red is not None:
            status = 'unchanged'
            message = dup.group(1)
        elif lgn is not None:
            status = 'error'
            message = lgn.group(1)
        else:
            status = 'error'
            message = output

        return status,message
