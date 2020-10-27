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
# from aiida.tools.importexport.archive.readers import ReaderJsonZip

# from tests.utils.archives import get_archive_file

# PATH = '/Users/chrisjsewell/Documents/GitHub/aiida_core_develop/out2.aiida'


def test_json_zip():
    """Test the JSON zip reader."""
    # with ReaderJsonZip(PATH) as reader:
    #     assert reader.metadata.export_version == '0.9'
    #     assert reader.metadata.aiida_version == '1.4.2'
    #     assert sorted(reader.entity_names) == ['Comment', 'Computer', 'Group', 'Log', 'Node', 'User']
    #     assert reader.entity_count('Node') == 40065
    #     assert sum(1 for _ in reader.iter_entity_fields('Node')) == 40065
    #     assert reader.entity_count('Computer') == 0
    #     assert reader.entity_count('User') == 1
    #     assert reader.entity_count('Group') == 1
    #     assert sum(1 for _ in reader.iter_group_uuids()) == 1
    #     assert reader.link_count == 40064
    #     assert sum(1 for _ in reader.iter_link_data()) == 40064
    #     assert next(reader.iter_entity_fields('Node', fields=('label', 'node_type', 'attributes'))) == (
    #         1, {
    #             'node_type': 'data.dict.Dict.',
    #             'label': '',
    #             'attributes': {
    #                 '0': 0,
    #                 '1': 1,
    #                 '2': 2,
    #                 '3': 3,
    #                 '4': 4,
    #                 '5': 5,
    #                 '6': 6,
    #                 '7': 7,
    #                 '8': 8,
    #                 '9': 9
    #             }
    #         }
    #     )
    #     assert next(reader.iter_entity_fields('Group', fields=('type_string', 'user'))
    #                 ) == (1, {
    #                     'user': 1,
    #                     'type_string': 'core.import'
    #                 })
    #     subfolder = reader.node_repository(next(reader.iter_node_uuids()))
    #     assert subfolder.get_subfolder('path').get_content_list() == ['key1', 'key0']

    # def test_context_required(self):
    #     """Verify that accessing a property of an Archive outside of a context manager raises."""
    #     with self.assertRaises(InvalidOperation):
    #         filepath = get_archive_file('export_v0.1_simple.aiida', filepath='export/migrate')
    #         archive = Archive(filepath)
    #         archive.version_format  # pylint: disable=pointless-statement

    # def test_version_format(self):
    #     """Verify that `version_format` return the correct archive format version."""
    #     filepath = get_archive_file('export_v0.1_simple.aiida', filepath='export/migrate')
    #     with Archive(filepath) as archive:
    #         self.assertEqual(archive.version_format, '0.1')

    # def test_empty_archive(self):
    #     """Verify that attempting to unpack an empty archive raises a `CorruptArchive` exception."""
    #     filepath = get_archive_file('empty.aiida', filepath='export/migrate')
    #     with self.assertRaises(CorruptArchive):
    #         with Archive(filepath) as archive:
    #             archive.version_format  # pylint: disable=pointless-statement
