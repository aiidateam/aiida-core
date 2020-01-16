# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from export version 0.7 to 0.8"""

from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport.migration.utils import verify_metadata_version
from aiida.tools.importexport.migration.v07_to_v08 import (migrate_v7_to_v8, migration_default_link_label)

from tests.utils.archives import get_json_files


class TestMigrateV07toV08(AiidaTestCase):
    """Test migration of export files from export version 0.7 to 0.8"""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        # Utility helpers
        cls.external_archive = {'filepath': 'archives', 'external_module': 'aiida-export-migration-tests'}
        cls.core_archive = {'filepath': 'export/migrate'}

    def test_migrate_v7_to_v8(self):
        """Test migration for file containing complete v0.7 era possibilities"""
        from aiida import get_version

        # Get metadata.json and data.json as dicts from v0.7 file archive
        metadata_v7, data_v7 = get_json_files('export_v0.7_simple.aiida', **self.core_archive)
        verify_metadata_version(metadata_v7, version='0.7')

        # Get metadata.json and data.json as dicts from v0.8 file archive
        metadata_v8, data_v8 = get_json_files('export_v0.8_simple.aiida', **self.core_archive)
        verify_metadata_version(metadata_v8, version='0.8')

        # Migrate to v0.8
        migrate_v7_to_v8(metadata_v7, data_v7)
        verify_metadata_version(metadata_v7, version='0.8')

        # Remove AiiDA version, since this may change irregardless of the migration function
        metadata_v7.pop('aiida_version')
        metadata_v8.pop('aiida_version')

        # Assert conversion message in `metadata.json` is correct and then remove it for later assertions
        self.maxDiff = None  # pylint: disable=invalid-name
        conversion_message = 'Converted from version 0.7 to 0.8 with AiiDA v{}'.format(get_version())
        self.assertEqual(
            metadata_v7.pop('conversion_info')[-1],
            conversion_message,
            msg='The conversion message after migration is wrong'
        )
        metadata_v8.pop('conversion_info')

        # Assert changes were performed correctly
        self.assertDictEqual(
            metadata_v7,
            metadata_v8,
            msg='After migration, metadata.json should equal intended metadata.json from archives'
        )
        self.assertDictEqual(
            data_v7, data_v8, msg='After migration, data.json should equal intended data.json from archives'
        )

    def test_migrate_v7_to_v8_complete(self):
        """Test migration for file containing complete v0.7 era possibilities"""
        # Get metadata.json and data.json as dicts from v0.7 file archive
        metadata, data = get_json_files('export_v0.7_manual.aiida', **self.external_archive)
        verify_metadata_version(metadata, version='0.7')

        # Migrate to v0.8
        migrate_v7_to_v8(metadata, data)
        verify_metadata_version(metadata, version='0.8')

        self.maxDiff = None  # pylint: disable=invalid-name
        # Check that no links have the label '_return', since it should now be 'result'
        illegal_label = '_return'
        for link in data.get('links_uuid'):
            self.assertFalse(
                link['label'] == illegal_label,
                msg='The illegal link label {} was not expected to be present - '
                "it should now be 'result'".format(illegal_label)
            )

    def test_migration_0043_default_link_label(self):
        """Check CorruptArchive is raised for different cases during migration 0040"""
        # data has one "valid" link, in the form of <label="a_good_label">.
        # data also has one "invalid" link, in form of <label="_return">.
        # After the migration, the "invalid" link should have been updated to the "valid" link <label="result">
        data = {
            'links_uuid': [{
                'input': 'some-random-uuid',
                'output': 'some-other-random-uuid',
                'label': '_return',
                'type': 'return'
            }, {
                'input': 'some-random-uuid',
                'output': 'some-other-random-uuid',
                'label': 'a_good_label',
                'type': 'return'
            }]
        }

        migration_default_link_label(data)

        self.assertEqual(
            data, {
                'links_uuid': [{
                    'input': 'some-random-uuid',
                    'output': 'some-other-random-uuid',
                    'label': 'result',
                    'type': 'return'
                }, {
                    'input': 'some-random-uuid',
                    'output': 'some-other-random-uuid',
                    'label': 'a_good_label',
                    'type': 'return'
                }]
            }
        )
