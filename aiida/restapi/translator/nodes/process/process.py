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
Translator for process node
"""

from aiida.restapi.translator.nodes.node import NodeTranslator


class ProcessTranslator(NodeTranslator):
    """
    Translator relative to resource 'data' and aiida class `~aiida.orm.nodes.data.data.Data`
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'process'
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import ProcessNode
    _aiida_class = ProcessNode
    # The string name of the AiiDA class
    _aiida_type = 'process.ProcessNode'

    _result_type = __label__

    @staticmethod
    def get_report(process):
        """Show the log report for one or multiple processes."""
        from aiida.orm import Log

        def get_dict(log):
            """Returns the dict representation of log object"""
            return {
                'time': log.time,
                'loggername': log.loggername,
                'levelname': log.levelname,
                'dbnode_id': log.dbnode_id,
                'message': log.message,
            }

        report = {}
        report['logs'] = [get_dict(log) for log in Log.collection.get_logs_for(process)]

        return report

    def get_projectable_properties(self):
        """
        Get projectable properties specific for Process nodes
        :return: dict of projectable properties and column_order list
        """
        projectable_properties = {
            'attributes.process_label': {
                'display_name': 'Name',
                'help_text': 'Process label attribute',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'attributes.process_state': {
                'display_name': 'Process state',
                'help_text': 'Process state attribute',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'creator': {
                'display_name': 'Creator',
                'help_text': 'User that created the node',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'ctime': {
                'display_name': 'Creation time',
                'help_text': 'Creation time of the node',
                'is_foreign_key': False,
                'type': 'datetime.datetime',
                'is_display': True
            },
            'mtime': {
                'display_name': 'Last Modification time',
                'help_text': 'Last modification time',
                'is_foreign_key': False,
                'type': 'datetime.datetime',
                'is_display': True
            },
            'process_type': {
                'display_name': 'Process type',
                'help_text': 'Process type',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': False
            },
            'user_id': {
                'display_name': 'Id of creator',
                'help_text': 'Id of the user that created the node',
                'is_foreign_key': True,
                'related_column': 'id',
                'related_resource': '_dbusers',
                'type': 'int',
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
        column_order = ['uuid', 'attributes.process_label', 'ctime', 'mtime', 'creator', 'attributes.process_state']

        return projectable_properties, column_order
