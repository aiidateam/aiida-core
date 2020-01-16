# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test export file migration from export version 0.3 to 0.4"""
# pylint: disable=too-many-locals,too-many-branches,too-many-statements

import tarfile
import zipfile

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import NotExistent
from aiida.common.folders import SandboxFolder
from aiida.common.json import load as jsonload
from aiida.tools.importexport.common.archive import extract_tar, extract_zip
from aiida.tools.importexport.migration.utils import verify_metadata_version
from aiida.tools.importexport.migration.v03_to_v04 import migrate_v3_to_v4

from tests.utils.archives import get_archive_file, get_json_files


class TestMigrateV03toV04(AiidaTestCase):
    """Test migration of export files from export version 0.3 to 0.4"""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        # Utility helpers
        cls.external_archive = {'filepath': 'archives', 'external_module': 'aiida-export-migration-tests'}
        cls.core_archive = {'filepath': 'export/migrate'}

    def test_migrate_v3_to_v4(self):
        """Test function migrate_v3_to_v4"""
        from aiida import get_version

        # Get metadata.json and data.json as dicts from v0.4 file archive
        metadata_v4, data_v4 = get_json_files('export_v0.4_simple.aiida', **self.core_archive)
        verify_metadata_version(metadata_v4, version='0.4')

        # Get metadata.json and data.json as dicts from v0.3 file archive
        # Cannot use 'get_json_files' for 'export_v0.3_simple.aiida',
        # because we need to pass the SandboxFolder to 'migrate_v3_to_v4'
        dirpath_archive = get_archive_file('export_v0.3_simple.aiida', **self.core_archive)

        with SandboxFolder(sandbox_in_repo=False) as folder:
            if zipfile.is_zipfile(dirpath_archive):
                extract_zip(dirpath_archive, folder, silent=True)
            elif tarfile.is_tarfile(dirpath_archive):
                extract_tar(dirpath_archive, folder, silent=True)
            else:
                raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

            try:
                with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                    data_v3 = jsonload(fhandle)
                with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                    metadata_v3 = jsonload(fhandle)
            except IOError:
                raise NotExistent('export archive does not contain the required file {}'.format(fhandle.filename))

            verify_metadata_version(metadata_v3, version='0.3')

            # Migrate to v0.4
            migrate_v3_to_v4(metadata_v3, data_v3, folder)
            verify_metadata_version(metadata_v3, version='0.4')

        # Remove AiiDA version, since this may change irregardless of the migration function
        metadata_v3.pop('aiida_version')
        metadata_v4.pop('aiida_version')

        # Assert conversion message in `metadata.json` is correct and then remove it for later assertions
        self.maxDiff = None  # pylint: disable=invalid-name
        conversion_message = 'Converted from version 0.3 to 0.4 with AiiDA v{}'.format(get_version())
        self.assertEqual(
            metadata_v3.pop('conversion_info')[-1],
            conversion_message,
            msg='The conversion message after migration is wrong'
        )
        metadata_v4.pop('conversion_info')

        # Assert changes were performed correctly
        self.assertDictEqual(
            metadata_v3,
            metadata_v4,
            msg='After migration, metadata.json should equal intended metadata.json from archives'
        )
        self.assertDictEqual(
            data_v3, data_v4, msg='After migration, data.json should equal intended data.json from archives'
        )

    def test_migrate_v3_to_v4_complete(self):
        """Test migration for file containing complete v0.3 era possibilities"""

        # Get metadata.json and data.json as dicts from v0.3 file archive
        dirpath_archive = get_archive_file('export_v0.3.aiida', **self.external_archive)

        # Migrate
        with SandboxFolder(sandbox_in_repo=False) as folder:
            if zipfile.is_zipfile(dirpath_archive):
                extract_zip(dirpath_archive, folder, silent=True)
            elif tarfile.is_tarfile(dirpath_archive):
                extract_tar(dirpath_archive, folder, silent=True)
            else:
                raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

            try:
                with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                    data = jsonload(fhandle)
                with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                    metadata = jsonload(fhandle)
            except IOError:
                raise NotExistent('export archive does not contain the required file {}'.format(fhandle.filename))

            verify_metadata_version(metadata, version='0.3')

            # Save pre-migration info
            links_count_org = len(data['links_uuid'])
            work_uuids = {
                value['uuid']
                for value in data['export_data']['Node'].values()
                if value['type'].startswith('calculation.function') or value['type'].startswith('calculation.work')
            }
            illegal_links = []
            for link in data['links_uuid']:
                if link['input'] in work_uuids and link['type'] == 'createlink':
                    illegal_links.append(link)

            # Migrate to v0.4
            migrate_v3_to_v4(metadata, data, folder)
            verify_metadata_version(metadata, version='0.4')

        ## Following checks are based on the archive-file
        ## Which means there are more legal entities, they are simply not relevant here.

        self.maxDiff = None  # pylint: disable=invalid-name
        # Check schema-changes
        new_node_attrs = {'node_type', 'process_type'}
        for change in new_node_attrs:
            # data.json
            for node in data['export_data']['Node'].values():
                self.assertIn(change, node, msg="'{}' not found for {}".format(change, node))
            # metadata.json
            self.assertIn(
                change,
                metadata['all_fields_info']['Node'],
                msg="'{}' not found in metadata.json for Node".format(change)
            )

        # Check Node types
        legal_node_types = {
            'data.float.Float.', 'data.int.Int.', 'data.dict.Dict.', 'data.code.Code.', 'data.structure.StructureData.',
            'data.folder.FolderData.', 'data.remote.RemoteData.', 'data.upf.UpfData.', 'data.array.ArrayData.',
            'data.array.bands.BandsData.', 'data.array.kpoints.KpointsData.', 'data.array.trajectory.TrajectoryData.',
            'process.workflow.workchain.WorkChainNode.', 'process.calculation.calcjob.CalcJobNode.'
        }
        legal_process_types = {'', 'aiida.calculations:quantumespresso.pw'}
        for node in data['export_data']['Node'].values():
            self.assertIn(
                node['node_type'],
                legal_node_types,
                msg='{} is not a legal node_type. Legal node types: {}'.format(node['node_type'], legal_node_types)
            )
            self.assertIn(
                node['process_type'],
                legal_process_types,
                msg='{} is not a legal process_type. Legal process types: {}'.format(
                    node['process_type'], legal_node_types
                )
            )

        # Check links
        # Make sure the two illegal create links were removed during the migration
        self.assertEqual(
            len(data['links_uuid']),
            links_count_org - 2,
            msg='Two of the org. {} links should have been removed during the migration, '
            'instead there are now {} links'.format(links_count_org, len(data['links_uuid']))
        )
        legal_link_types = {'unspecified', 'create', 'return', 'input_calc', 'input_work', 'call_calc', 'call_work'}
        for link in data['links_uuid']:
            self.assertIn(link['type'], legal_link_types)
        for link in illegal_links:
            self.assertNotIn(link, data['links_uuid'], msg='{} should not be in the migrated export file'.format(link))

        # Check Groups
        # There is one Group in the export file, it is a user group
        updated_attrs = {'label', 'type_string'}
        legal_group_type = {'user'}
        for attr in updated_attrs:
            # data.json
            for group in data['export_data']['Group'].values():
                self.assertIn(attr, group, msg='{} not found in Group {}'.format(attr, group))
                self.assertIn(
                    group['type_string'],
                    legal_group_type,
                    msg='{} is not a legal Group type_string'.format(group['type_string'])
                )
            # metadata.json
            self.assertIn(attr, metadata['all_fields_info']['Group'], msg='{} not found in metadata.json'.format(attr))

        # Check node_attributes*
        calcjob_nodes = []
        process_nodes = []
        for node_id, content in data['export_data']['Node'].items():
            if content['node_type'] == 'process.calculation.calcjob.CalcJobNode.':
                calcjob_nodes.append(node_id)
            elif content['node_type'].startswith('process.'):
                process_nodes.append(node_id)

        mandatory_updated_calcjob_attrs = {'resources', 'parser_name'}
        optional_updated_calcjob_attrs = {'custom_environment_variables': 'environment_variables'}
        updated_process_attrs = {'process_label'}
        fields = {'node_attributes', 'node_attributes_conversion'}
        for field in fields:
            for node_id in calcjob_nodes:
                for attr in mandatory_updated_calcjob_attrs:
                    self.assertIn(
                        attr,
                        data[field][node_id],
                        msg="Updated attribute name '{}' not found in {} for node_id: {}".format(attr, field, node_id)
                    )
                for old, new in optional_updated_calcjob_attrs.items():
                    self.assertNotIn(
                        old,
                        data[field][node_id],
                        msg="Old attribute '{}' found in {} for node_id: {}. "
                        "It should now be updated to '{}' or not exist".format(old, field, node_id, new)
                    )
            for node_id in process_nodes:
                for attr in updated_process_attrs:
                    self.assertIn(
                        attr,
                        data[field][node_id],
                        msg="Updated attribute name '{}' not found in {} for node_id: {}".format(attr, field, node_id)
                    )

        # Check TrajectoryData
        # There should be minimum one TrajectoryData in the export file
        trajectorydata_nodes = []
        for node_id, content in data['export_data']['Node'].items():
            if content['node_type'] == 'data.array.trajectory.TrajectoryData.':
                trajectorydata_nodes.append(node_id)

        updated_attrs = {'symbols'}
        fields = {'node_attributes', 'node_attributes_conversion'}
        for field in fields:
            for node_id in trajectorydata_nodes:
                for attr in updated_attrs:
                    self.assertIn(
                        attr,
                        data[field][node_id],
                        msg="Updated attribute name '{}' not found in {} for TrajecteoryData node_id: {}".format(
                            attr, field, node_id
                        )
                    )

        # Check Computer
        removed_attrs = {'enabled'}
        for attr in removed_attrs:
            # data.json
            for computer in data['export_data']['Computer'].values():
                self.assertNotIn(
                    attr, computer, msg="'{}' should have been removed from Computer {}".format(attr, computer['name'])
                )
            # metadata.json
            self.assertNotIn(
                attr,
                metadata['all_fields_info']['Computer'],
                msg="'{}' should have been removed from Computer in metadata.json".format(attr)
            )

        # Check new entities
        new_entities = {'Log', 'Comment'}
        fields = {'all_fields_info', 'unique_identifiers'}
        for entity in new_entities:
            for field in fields:
                self.assertIn(entity, metadata[field], msg='{} not found in {} in metadata.json'.format(entity, field))

        # Check extras
        # Dicts with key, vales equal to node_id, {} should be present
        # This means they should be same length as data['export_data']['Node'] or 'node_attributes*'
        attrs_count = len(data['node_attributes'])
        new_fields = {'node_extras', 'node_extras_conversion'}
        for field in new_fields:
            self.assertIn(field, list(data.keys()), msg="New field '{}' not found in data.json".format(field))
            self.assertEqual(
                len(data[field]),
                attrs_count,
                msg="New field '{}' found to have only {} entries, but should have had {} entries".format(
                    field, len(data[field]), attrs_count
                )
            )

    def test_compare_migration_with_aiida_made(self):
        """
        Compare the migration of a Workflow made and exported with version 0.3 to version 0.4,
        and the same Workflow made and exported with version 0.4.
        (AiiDA versions 0.12.3 versus 1.0.0b2)
        NB: Since PKs and UUIDs will have changed, comparisons between 'data.json'-files will be made indirectly
        """
        # Get metadata.json and data.json as dicts from v0.3 file archive and migrate
        dirpath_archive = get_archive_file('export_v0.3.aiida', **self.external_archive)

        # Migrate
        with SandboxFolder(sandbox_in_repo=False) as folder:
            if zipfile.is_zipfile(dirpath_archive):
                extract_zip(dirpath_archive, folder, silent=True)
            elif tarfile.is_tarfile(dirpath_archive):
                extract_tar(dirpath_archive, folder, silent=True)
            else:
                raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

            try:
                with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                    data_v3 = jsonload(fhandle)
                with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                    metadata_v3 = jsonload(fhandle)
            except IOError:
                raise NotExistent('export archive does not contain the required file {}'.format(fhandle.filename))

            # Migrate to v0.4
            migrate_v3_to_v4(metadata_v3, data_v3, folder)

        # Get metadata.json and data.json as dicts from v0.4 file archive
        metadata_v4, data_v4 = get_json_files('export_v0.4.aiida', **self.external_archive)

        # Compare 'metadata.json'
        self.maxDiff = None
        metadata_v3.pop('conversion_info')
        metadata_v3.pop('aiida_version')
        metadata_v4.pop('aiida_version')
        self.assertDictEqual(metadata_v3, metadata_v4)

        self.maxDiff = None
        # Compare 'data.json'
        self.assertEqual(len(data_v3), len(data_v4))

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
        for entity, details in entities.items():
            for node in data_v3['export_data'][entity].values():
                add = node.get('node_type', None)  # Node
                if not add:
                    add = node.get('hostname', None)  # Computer
                if not add:
                    add = node.get('type_string', None)  # Group
                self.assertIsNotNone(add, msg="Helper variable 'add' should never be None")
                details['migrated'].append(add)
            for node in data_v4['export_data'][entity].values():
                add = node.get('node_type', None)  # Node
                if not add:
                    add = node.get('hostname', None)  # Computer
                if not add:
                    add = node.get('type_string', None)  # Group
                self.assertIsNotNone(add, msg="Helper variable 'add' should never be None")
                details['made'].append(add)

            #### Two extra Dicts are present for AiiDA made export 0.4 file ####
            if entity == 'Node':
                details['migrated'].extend(2 * ['data.dict.Dict.'])

            self.assertListEqual(
                sorted(details['migrated']),
                sorted(details['made']),
                msg='Number of {}-entities differ, see diff for details'.format(entity)
            )

        fields = {
            'groups_uuid', 'node_attributes_conversion', 'node_attributes', 'node_extras', 'node_extras_conversion'
        }  # 'export_data' is special, see below
        for field in fields:
            if field != 'groups_uuid':
                correction = 2  # Two extra Dicts in AiiDA made export v0.4 file
            else:
                correction = 0

            self.assertEqual(
                len(data_v3[field]),
                len(data_v4[field]) - correction,
                msg='Number of entities in {} differs for the export files'.format(field)
            )

        number_of_links_v3 = {
            'unspecified': 0,
            'create': 0,
            'return': 0,
            'input_calc': 0,
            'input_work': 0,
            'call_calc': 0,
            'call_work': 0
        }
        for link in data_v3['links_uuid']:
            number_of_links_v3[link['type']] += 1

        number_of_links_v4 = {
            'unspecified': 0,
            'create': 0,
            'return': 0,
            'input_calc': -2,  # Two extra Dict inputs to CalcJobNodes
            'input_work': 0,
            'call_calc': 0,
            'call_work': 0
        }
        for link in data_v4['links_uuid']:
            number_of_links_v4[link['type']] += 1

        self.assertDictEqual(
            number_of_links_v3,
            number_of_links_v4,
            msg='There are a different number of specific links in the migrated export file than the AiiDA made one.'
        )

        self.assertEqual(number_of_links_v3['unspecified'], 0)
        self.assertEqual(number_of_links_v4['unspecified'], 0)

        # Special for data['export_data']['User']
        # There is an extra user in the migrated export v0.3 file
        self.assertEqual(len(data_v3['export_data']['User']), len(data_v4['export_data']['User']) + 1)

        # Special for data['export_data']
        # There are Logs exported in the AiiDA made export v0.4 file
        self.assertEqual(len(data_v3['export_data']) + 1, len(data_v4['export_data']))

    def test_illegal_create_links(self):
        """Test illegal create links from workchain are detected and removed from exports using v0.3"""
        # Initialization
        dirpath_archive = get_archive_file('export_v0.3.aiida', **self.external_archive)
        known_illegal_links = 2

        # Unpack archive, check data.json, and migrate to v0.4
        with SandboxFolder(sandbox_in_repo=False) as folder:
            if zipfile.is_zipfile(dirpath_archive):
                extract_zip(dirpath_archive, folder, silent=True)
            elif tarfile.is_tarfile(dirpath_archive):
                extract_tar(dirpath_archive, folder, silent=True)
            else:
                raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

            try:
                with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                    data = jsonload(fhandle)
                with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                    metadata = jsonload(fhandle)
            except IOError:
                raise NotExistent('export archive does not contain the required file {}'.format(fhandle.filename))

            # Check illegal create links are present in org. export file
            links_count = len(data['links_uuid'])
            links_count_migrated = links_count - known_illegal_links

            workfunc_uuids = {
                value['uuid']
                for value in data['export_data']['Node'].values()
                if value['type'].startswith('calculation.function') or value['type'].startswith('calculation.work')
            }
            violations = []
            for link in data['links_uuid']:
                if link['input'] in workfunc_uuids and link['type'] == 'createlink':
                    violations.append(link)
            self.assertEqual(
                len(violations),
                known_illegal_links,
                msg='{} illegal create links were expected, instead {} was/were found'.format(
                    known_illegal_links, len(violations)
                )
            )

            # Migrate to v0.4
            migrate_v3_to_v4(metadata, data, folder)

        # Check illegal create links were removed
        self.assertEqual(
            len(data['links_uuid']),
            links_count_migrated,
            msg='{} links were expected, instead {} was/were found'.format(
                links_count_migrated, len(data['links_uuid'])
            )
        )

        workfunc_uuids = {
            value['uuid']
            for value in data['export_data']['Node'].values()
            if value['node_type'].find('WorkFunctionNode') != -1 or value['node_type'].find('WorkChainNode') != -1
        }
        violations = []
        for link in data['links_uuid']:
            if link['input'] in workfunc_uuids and link['type'] == 'create':
                violations.append(link)
        self.assertEqual(
            len(violations), 0, msg='0 illegal links were expected, instead {} was/were found'.format(len(violations))
        )
