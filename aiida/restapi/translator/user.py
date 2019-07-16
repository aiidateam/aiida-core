# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Translator for user"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.restapi.translator.base import BaseTranslator
from aiida import orm


class UserTranslator(BaseTranslator):
    """
    Translator relative to resource 'users' and aiida class User
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "users"
    # The AiiDA class one-to-one associated to the present class
    _aiida_class = orm.User
    # The string name of the AiiDA class
    _aiida_type = "User"

    # If True (False) the corresponding AiiDA class has (no) uuid property
    _has_uuid = False

    _result_type = __label__

    _default_projections = ['id', 'first_name', 'last_name', 'institution']

    ## user schema
    # All the values from column_order must present in additional info dict
    # Note: final schema will contain details for only the fields present in column order
    _schema_projections = {
        'column_order': ['id', 'first_name', 'last_name', 'email', 'institution'],
        'additional_info': {
            'id': {
                'is_display': True
            },
            'first_name': {
                'is_display': True
            },
            'last_name': {
                'is_display': True
            },
            'email': {
                'is_display': True
            },
            'institution': {
                'is_display': True
            }
        }
    }

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        super(UserTranslator, self).__init__(Class=self.__class__, **kwargs)
