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
Translator for data node
"""

from aiida.common.exceptions import LicensingException
from aiida.restapi.common.exceptions import RestInputValidationError
from aiida.restapi.translator.nodes.node import NodeTranslator


class DataTranslator(NodeTranslator):
    """
    Translator relative to resource 'data' and aiida class `~aiida.orm.nodes.data.data.Data`
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'data'
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import Data
    _aiida_class = Data
    # The string name of the AiiDA class
    _aiida_type = 'data.Data'

    _result_type = __label__

    @staticmethod
    def get_downloadable_data(node, download_format=None):
        """
        Return content in the specified format for download

        :param node: node representing cif file to be downloaded
        :param download_format: export format
        :returns: content of the node in the specified format for download
        """
        response = {}

        if download_format is None:
            raise RestInputValidationError(
                'Please specify the download format. '
                'The available download formats can be '
                'queried using the /nodes/download_formats/ endpoint.'
            )

        elif download_format in node.get_export_formats():
            try:
                response['data'] = node._exportcontent(download_format)[0]  # pylint: disable=protected-access
                response['status'] = 200
                try:
                    response['filename'] = node.filename
                except AttributeError:
                    response['filename'] = f'{node.uuid}.{download_format}'
            except LicensingException as exc:
                response['status'] = 500
                response['data'] = str(exc)

            return response

        else:
            raise RestInputValidationError(
                'The format {} is not supported. '
                'The available download formats can be '
                'queried using the /nodes/download_formats/ endpoint.'.format(download_format)
            )
