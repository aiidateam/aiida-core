# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Translator for CifData """

from aiida.restapi.translator.nodes.data import DataTranslator


class CifDataTranslator(DataTranslator):
    """
    Translator relative to resource 'structures' and aiida class CifData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'cifs'
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import CifData
    _aiida_class = CifData
    # The string name of the AiiDA class
    _aiida_type = 'data.core.cif.CifData'

    _result_type = __label__

    @staticmethod
    def get_derived_properties(node):
        """
        Generic function extended for cif. Currently
        it is not implemented.

        :param node: node object
        :returns: empty dict
        """
        response = {}

        return response
