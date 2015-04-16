# -*- coding: utf-8 -*-
"""
Plugin to parse outputs from the scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
from aiida.parsers.plugins.codtools.ciffilter import CiffilterParser
from aiida.orm.calculation.job.codtools.cifcoddeposit import CifcoddepositCalculation
from aiida.orm.data.parameter import ParameterData

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.4.1"

class CifcoddepositParser(CiffilterParser):
    """
    Specific parser for the output of cif_cod_deposit script.
    """
    def _check_calc_compatibility(self,calc):
        from aiida.common.exceptions import ParsingError
        if not isinstance(calc,CifcoddepositCalculation):
            raise ParsingError("Input calc must be a CifcoddepositCalculation")

    def _get_output_nodes(self, output_path, error_path):
        """
        Extracts output nodes from the standard output and standard error
        files.
        """

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
