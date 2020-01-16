# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from export version 0.6 to 0.7"""

from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport.migration.utils import verify_metadata_version
from aiida.tools.importexport.migration.v06_to_v07 import (
    migrate_v6_to_v7, migration_data_migration_legacy_process_attributes
)

from tests.utils.archives import get_json_files


class TestMigrateV06toV07(AiidaTestCase):
    """Test migration of export files from export version 0.6 to 0.7"""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        # Utility helpers
        cls.external_archive = {'filepath': 'archives', 'external_module': 'aiida-export-migration-tests'}
        cls.core_archive = {'filepath': 'export/migrate'}

    def test_migrate_v6_to_v7(self):
        """Test migration for file containing complete v0.6 era possibilities"""
        from aiida import get_version

        # Get metadata.json and data.json as dicts from v0.6 file archive
        metadata_v6, data_v6 = get_json_files('export_v0.6_simple.aiida', **self.core_archive)
        verify_metadata_version(metadata_v6, version='0.6')

        # Get metadata.json and data.json as dicts from v0.7 file archive
        metadata_v7, data_v7 = get_json_files('export_v0.7_simple.aiida', **self.core_archive)
        verify_metadata_version(metadata_v7, version='0.7')

        # Migrate to v0.7
        migrate_v6_to_v7(metadata_v6, data_v6)
        verify_metadata_version(metadata_v6, version='0.7')

        # Remove AiiDA version, since this may change irregardless of the migration function
        metadata_v6.pop('aiida_version')
        metadata_v7.pop('aiida_version')

        # Assert conversion message in `metadata.json` is correct and then remove it for later assertions
        self.maxDiff = None  # pylint: disable=invalid-name
        conversion_message = 'Converted from version 0.6 to 0.7 with AiiDA v{}'.format(get_version())
        self.assertEqual(
            metadata_v6.pop('conversion_info')[-1],
            conversion_message,
            msg='The conversion message after migration is wrong'
        )
        metadata_v7.pop('conversion_info')

        # Assert changes were performed correctly
        self.assertDictEqual(
            metadata_v6,
            metadata_v7,
            msg='After migration, metadata.json should equal intended metadata.json from archives'
        )
        self.assertDictEqual(
            data_v6, data_v7, msg='After migration, data.json should equal intended data.json from archives'
        )

    def test_migrate_v6_to_v7_complete(self):
        """Test migration for file containing complete v0.6 era possibilities"""
        # Get metadata.json and data.json as dicts from v0.6 file archive
        metadata, data = get_json_files('export_v0.6_manual.aiida', **self.external_archive)
        verify_metadata_version(metadata, version='0.6')

        # Migrate to v0.7
        migrate_v6_to_v7(metadata, data)
        verify_metadata_version(metadata, version='0.7')

        self.maxDiff = None  # pylint: disable=invalid-name
        # Check attributes of process.* nodes
        illegal_attrs = {'_sealed', '_finished', '_failed', '_aborted', '_do_abort'}
        new_attrs = {'sealed': True}
        for node_pk, attrs in data['node_attributes'].items():
            if data['export_data']['Node'][node_pk]['node_type'].startswith('process.'):
                # Check if illegal attributes were removed successfully
                for attr in illegal_attrs:
                    self.assertNotIn(
                        attr,
                        attrs,
                        msg="key '{}' should have been removed from attributes for Node <pk={}>".format(attr, node_pk)
                    )

                # Check new attributes were added successfully
                for attr in new_attrs:
                    self.assertIn(
                        attr, attrs, msg="key '{}' was not added to attributes for Node <pk={}>".format(attr, node_pk)
                    )
                    self.assertEqual(
                        attrs[attr],
                        new_attrs[attr],
                        msg="key '{}' should have had the value {}, but did instead have {}".format(
                            attr, new_attrs[attr], attrs[attr]
                        )
                    )

        # Check Attribute and Link have been removed
        illegal_entities = {'Attribute', 'Link'}
        for dict_ in {'unique_identifiers', 'all_fields_info'}:
            for entity in illegal_entities:
                self.assertNotIn(
                    entity,
                    metadata[dict_],
                    msg="key '{}' should have been removed from '{}' in metadata.json".format(entity, dict_)
                )

    def test_migration_0040_corrupt_archive(self):
        """Check CorruptArchive is raised for different cases during migration 0040"""
        from aiida.tools.importexport.common.exceptions import CorruptArchive

        # data has one "valid" entry, in the form of Node <PK=42>.
        # At least it has the needed key `node_type`.
        # data also has one "invalid" entry, in form of Node <PK=25>.
        # It is listed in `node_attributes`, but not in `export_data.Node`
        # Also Node <PK=25> is present in `export_data.Node`, but not in `node_attributes`.
        # This is not fine, but will not (and should not) be caught by this particular migration function
        data = {
            'node_attributes': {
                25: {},
                42: {}
            },
            'export_data': {
                'Node': {
                    42: {
                        'node_type': 'data.int.Int.'
                    },
                    52: {
                        'node_type': 'data.dict.Dict.'
                    }
                }
            }
        }

        with self.assertRaises(CorruptArchive) as exc:
            migration_data_migration_legacy_process_attributes(data)

        self.assertIn('Your export archive is corrupt! Org. exception:', str(exc.exception))

        # data has one "valid" entry, in the form of Node <PK=52>.
        # data also has one "invalid" entry, in form of Node <PK=42>.
        # It is in an active process state ('waiting')
        data = {
            'node_attributes': {
                52: {
                    'process_state': 'finished',
                    '_sealed': True
                },
                42: {
                    'process_state': 'waiting'
                }
            },
            'export_data': {
                'Node': {
                    42: {
                        'node_type': 'process.calculation.calcjob.CalcJobNode.'
                    },
                    52: {
                        'node_type': 'process.calculation.calcjob.CalcJobNode.'
                    }
                }
            }
        }

        with self.assertRaises(CorruptArchive) as exc:
            migration_data_migration_legacy_process_attributes(data)

        self.assertIn('Your export archive is corrupt! Please see the log-file', str(exc.exception))

    def test_migration_0040_no_process_state(self):
        """Check old ProcessNodes without a `process_state` can be migrated"""
        # data has one "new" entry, in the form of Node <PK=52>.
        # data also has one "old" entry, in form of Node <PK=42>.
        # It doesn't have a `process_state` attribute (nor a `sealed` or `_sealed`)
        data = {
            'node_attributes': {
                52: {
                    'process_state': 'finished',
                    'sealed': True
                },
                42: {}
            },
            'export_data': {
                'Node': {
                    42: {
                        'node_type': 'process.workflow.workfunction.WorkFunctionNode.'
                    },
                    52: {
                        'node_type': 'process.calculation.calcjob.CalcJobNode.'
                    }
                }
            }
        }

        migration_data_migration_legacy_process_attributes(data)

        self.assertDictEqual(data['node_attributes'][42], {'sealed': True})
