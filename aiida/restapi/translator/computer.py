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
    __label__ = 'computers'
    # The AiiDA class one-to-one associated to the present class
    _aiida_class = orm.Computer
    # The string name of the AiiDA class
    _aiida_type = 'Computer'

    # If True (False) the corresponding AiiDA class has (no) uuid property
    _has_uuid = True

    _result_type = __label__

    def get_projectable_properties(self):
        """
        Get projectable properties specific for Computer
        :return: dict of projectable properties and column_order list
        """
        from aiida.plugins.entry_point import get_entry_points
        from aiida.common.exceptions import EntryPointError

        schedulers = {}
        for entry_point in get_entry_points('aiida.schedulers'):
            try:
                schedulers[entry_point.name] = {'doc': entry_point.load().__doc__}
            except EntryPointError:
                continue

        transports = {}
        for entry_point in get_entry_points('aiida.transports'):
            try:
                transports[entry_point.name] = {'doc': entry_point.load().__doc__}
            except EntryPointError:
                continue

        projectable_properties = {
            'description': {
                'display_name': 'Description',
                'help_text': 'short description of the Computer',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': False
            },
            'hostname': {
                'display_name': 'Host',
                'help_text': 'Name of the host',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'id': {
                'display_name': 'Id',
                'help_text': 'Id of the object',
                'is_foreign_key': False,
                'type': 'int',
                'is_display': False
            },
            'name': {
                'display_name': 'Name',
                'help_text': 'Name of the object',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'scheduler_type': {
                'display_name': 'Scheduler',
                'help_text': 'Scheduler type',
                'is_foreign_key': False,
                'type': 'str',
                'valid_choices': schedulers,
                'is_display': True
            },
            'transport_type': {
                'display_name': 'Transport type',
                'help_text': 'Transport Type',
                'is_foreign_key': False,
                'type': 'str',
                'valid_choices': transports,
                'is_display': False
            },
            'uuid': {
                'display_name': 'Unique ID',
                'help_text': 'Universally Unique Identifier',
                'is_foreign_key': False,
                'type': 'unicode',
                'is_display': True
            }
        }

        # Note: final schema will contain details for only the fields present in column order
        column_order = ['uuid', 'name', 'hostname', 'description', 'scheduler_type', 'transport_type']

        return projectable_properties, column_order
