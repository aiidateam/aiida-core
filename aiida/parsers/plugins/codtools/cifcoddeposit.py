# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.parsers.plugins.codtools.ciffilter import CiffilterParser
from aiida.orm.calculation.job.codtools.cifcoddeposit import CifcoddepositCalculation
from aiida.common.extendeddicts import Enumerate



class CoddepositionState(Enumerate):
    pass


cod_deposition_states = CoddepositionState((
    'SUCCESS',  # Structures are deposited/updated successfully
    'DUPLICATE',  # Structures are found to be already in the database
    'UNCHANGED',  # Structures are not updated (nothing to update)
    'INPUTERROR',  # Other error caused by user's input
    'SERVERERROR',  # Internal server error
    'UNKNOWN'  # Unknown state
))


class CifcoddepositParser(CiffilterParser):
    """
    Specific parser for the output of cif_cod_deposit script.
    """

    def __init__(self, calc):
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

        status = cod_deposition_states.UNKNOWN
        messages = []

        if output_path is not None:
            content = None
            with open(output_path) as f:
                content = f.read()
            status, message = CifcoddepositParser._deposit_result(content)
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

        if status == cod_deposition_states.SUCCESS:
            return True, output_nodes
        else:
            return False, output_nodes

    @classmethod
    def _deposit_result(cls, output):
        import re

        status = cod_deposition_states.UNKNOWN
        message = ''

        output = re.sub('^[^:]*cif-deposit\.pl:\s+', '', output)
        output = re.sub('\n$', '', output)

        dep = re.search('^(structures .+ were successfully deposited '
                        'into .?COD)$', output)
        dup = re.search('^(the following structures seem to be already '
                        'in .?COD):', output, re.IGNORECASE)
        red = re.search('^(redeposition of structure is unnecessary)',
                        output)
        lgn = re.search('<p class="error"[^>]*>[^:]+: (.*)',
                        output, re.IGNORECASE)

        if dep is not None:
            status = cod_deposition_states.SUCCESS
            message = dep.group(1)
        elif dup is not None:
            status = cod_deposition_states.DUPLICATE
            message = dup.group(1)
        elif red is not None:
            status = cod_deposition_states.UNCHANGED
            message = dup.group(1)
        elif lgn is not None:
            status = cod_deposition_states.INPUTERROR
            message = lgn.group(1)
        else:
            status = cod_deposition_states.INPUTERROR
            message = output

        return status, message
