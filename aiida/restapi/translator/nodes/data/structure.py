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
Translator for structure data
"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from aiida.restapi.translator.nodes.data import DataTranslator


class StructureDataTranslator(DataTranslator):
    """
    Translator relative to resource 'structures' and aiida class StructureData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'structures'
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import StructureData
    _aiida_class = StructureData
    # The string name of the AiiDA class
    _aiida_type = 'data.structure.StructureData'

    _result_type = __label__

    @staticmethod
    def get_derived_properties(node):
        """
        Returns: derived properties of the structure.
        """
        response = {}

        # Add extra information
        response['dimensionality'] = node.get_dimensionality()
        response['formula'] = node.get_formula()

        return response
