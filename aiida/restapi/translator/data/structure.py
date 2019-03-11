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
Translator for structure data
"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from aiida.restapi.translator.data import DataTranslator
from aiida.restapi.common.exceptions import RestInputValidationError
from aiida.common.exceptions import LicensingException


class StructureDataTranslator(DataTranslator):
    """
    Translator relative to resource 'structures' and aiida class StructureData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "structures"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import StructureData
    _aiida_class = StructureData
    # The string name of the AiiDA class
    _aiida_type = "data.structure.StructureData"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(StructureDataTranslator, self).__init__(Class=self.__class__, **kwargs)

    @staticmethod
    def get_visualization_data(node, visformat='xsf'):
        """
        Returns: data in specified format. If visformat is not specified returns data
        in xsf format in order to visualize the structure with JSmol.
        """
        response = {}
        response["str_viz_info"] = {}

        # This check is explicitly added here because sometimes
        # None is passed here as an value for visformat.
        if visformat is None:
            visformat = 'xsf'

        if visformat in node.get_export_formats():
            try:
                response["str_viz_info"]["data"] = node._exportcontent(visformat)[0].decode('utf-8')  # pylint: disable=protected-access
                response["str_viz_info"]["format"] = visformat
            except LicensingException as exc:
                response = str(exc)

        else:
            raise RestInputValidationError("The format {} is not supported.".format(visformat))

        # Add extra information
        response["dimensionality"] = node.get_dimensionality()
        response["pbc"] = node.pbc
        response["formula"] = node.get_formula()

        return response

    @staticmethod
    def get_downloadable_data(node, download_format="cif"):
        """
        Generic function extented for structure data

        :param node: node object that has to be visualized
        :param download_format: file extension format
        :returns: data in selected format to download
        """

        response = {}

        # This check is explicitly added here because sometimes
        # None is passed here as an value for download_format.
        if download_format is None:
            download_format = 'cif'

        if download_format in node.get_export_formats():
            try:
                response["data"] = node._exportcontent(download_format)[0]  # pylint: disable=protected-access
                response["status"] = 200
                response["filename"] = node.uuid + "_structure." + download_format
            except LicensingException as exc:
                response["status"] = 500
                response["data"] = str(exc)

        return response
