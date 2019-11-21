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
Translator for calcjob node
"""

from aiida.restapi.translator.nodes.process.process import ProcessTranslator


class CalcJobTranslator(ProcessTranslator):
    """
    Translator relative to resource 'calculations' and aiida class Calculation
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'calcjobs'
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import CalcJobNode
    _aiida_class = CalcJobNode
    # The string name of the AiiDA class
    _aiida_type = 'process.calculation.calcjob.CalcJobNode'

    _result_type = __label__

    @staticmethod
    def get_input_files(node, filename):
        """
        Get the submitted input files for job calculation
        :param node: aiida node
        :return: the retrieved input files for job calculation
        """
        from aiida.restapi.translator.nodes.node import NodeTranslator
        return NodeTranslator.get_repo_list(node, filename)

    @staticmethod
    def get_output_files(node, filename):
        """
        Get the retrieved output files for job calculation
        :param node: aiida node
        :return: the retrieved output files for job calculation
        """
        from aiida.common.exceptions import NotExistent
        from aiida.restapi.translator.nodes.node import NodeTranslator

        try:
            retrieved_folder_node = node.outputs.retrieved
        except NotExistent:
            response = {}
            response['status'] = 200
            response['data'] = 'This node does not have retrieved folder'
            return response

        return NodeTranslator.get_repo_list(retrieved_folder_node, filename)

    @staticmethod
    def get_derived_properties(node):
        """
        Generic function extended for calcjob. Currently
        it is not implemented.

        :param node: node object
        :returns: empty dict
        """
        response = {}

        return response
