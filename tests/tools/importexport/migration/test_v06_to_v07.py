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
from aiida.tools.importexport.migration.v06_to_v07 import migrate_v6_to_v7

from . import ArchiveMigrationTest


class TestMigrate(ArchiveMigrationTest):
    """Tests specific for this archive migration."""

    def test_migrate_external(self):
        """Test the migration on the test archive provided by the external test package."""
        metadata, data = self.migrate('export_v0.6_manual.aiida', '0.6', '0.7', migrate_v6_to_v7)

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
        from aiida.tools.importexport.migration.v06_to_v07 import migration_data_migration_legacy_process_attributes

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
        from aiida.tools.importexport.migration.v06_to_v07 import migration_data_migration_legacy_process_attributes
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
