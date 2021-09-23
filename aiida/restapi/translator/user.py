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

from aiida import orm
from aiida.restapi.translator.base import BaseTranslator


class UserTranslator(BaseTranslator):
    """
    Translator relative to resource 'users' and aiida class User
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'users'
    # The AiiDA class one-to-one associated to the present class
    _aiida_class = orm.User
    # The string name of the AiiDA class
    _aiida_type = 'User'

    # If True (False) the corresponding AiiDA class has (no) uuid property
    _has_uuid = False

    _result_type = __label__

    _default_projections = ['id', 'first_name', 'last_name', 'institution']

    def get_projectable_properties(self):
        """
        Get projectable properties specific for User
        :return: dict of projectable properties and column_order list
        """
        projectable_properties = {
            'id': {
                'display_name': 'Id',
                'help_text': 'Id of the object',
                'is_foreign_key': False,
                'type': 'int',
                'is_display': True
            },
            'first_name': {
                'display_name': 'First name',
                'help_text': 'First name of the user',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'institution': {
                'display_name': 'Institution',
                'help_text': 'Affiliation of the user',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'last_name': {
                'display_name': 'Last name',
                'help_text': 'Last name of the user',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            }
        }

        # Note: final schema will contain details for only the fields present in column order
        column_order = ['id', 'first_name', 'last_name', 'institution']

        return projectable_properties, column_order
