# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-branches
"""Test export file migration from export version 0.2 to 0.3"""
from aiida.tools.importexport.migration.v02_to_v03 import migrate_v2_to_v3

from tests.utils.archives import get_json_files
from . import ArchiveMigrationTest


class TestMigrate(ArchiveMigrationTest):
    """Tests specific for this archive migration."""

    def test_migrate_external(self):
        """Test the migration on the test archive provided by the external test package."""
        metadata, data = self.migrate('export_v0.2.aiida', '0.2', '0.3', migrate_v2_to_v3)

        # Check link types
        legal_link_types = {'unspecified', 'createlink', 'returnlink', 'inputlink', 'calllink'}
        for link in data['links_uuid']:
            self.assertIn('type', link, msg="key 'type' was not added to link: {}".format(link))
            self.assertIn(link['type'], legal_link_types)

        # Check entity names
        legal_entity_names = {'Node', 'Link', 'Group', 'Computer', 'User', 'Attribute'}
        for field in {'unique_identifiers', 'all_fields_info'}:
            for entity, prop in metadata[field].items():
                self.assertIn(
                    entity,
                    legal_entity_names,
                    msg="'{}' should now be equal to anyone of these: {}, but is not".format(
                        entity, legal_entity_names
                    )
                )

                if field == 'all_fields_info':
                    for value in prop.values():
                        if 'requires' in value:
                            self.assertIn(
                                value['requires'],
                                legal_entity_names,
                                msg="'{}' should now be equal to anyone of these: {}, but is not".format(
                                    value, legal_entity_names
                                )
                            )

        for entity in data['export_data']:
            self.assertIn(
                entity,
                legal_entity_names,
                msg="'{}' should now be equal to anyone of these: {}, but is not".format(entity, legal_entity_names)
            )

    def test_compare_migration_with_aiida_made(self):
        """
        Compare the migration of a Workflow made and exported with version 0.2 to version 0.3,
        and the same Workflow made and exported with version 0.3.
        (AiiDA versions 0.9.1 versus 0.12.3)
        NB: Since PKs and UUIDs will have changed, comparisons between 'data.json'-files will be made indirectly
        """

        # Get metadata.json and data.json as dicts from v0.2 file archive and migrate
        metadata_v2, data_v2 = get_json_files('export_v0.2.aiida', **self.external_archive)
        migrate_v2_to_v3(metadata_v2, data_v2)

        # Get metadata.json and data.json as dicts from v0.3 file archive
        metadata_v3, data_v3 = get_json_files('export_v0.3.aiida', **self.external_archive)

        # Compare 'metadata.json'
        metadata_v2.pop('conversion_info')
        metadata_v2.pop('aiida_version')
        metadata_v3.pop('aiida_version')
        self.assertDictEqual(metadata_v2, metadata_v3)

        # Compare 'data.json'
        self.assertEqual(len(data_v2), len(data_v3))

        entities = {
            'Node': {
                'migrated': [],
                'made': []
            },
            'Computer': {
                'migrated': [],
                'made': []
            },
            'Group': {
                'migrated': [],
                'made': []
            }
        }  # User is special, see below
        add = None
        for entity, details in entities.items():
            for node in data_v2['export_data'][entity].values():
                if entity == 'Node':  # Node
                    add = node.get('type')
                if not add:
                    add = node.get('hostname', None)  # Computer
                if not add:
                    add = node.get('name', None)  # Group
                self.assertIsNotNone(add, msg="Helper variable 'add' should never be None")
                details['migrated'].append(add)
            for node in data_v3['export_data'][entity].values():
                if entity == 'Node':  # Node
                    add = node.get('type')

                    # Special case - BandsData did not exist for AiiDA v0.9.1
                    if add.endswith('BandsData.'):
                        add = 'data.array.kpoints.KpointsData.'

                if not add:
                    add = node.get('hostname', None)  # Computer
                if not add:
                    add = node.get('name', None)  # Group
                self.assertIsNotNone(add, msg="Helper variable 'add' should never be None")
                details['made'].append(add)

            self.assertListEqual(
                sorted(details['migrated']),
                sorted(details['made']),
                msg='Number of {}-entities differ, see diff for details'.format(entity)
            )

        fields = {'export_data', 'groups_uuid', 'node_attributes_conversion', 'node_attributes'}
        for field in fields:
            self.assertEqual(
                len(data_v2[field]),
                len(data_v3[field]),
                msg='Number of entities in {} differs for the export files'.format(field)
            )

        number_of_links_v2 = {
            'unspecified': 0,
            'createlink': 2,  # There are two extra create-links in the AiiDA made export v0.3 file
            'returnlink': 0,
            'inputlink': 0,
            'calllink': 0
        }
        for link in data_v2['links_uuid']:
            number_of_links_v2[link['type']] += 1

        number_of_links_v3 = {'unspecified': 0, 'createlink': 0, 'returnlink': 0, 'inputlink': 0, 'calllink': 0}
        for link in data_v3['links_uuid']:
            number_of_links_v3[link['type']] += 1

        self.assertDictEqual(
            number_of_links_v2,
            number_of_links_v3,
            msg='There are a different number of specific links in the migrated export file than the AiiDA made one.'
        )

        self.assertEqual(number_of_links_v2['unspecified'], 0)
        self.assertEqual(number_of_links_v3['unspecified'], 0)

        # Special for data['export_data']['User']
        # There is an extra user in the AiiDA made export file
        self.assertEqual(len(data_v2['export_data']['User']) + 1, len(data_v3['export_data']['User']))
