# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Translator for workchain node
"""

from aiida.restapi.translator.nodes.process.process import ProcessTranslator


class WorkChainTranslator(ProcessTranslator):
    """
    Translator relative to resource 'workchain' and aiida class Process
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'workchain'
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import WorkChainNode
    _aiida_class = WorkChainNode
    # The string name of the AiiDA class
    _aiida_type = 'process.workflow.workchain.WorkChainNode'

    _result_type = __label__

    @staticmethod
    def get_derived_properties(node):
        """
        Generic function extended for workchain. Currently
        it is not implemented.

        :param node: node object
        :returns: empty dict
        """
        response = {}

        return response
