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
Translator for group
"""

from aiida import orm
from aiida.restapi.translator.base import BaseTranslator


class GroupTranslator(BaseTranslator):
    """
    Translator relative to resource 'groups' and aiida class Group
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'groups'
    # The AiiDA class one-to-one associated to the present class
    _aiida_class = orm.Group
    # The string name of the AiiDA class
    _aiida_type = 'groups.Group'

    # If True (False) the corresponding AiiDA class has (no) uuid property
    _has_uuid = True

    _result_type = __label__

    def get_projectable_properties(self):
        """
        Get projectable properties specific for Group
        :return: dict of projectable properties and column_order list
        """
        projectable_properties = {
            'description': {
                'display_name': 'Description',
                'help_text': 'Short description of the group',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': False
            },
            'id': {
                'display_name': 'Id',
                'help_text': 'Id of the object',
                'is_foreign_key': False,
                'type': 'int',
                'is_display': False
            },
            'label': {
                'display_name': 'Label',
                'help_text': 'Name of the object',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'type_string': {
                'display_name': 'Type_string',
                'help_text': 'Type of the group',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'user_id': {
                'display_name': 'Id of creator',
                'help_text': 'Id of the user that created the node',
                'is_foreign_key': True,
                'related_column': 'id',
                'related_resource': 'users',
                'type': 'int',
                'is_display': False
            },
            'uuid': {
                'display_name': 'Unique ID',
                'help_text': 'Universally Unique Identifier',
                'is_foreign_key': False,
                'type': 'unicode',
                'is_display': False
            }
        }

        # Note: final schema will contain details for only the fields present in column order
        column_order = ['id', 'label', 'type_string', 'description', 'user_id', 'uuid']

        return projectable_properties, column_order
