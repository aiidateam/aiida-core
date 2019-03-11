# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Translator for bands data
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.restapi.translator.data import DataTranslator


class BandsDataTranslator(DataTranslator):
    """
    Translator relative to resource 'bands' and aiida class BandsData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "bands"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import BandsData
    _aiida_class = BandsData
    # The string name of the AiiDA class
    _aiida_type = "data.array.bands.BandsData"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(BandsDataTranslator, self).__init__(Class=self.__class__, **kwargs)

    @staticmethod
    def get_visualization_data(node, visformat=None):
        """
        Returns: data in a format required by dr.js to visualize a 2D plot
        with multiple data series.

        Strategy: I take advantage of the export functionality of BandsData
        objects. The raw export has to be filtered for string escape characters.
        this is done by decoding the string returned by node._exportcontent.

        TODO: modify the function exportstring (or add another function in
        BandsData) so that it returns a python object rather than a string.
        """

        import ujson as uj
        json_string = node._exportcontent('json', comments=False)  # pylint: disable=protected-access
        json_content = uj.decode(json_string[0])

        # Add Ylabel which by default is not exported
        y_label = node.label + ' ({})'.format(node.get_attribute('units'))
        json_content['Y_label'] = y_label

        return json_content

    @staticmethod
    def get_downloadable_data(node, download_format=None):
        """
        Generic function extented for kpoints data. Currently
        it is not implemented.

        :param node: node object that has to be visualized
        :param download_format: file extension format
        :returns: raise RestFeatureNotAvailable exception
        """

        from aiida.restapi.common.exceptions import RestFeatureNotAvailable

        raise RestFeatureNotAvailable("This endpoint is not available for Bands.")
