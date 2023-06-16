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
Translator for bands data
"""
import json

from aiida.restapi.translator.nodes.data import DataTranslator


class BandsDataTranslator(DataTranslator):
    """
    Translator relative to resource 'bands' and aiida class BandsData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'bands'
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import BandsData
    _aiida_class = BandsData
    # The string name of the AiiDA class
    _aiida_type = 'data.core.array.bands.BandsData'

    _result_type = __label__

    @staticmethod
    def get_derived_properties(node):  # pylint: disable=arguments-differ
        """
        Returns: data in a format required by dr.js to visualize a 2D plot
        with multiple data series.

        Strategy: I take advantage of the export functionality of BandsData
        objects. The raw export has to be filtered for string escape characters.
        this is done by decoding the string returned by node._exportcontent.

        TODO: modify the function exportstring (or add another function in
        BandsData) so that it returns a python object rather than a string.
        """
        response = {}

        json_string = node._exportcontent('json', comments=False)  # pylint: disable=protected-access
        json_content = json.loads(json_string[0])
        response['bands'] = json_content

        return response
