# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for archive reader."""
from aiida.tools.importexport.dbimport.readers import ReaderJsonZip

PATH = '/Users/chrisjsewell/Documents/GitHub/aiida_core_develop/out.aiida'


def test_json_zip():
    """Test the JSON zip reader."""
    with ReaderJsonZip(PATH) as reader:
        assert reader.metadata.export_version == '0.9'
        assert reader.metadata.aiida_version == '1.4.2'
        assert sorted(reader.entity_names) == ['Comment', 'Computer', 'Group', 'Log', 'Node', 'User']
        assert reader.entity_count('Node') == 40065
        assert sum(1 for _ in reader.iter_entity_fields('Node')) == 40065
        assert reader.entity_count('Computer') == 0
        assert reader.entity_count('User') == 1
        assert reader.entity_count('Group') == 0
        assert sum(1 for _ in reader.iter_group_uuids()) == 0
        assert reader.link_count == 40064
        assert sum(1 for _ in reader.iter_link_data()) == 40064
        assert next(reader.iter_entity_fields('Node', fields=('label', 'node_type', 'attributes'))) == (
            15663, {
                'node_type': 'data.dict.Dict.',
                'label': '',
                'attributes': {
                    '0': 0,
                    '1': 1,
                    '2': 2,
                    '3': 3,
                    '4': 4,
                    '5': 5,
                    '6': 6,
                    '7': 7,
                    '8': 8,
                    '9': 9
                }
            }
        )
        subfolder = reader.node_repository(next(reader.iter_node_uuids()))
        assert subfolder.get_subfolder('path').get_content_list() == ['key1', 'key0']
