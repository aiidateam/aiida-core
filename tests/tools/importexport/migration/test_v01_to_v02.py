# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from export version 0.1 to 0.2"""

from aiida import get_version
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport.migration.utils import verify_metadata_version
from aiida.tools.importexport.migration.v01_to_v02 import migrate_v1_to_v2

from tests.utils.archives import get_json_files


class TestMigrateV01toV02(AiidaTestCase):
    """Test migration of export files from export version 0.1 to 0.2"""

    def test_migrate_v1_to_v2(self):
        """Test function migrate_v1_to_v2"""
        # Get metadata.json and data.json as dicts from v0.1 file archive
        metadata_v1, data_v1 = get_json_files('export_v0.1_simple.aiida', filepath='export/migrate')
        verify_metadata_version(metadata_v1, version='0.1')

        # Get metadata.json and data.json as dicts from v0.2 file archive
        metadata_v2, data_v2 = get_json_files('export_v0.2_simple.aiida', filepath='export/migrate')
        verify_metadata_version(metadata_v2, version='0.2')

        # Migrate to v0.2
        migrate_v1_to_v2(metadata_v1, data_v1)
        verify_metadata_version(metadata_v1, version='0.2')

        # Remove AiiDA version, since this may change irregardless of the migration function
        metadata_v1.pop('aiida_version')
        metadata_v2.pop('aiida_version')

        # Assert conversion message in `metadata.json` is correct and then remove it for later assertions
        conversion_message = 'Converted from version 0.1 to 0.2 with AiiDA v{}'.format(get_version())
        self.assertEqual(
            metadata_v1.pop('conversion_info')[-1],
            conversion_message,
            msg='The conversion message after migration is wrong'
        )
        metadata_v2.pop('conversion_info')

        # Assert changes were performed correctly
        self.maxDiff = None  # pylint: disable=invalid-name
        self.assertDictEqual(
            metadata_v1,
            metadata_v2,
            msg='After migration, metadata.json should equal intended metadata.json from archives'
        )
        self.assertDictEqual(
            data_v1, data_v2, msg='After migration, data.json should equal intended data.json from archives'
        )
