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
Translator for code
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.restapi.translator.nodes.data import DataTranslator


class CodeTranslator(DataTranslator):
    """
    Translator relative to resource 'codes' and aiida class Code
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "codes"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import Code
    _aiida_class = Code
    # The string name of the AiiDA class
    _aiida_type = "data.code.Code"

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(CodeTranslator, self).__init__(Class=self.__class__, **kwargs)

    @staticmethod
    def get_visualization_data(node, visformat=None):
        """
        Generic function extented for codes data. Currently
        it is not implemented.

        :param node: node object that has to be visualized
        :param visformat: visualization format
        :returns: raise RestFeatureNotAvailable exception
        """

        from aiida.restapi.common.exceptions import RestFeatureNotAvailable

        raise RestFeatureNotAvailable("This endpoint is not available for Codes.")

    @staticmethod
    def get_downloadable_data(node, download_format=None):
        """
        Generic function extented for codes data. Currently
        it is not implemented.

        :param node: node object that has to be downloaded
        :param download_format: file extension format
        :returns: raise RestFeatureNotAvailable exception
        """

        from aiida.restapi.common.exceptions import RestFeatureNotAvailable

        raise RestFeatureNotAvailable("This endpoint is not available for Codes.")
