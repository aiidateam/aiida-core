# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.restapi.translator.data import DataTranslator
from flask import send_from_directory
import os

class UpfDataTranslator(DataTranslator):
    """
    Translator relative to resource 'bands' and aiida class BandsData
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "upfs"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm.data.upf import UpfData
    _aiida_class = UpfData
    # The string name of the AiiDA class
    _aiida_type = "data.upf.UpfData"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(UpfDataTranslator, self).__init__(Class=self.__class__,
                                                **kwargs)

    @staticmethod
    def get_visualization_data(node, format=None):
        """

        Returns: data in a format required by dr.js to visualize a 2D plot
        with multiple data series.

        """
        return []

    @staticmethod
    def get_downloadable_data(node, format=None):
        """
        Generic function extented for kpoints data. Currently
        it is not implemented.

        :param node: node object that has to be visualized
        :param format: file extension format
        :returns: raise RestFeatureNotAvailable exception
        """
        response = {}
        if node.folder.exists():
            filepath = os.path.join(node.get_abs_path(), "path")
            filename = node.filename
            try:
                response["status"] = 200
                response["data"] = send_from_directory(filepath, filename)
                response["filename"] = filename
                return response
            except Exception as e:
                response["status"] = 500
                response["data"] = e.message

        else:
            response["status"] = 200
            response["data"] = "file does not exist"
            return response


