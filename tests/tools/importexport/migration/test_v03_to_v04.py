# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
"""Test archive file migration from export version 0.3 to 0.4"""
import tarfile
import zipfile

from archive_path import TarPath, ZipPath

from aiida.common.exceptions import NotExistent
from aiida.common import json
from aiida.tools.importexport.archive import CacheFolder
from aiida.tools.importexport.archive.migrations.utils import verify_metadata_version
from aiida.tools.importexport.archive.migrations.v03_to_v04 import migrate_v3_to_v4

from tests.utils.archives import get_archive_file, read_json_files


def test_migrate_external(external_archive, tmp_path):
    """Test migration for file containing complete v0.3 era possibilities"""

    # Get metadata.json and data.json as dicts from v0.3 file archive
    dirpath_archive = get_archive_file('export_v0.3.aiida', **external_archive)

    out_path = tmp_path / 'aiida.out'

    # Migrate
    if zipfile.is_zipfile(dirpath_archive):
        ZipPath(dirpath_archive).extract_tree(out_path)
    elif tarfile.is_tarfile(dirpath_archive):
        TarPath(dirpath_archive).extract_tree(out_path)
    else:
        raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

    try:
        metadata = json.loads((out_path / 'metadata.json').read_text('utf8'))
        data = json.loads((out_path / 'data.json').read_text('utf8'))
    except IOError:
        raise NotExistent(f'export archive does not contain the required file {out_path}')

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
    folder = CacheFolder(out_path)
    migrate_v3_to_v4(folder)
    _, metadata = folder.load_json('metadata.json')
    _, data = folder.load_json('data.json')
    verify_metadata_version(metadata, version='0.4')

    ## Following checks are based on the archive-file
    ## Which means there are more legal entities, they are simply not relevant here.

    # Check schema-changes
    new_node_attrs = {'node_type', 'process_type'}
    for change in new_node_attrs:
        # data.json
        for node in data['export_data']['Node'].values():
            assert change in node, f"'{change}' not found for {node}"
        # metadata.json
        assert change in metadata['all_fields_info']['Node'], f"'{change}' not found in metadata.json for Node"

    # Check Node types
    legal_node_types = {
        'data.float.Float.', 'data.int.Int.', 'data.dict.Dict.', 'data.code.Code.', 'data.structure.StructureData.',
        'data.folder.FolderData.', 'data.remote.RemoteData.', 'data.upf.UpfData.', 'data.array.ArrayData.',
        'data.array.bands.BandsData.', 'data.array.kpoints.KpointsData.', 'data.array.trajectory.TrajectoryData.',
        'process.workflow.workchain.WorkChainNode.', 'process.calculation.calcjob.CalcJobNode.'
    }
    legal_process_types = {'', 'aiida.calculations:quantumespresso.pw'}
    for node in data['export_data']['Node'].values():
        assert node['node_type'] in legal_node_types, (
            f"{node['node_type']} is not a legal node_type. Legal node types: {legal_node_types}"
        )
        assert node['process_type'] in legal_process_types, (
            f"{node['process_type']} is not a legal process_type. Legal process types: {legal_node_types}"
        )

    # Check links
    # Make sure the two illegal create links were removed during the migration
    assert len(data['links_uuid']) == links_count_org - 2, (
        'Two of the org. {} links should have been removed during the migration, '
        'instead there are now {} links'.format(links_count_org, len(data['links_uuid']))
    )
    legal_link_types = {'unspecified', 'create', 'return', 'input_calc', 'input_work', 'call_calc', 'call_work'}
    for link in data['links_uuid']:
        assert link['type'] in legal_link_types
    for link in illegal_links:
        assert link not in data['links_uuid'], f'{link} should not be in the migrated archive file'

    # Check Groups
    # There is one Group in the archive file, it is a user group
    updated_attrs = {'label', 'type_string'}
    legal_group_type = {'user'}
    for attr in updated_attrs:
        # data.json
        for group in data['export_data']['Group'].values():
            assert attr in group, f'{attr} not found in Group {group}'
            assert group['type_string'] in legal_group_type, f"{group['type_string']} is not a legal Group type_string"

        # metadata.json
        assert attr in metadata['all_fields_info']['Group'], f'{attr} not found in metadata.json'

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
                assert attr in data[field][node_id], (
                    f"Updated attribute name '{attr}' not found in {field} for node_id: {node_id}"
                )
            for old, new in optional_updated_calcjob_attrs.items():
                assert old not in data[field][node_id], (
                    "Old attribute '{}' found in {} for node_id: {}. "
                    "It should now be updated to '{}' or not exist".format(old, field, node_id, new)
                )
        for node_id in process_nodes:
            for attr in updated_process_attrs:
                assert attr in data[field][node_id], (
                    f"Updated attribute name '{attr}' not found in {field} for node_id: {node_id}"
                )

    # Check TrajectoryData
    # There should be minimum one TrajectoryData in the archive file
    trajectorydata_nodes = []
    for node_id, content in data['export_data']['Node'].items():
        if content['node_type'] == 'data.array.trajectory.TrajectoryData.':
            trajectorydata_nodes.append(node_id)

    updated_attrs = {'symbols'}
    fields = {'node_attributes', 'node_attributes_conversion'}
    for field in fields:
        for node_id in trajectorydata_nodes:
            for attr in updated_attrs:
                assert attr in data[field][node_id], (
                    f"Updated attribute name '{attr}' not found in {field} for TrajecteoryData node_id: {node_id}"
                )

    # Check Computer
    removed_attrs = {'enabled'}
    for attr in removed_attrs:
        # data.json
        for computer in data['export_data']['Computer'].values():
            assert attr not in computer, f"'{attr}' should have been removed from Computer {computer['name']}"

        # metadata.json
        assert attr not in metadata['all_fields_info']['Computer'], (
            f"'{attr}' should have been removed from Computer in metadata.json"
        )

    # Check new entities
    new_entities = {'Log', 'Comment'}
    fields = {'all_fields_info', 'unique_identifiers'}
    for entity in new_entities:
        for field in fields:
            assert entity in metadata[field], f'{entity} not found in {field} in metadata.json'

    # Check extras
    # Dicts with key, vales equal to node_id, {} should be present
    # This means they should be same length as data['export_data']['Node'] or 'node_attributes*'
    attrs_count = len(data['node_attributes'])
    new_fields = {'node_extras', 'node_extras_conversion'}
    for field in new_fields:
        assert field in list(data.keys()), f"New field '{field}' not found in data.json"
        assert len(data[field]) == attrs_count, (
            f"New field '{field}' found to have only {len(data[field])} entries, "
            f'but should have had {attrs_count} entries'
        )


def test_compare_migration_with_aiida_made(external_archive, migrate_from_func):
    """
    Compare the migration of a Workflow made and exported with version 0.3 to version 0.4,
    and the same Workflow made and exported with version 0.4.
    (AiiDA versions 0.12.3 versus 1.0.0b2)
    NB: Since PKs and UUIDs will have changed, comparisons between 'data.json'-files will be made indirectly
    """
    # Get metadata.json and data.json as dicts from v0.3 file archive and migrate
    metadata_v3, data_v3 = migrate_from_func('export_v0.3.aiida', '0.3', '0.4', migrate_v3_to_v4)

    # Get metadata.json and data.json as dicts from v0.4 file archive
    archive_path = get_archive_file('export_v0.4.aiida', **external_archive)
    metadata_v4, data_v4 = read_json_files(archive_path)  # pylint: disable=unbalanced-tuple-unpacking

    # Compare 'metadata.json'
    metadata_v3.pop('conversion_info')
    metadata_v3.pop('aiida_version')
    metadata_v4.pop('aiida_version')
    assert metadata_v3 == metadata_v4

    # Compare 'data.json'
    assert len(data_v3) == len(data_v4)

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
            assert add is not None, "Helper variable 'add' should never be None"
            details['migrated'].append(add)
        for node in data_v4['export_data'][entity].values():
            add = node.get('node_type', None)  # Node
            if not add:
                add = node.get('hostname', None)  # Computer
            if not add:
                add = node.get('type_string', None)  # Group
            assert add is not None, "Helper variable 'add' should never be None"
            details['made'].append(add)

        #### Two extra Dicts are present for AiiDA made export 0.4 file ####
        if entity == 'Node':
            details['migrated'].extend(2 * ['data.dict.Dict.'])

        assert sorted(details['migrated']) == sorted(details['made']
                                                     ), (f'Number of {entity}-entities differ, see diff for details')

    fields = {
        'groups_uuid', 'node_attributes_conversion', 'node_attributes', 'node_extras', 'node_extras_conversion'
    }  # 'export_data' is special, see below
    for field in fields:
        if field != 'groups_uuid':
            correction = 2  # Two extra Dicts in AiiDA made export v0.4 file
        else:
            correction = 0

        assert len(
            data_v3[field]
        ) == len(data_v4[field]) - correction, (f'Number of entities in {field} differs for the archive files')

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

    assert number_of_links_v3 == number_of_links_v4, (
        'There are a different number of specific links in the migrated archive file than the AiiDA made one.'
    )

    assert number_of_links_v3['unspecified'] == 0
    assert number_of_links_v4['unspecified'] == 0

    # Special for data['export_data']['User']
    # There is an extra user in the migrated export v0.3 file
    assert len(data_v3['export_data']['User']) == len(data_v4['export_data']['User']) + 1

    # Special for data['export_data']
    # There are Logs exported in the AiiDA made export v0.4 file
    assert len(data_v3['export_data']) + 1 == len(data_v4['export_data'])


def test_illegal_create_links(external_archive, tmp_path):
    """Test illegal create links from workchain are detected and removed from exports using v0.3"""
    # Initialization
    dirpath_archive = get_archive_file('export_v0.3.aiida', **external_archive)
    known_illegal_links = 2

    out_path = tmp_path / 'aiida.out'

    # Migrate
    if zipfile.is_zipfile(dirpath_archive):
        ZipPath(dirpath_archive).extract_tree(out_path)
    elif tarfile.is_tarfile(dirpath_archive):
        TarPath(dirpath_archive).extract_tree(out_path)
    else:
        raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

    try:
        data = json.loads((out_path / 'data.json').read_text('utf8'))
    except IOError:
        raise NotExistent(f'export archive does not contain the required file {out_path}')

    # Check illegal create links are present in org. archive file
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
    assert len(violations) == known_illegal_links, (
        f'{known_illegal_links} illegal create links were expected, instead {len(violations)} was/were found'
    )

    # Migrate to v0.4
    folder = CacheFolder(out_path)
    migrate_v3_to_v4(folder)

    _, data = folder.load_json('data.json')

    # Check illegal create links were removed
    assert len(data['links_uuid']) == links_count_migrated, (
        f"{links_count_migrated} links were expected, instead {len(data['links_uuid'])} was/were found"
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
    assert len(violations) == 0, f'0 illegal links were expected, instead {len(violations)} was/were found'
