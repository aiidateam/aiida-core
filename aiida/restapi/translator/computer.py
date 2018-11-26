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
Translator for computer
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.restapi.translator.base import BaseTranslator
from aiida import orm


class ComputerTranslator(BaseTranslator):
    """
    Translator relative to resource 'computers' and aiida class Computer
    """
    # A label associated to the present class (coincides with the resource name)
    __label__ = "computers"
    # The AiiDA class one-to-one associated to the present class
    _aiida_class = orm.Computer
    # The string name of the AiiDA class
    _aiida_type = "Computer"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = 'computer'

    # If True (False) the corresponding AiiDA class has (no) uuid property
    _has_uuid = True

    _result_type = __label__

    ## computer schema
    # All the values from column_order must present in additional info dict
    # Note: final schema will contain details for only the fields present in column order
    _schema_projections = {
        "column_order": [
            "id", "name", "hostname", "description", "enabled", "scheduler_type", "transport_type", "transport_params",
            "uuid"
        ],
        "additional_info": {
            "id": {
                "is_display": True
            },
            "name": {
                "is_display": True
            },
            "hostname": {
                "is_display": True
            },
            "description": {
                "is_display": False
            },
            "enabled": {
                "is_display": True
            },
            "scheduler_type": {
                "is_display": True
            },
            "transport_type": {
                "is_display": False
            },
            "transport_params": {
                "is_display": False
            },
            "uuid": {
                "is_display": False
            }
        }
    }

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(ComputerTranslator, self).__init__(Class=self.__class__, **kwargs)
