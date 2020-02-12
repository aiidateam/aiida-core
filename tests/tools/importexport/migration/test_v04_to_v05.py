# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from export version 0.4 to 0.5"""

import tarfile
import zipfile

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import NotExistent
from aiida.common.folders import SandboxFolder
from aiida.common.json import load as jsonload
from aiida.tools.importexport.common.archive import extract_tar, extract_zip
from aiida.tools.importexport.migration.utils import verify_metadata_version
from aiida.tools.importexport.migration.v04_to_v05 import migrate_v4_to_v5

from tests.utils.archives import get_archive_file, get_json_files


class TestMigrateV04toV05(AiidaTestCase):
    """Test migration of export files from export version 0.4 to 0.5"""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        # Utility helpers
        cls.external_archive = {'filepath': 'archives', 'external_module': 'aiida-export-migration-tests'}
        cls.core_archive = {'filepath': 'export/migrate'}

    def test_migrate_v4_to_v5(self):
        """Test function migrate_v4_to_v5"""
        from aiida import get_version

        # Get metadata.json and data.json as dicts from v0.5 file archive
        metadata_v5, data_v5 = get_json_files('export_v0.5_simple.aiida', **self.core_archive)
        verify_metadata_version(metadata_v5, version='0.5')

        # Get metadata.json and data.json as dicts from v0.4 file archive
        # Cannot use 'get_json_files' for 'export_v0.4_simple.aiida',
        # because we need to pass the SandboxFolder to 'migrate_v4_to_v5'
        dirpath_archive = get_archive_file('export_v0.4_simple.aiida', **self.core_archive)

        with SandboxFolder(sandbox_in_repo=False) as folder:
            if zipfile.is_zipfile(dirpath_archive):
                extract_zip(dirpath_archive, folder, silent=True)
            elif tarfile.is_tarfile(dirpath_archive):
                extract_tar(dirpath_archive, folder, silent=True)
            else:
                raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

            try:
                with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                    data_v4 = jsonload(fhandle)
                with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                    metadata_v4 = jsonload(fhandle)
            except IOError:
                raise NotExistent('export archive does not contain the required file {}'.format(fhandle.filename))

            verify_metadata_version(metadata_v4, version='0.4')

            # Migrate to v0.5
            migrate_v4_to_v5(metadata_v4, data_v4)
            verify_metadata_version(metadata_v4, version='0.5')

        # Remove AiiDA version, since this may change irregardless of the migration function
        metadata_v4.pop('aiida_version')
        metadata_v5.pop('aiida_version')

        # Assert conversion message in `metadata.json` is correct and then remove it for later assertions
        # Remove also 'conversion_info' from `metadata.json` of v0.5 file archive
        self.maxDiff = None  # pylint: disable=invalid-name
        conversion_message = 'Converted from version 0.4 to 0.5 with AiiDA v{}'.format(get_version())
        self.assertEqual(
            metadata_v4.pop('conversion_info')[-1],
            conversion_message,
            msg='The conversion message after migration is wrong'
        )
        metadata_v5.pop('conversion_info')

        # Assert changes were performed correctly
        self.assertDictEqual(
            metadata_v4,
            metadata_v5,
            msg='After migration, metadata.json should equal intended metadata.json from archives'
        )
        self.assertDictEqual(
            data_v4, data_v5, msg='After migration, data.json should equal intended data.json from archives'
        )

    def test_migrate_v4_to_v5_complete(self):
        """Test migration for file containing complete v0.4 era possibilities"""

        # Get metadata.json and data.json as dicts from v0.4 file archive
        metadata, data = get_json_files('export_v0.4.aiida', **self.external_archive)
        verify_metadata_version(metadata, version='0.4')

        # Migrate to v0.5
        migrate_v4_to_v5(metadata, data)
        verify_metadata_version(metadata, version='0.5')

        self.maxDiff = None  # pylint: disable=invalid-name
        # Check schema-changes
        removed_computer_attrs = {'transport_params'}
        removed_node_attrs = {'nodeversion', 'public'}
        for change in removed_computer_attrs:
            # data.json
            for computer in data['export_data']['Computer'].values():
                self.assertNotIn(change, computer, msg="'{}' unexpectedly found for {}".format(change, computer))
            # metadata.json
            self.assertNotIn(
                change,
                metadata['all_fields_info']['Computer'],
                msg="'{}' unexpectedly found in metadata.json for Computer".format(change)
            )
        for change in removed_node_attrs:
            # data.json
            for node in data['export_data']['Node'].values():
                self.assertNotIn(change, node, msg="'{}' unexpectedly found for {}".format(change, node))
            # metadata.json
            self.assertNotIn(
                change,
                metadata['all_fields_info']['Node'],
                msg="'{}' unexpectedly found in metadata.json for Node".format(change)
            )
