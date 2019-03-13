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
Translator for group
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.restapi.translator.base import BaseTranslator
from aiida import orm


class GroupTranslator(BaseTranslator):
    """
    Translator relative to resource 'groups' and aiida class Group
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "groups"
    # The AiiDA class one-to-one associated to the present class
    _aiida_class = orm.Group
    # The string name of the AiiDA class
    _aiida_type = "groups.Group"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = 'group'

    # If True (False) the corresponding AiiDA class has (no) uuid property
    _has_uuid = True

    _result_type = __label__

    ## group schema
    # All the values from column_order must present in additional info dict
    # Note: final schema will contain details for only the fields present in column order
    _schema_projections = {
        "column_order": ["id", "label", "type_string", "description", "user_id", "user_email", "uuid"],
        "additional_info": {
            "id": {
                "is_display": True
            },
            "label": {
                "is_display": True
            },
            "type_string": {
                "is_display": True
            },
            "description": {
                "is_display": False
            },
            "user_id": {
                "is_display": False
            },
            "user_email": {
                "is_display": True
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
        super(GroupTranslator, self).__init__(Class=self.__class__, **kwargs)
