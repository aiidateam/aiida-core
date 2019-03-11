# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Translator for CifData """
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.restapi.translator.data import DataTranslator
from aiida.common.exceptions import LicensingException


class CifDataTranslator(DataTranslator):
    """
    Translator relative to resource 'structures' and aiida class CifData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "cifs"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import CifData
    _aiida_class = CifData
    # The string name of the AiiDA class
    _aiida_type = "data.cif.CifData"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(CifDataTranslator, self).__init__(Class=self.__class__, **kwargs)

    #pylint: disable=arguments-differ,redefined-builtin,protected-access
    @staticmethod
    def get_visualization_data(node, visformat=None):
        """
        Returns: data in specified format. If format is not specified returns data
        in a format required by chemdoodle to visualize a structure.
        """
        response = {}
        response["str_viz_info"] = {}

        if visformat is None:
            visformat = 'cif'

        if visformat in node.get_export_formats():
            try:
                response["str_viz_info"]["data"] = node._exportcontent(format)[0]  # pylint: disable=protected-access
                response["str_viz_info"]["format"] = visformat
            except LicensingException as exc:
                response = str(exc)

        ## Add extra information
        #response["dimensionality"] = node.get_dimensionality()
        #response["pbc"] = node.pbc
        #response["formula"] = node.get_formula()

        return response

    #pylint: disable=arguments-differ,redefined-builtin,protected-access
    @staticmethod
    def get_downloadable_data(node, download_format=None):
        """
        Return cif string for download

        :param node: node representing cif file to be downloaded
        :returns: cif file
        """

        response = {}

        download_format = 'cif'
        try:
            response["data"] = node._exportcontent(download_format)[0]  # pylint: disable=protected-access
            response["status"] = 200
            response["filename"] = node.uuid + "." + download_format
        except LicensingException as exc:
            response["status"] = 500
            response["data"] = str(exc)

        return response
