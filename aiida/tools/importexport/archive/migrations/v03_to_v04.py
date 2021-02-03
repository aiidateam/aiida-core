# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration from v0.3 to v0.4, used by `verdi export migrate` command.

The migration steps are named similarly to the database migrations for Django and SQLAlchemy.
In the description of each migration, a revision number is given, which refers to the Django migrations.
The individual Django database migrations may be found at:

    `aiida.backends.djsite.db.migrations.00XX_<migration-name>.py`

Where XX are the numbers in the migrations' documentation: REV. 1.0.XX
And migration-name is the name of the particular migration.
The individual SQLAlchemy database migrations may be found at:

    `aiida.backends.sqlalchemy.migrations.versions.<id>_<migration-name>.py`

Where id is a SQLA id and migration-name is the name of the particular migration.
"""
# pylint: disable=invalid-name
import copy
import os

import numpy as np

from aiida.common import json
from aiida.tools.importexport.archive.common import CacheFolder
from aiida.tools.importexport.common.exceptions import ArchiveMigrationError
from .utils import verify_metadata_version, update_metadata, remove_fields


def migration_base_data_plugin_type_string(data):
    """Apply migration: 0009 - REV. 1.0.9
    `DbNode.type` content changes:
    'data.base.Bool.'  -> 'data.bool.Bool.'
    'data.base.Float.' -> 'data.float.Float.'
    'data.base.Int.'   -> 'data.int.Int.'
    'data.base.Str.'   -> 'data.str.Str.'
    'data.base.List.'  -> 'data.list.List.'
    """
    for content in data['export_data'].get('Node', {}).values():
        if content.get('type', '').startswith('data.base.'):
            type_str = content['type'].replace('data.base.', '')
            type_str = f'data.{type_str.lower()}{type_str}'
            content['type'] = type_str


def migration_process_type(metadata, data):
    """Apply migrations: 0010 - REV. 1.0.10
    Add `DbNode.process_type` column
    """
    # For data.json
    for content in data['export_data'].get('Node', {}).values():
        if 'process_type' not in content:
            content['process_type'] = ''
    # For metadata.json
    metadata['all_fields_info']['Node']['process_type'] = {}


def migration_code_sub_class_of_data(data):
    """Apply migrations: 0016 - REV. 1.0.16
    The Code class used to be just a sub class of Node, but was changed to act like a Data node.
    code.Code. -> data.code.Code.
    """
    for content in data['export_data'].get('Node', {}).values():
        if content.get('type', '') == 'code.Code.':
            content['type'] = 'data.code.Code.'


def migration_add_node_uuid_unique_constraint(data):
    """Apply migration: 0014 - REV. 1.0.14, 0018 - REV. 1.0.18
    Check that no entries with the same uuid are present in the archive file
    if yes - stop the import process
    """
    for entry_type in ['Group', 'Computer', 'Node']:
        if entry_type not in data['export_data']:  # if a particular entry type is not present - skip
            continue
        all_uuids = [content['uuid'] for content in data['export_data'][entry_type].values()]
        unique_uuids = set(all_uuids)
        if len(all_uuids) != len(unique_uuids):
            raise ArchiveMigrationError(f"""{entry_type}s with exactly the same UUID found, cannot proceed further.""")


def migration_migrate_builtin_calculations(data):
    """Apply migrations: 0019 - REV. 1.0.19
    Remove 'simpleplugin' from ArithmeticAddCalculation and TemplatereplacerCalculation type

    ATTENTION:

    The 'process_type' column did not exist before migration 0010, consequently, it could not be present in any
    export archive of the currently existing stable releases (0.12.*). Here, however, the migration acts
    on the content of the 'process_type' column, which could only be introduced in alpha releases of AiiDA 1.0.
    Assuming that 'add' and 'templateplacer' calculations are expected to have both 'type' and 'process_type' columns,
    they will be added based solely on the 'type' column content (unlike the way it is done in the DB migration,
    where the 'type_string' content was also checked).
    """
    for key, content in data['export_data'].get('Node', {}).items():
        if content.get('type', '') == 'calculation.job.simpleplugins.arithmetic.add.ArithmeticAddCalculation.':
            content['type'] = 'calculation.job.arithmetic.add.ArithmeticAddCalculation.'
            content['process_type'] = 'aiida.calculations:arithmetic.add'
        elif content.get('type', '') == 'calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation.':
            content['type'] = 'calculation.job.templatereplacer.TemplatereplacerCalculation.'
            content['process_type'] = 'aiida.calculations:templatereplacer'
        elif content.get('type', '') == 'data.code.Code.':
            if data['node_attributes'][key]['input_plugin'] == 'simpleplugins.arithmetic.add':
                data['node_attributes'][key]['input_plugin'] = 'arithmetic.add'

            elif data['node_attributes'][key]['input_plugin'] == 'simpleplugins.templatereplacer':
                data['node_attributes'][key]['input_plugin'] = 'templatereplacer'


def migration_provenance_redesign(data):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Apply migration: 0020 - REV. 1.0.20
    Provenance redesign
    """
    from aiida.manage.database.integrity.plugins import infer_calculation_entry_point
    from aiida.manage.database.integrity import write_database_integrity_violation
    from aiida.plugins.entry_point import ENTRY_POINT_STRING_SEPARATOR

    fallback_cases = []
    calcjobs_to_migrate = {}

    for key, value in data['export_data'].get('Node', {}).items():
        if value.get('type', '').startswith('calculation.job.'):
            calcjobs_to_migrate[key] = value

    if calcjobs_to_migrate:
        # step1: rename the type column of process nodes
        mapping_node_entry = infer_calculation_entry_point(
            type_strings=[e['type'] for e in calcjobs_to_migrate.values()]
        )
        for uuid, content in calcjobs_to_migrate.items():
            type_string = content['type']
            entry_point_string = mapping_node_entry[type_string]

            # If the entry point string does not contain the entry point string separator,
            # the mapping function was not able to map the type string onto a known entry point string.
            # As a fallback it uses the modified type string itself.
            # All affected entries should be logged to file that the user can consult.
            if ENTRY_POINT_STRING_SEPARATOR not in entry_point_string:
                fallback_cases.append([uuid, type_string, entry_point_string])

            content['process_type'] = entry_point_string

        if fallback_cases:
            headers = ['UUID', 'type (old)', 'process_type (fallback)']
            warning_message = 'found calculation nodes with a type string ' \
                              'that could not be mapped onto a known entry point'
            action_message = 'inferred `process_type` for all calculation nodes, ' \
                             'using fallback for unknown entry points'
            write_database_integrity_violation(fallback_cases, headers, warning_message, action_message)

    # step2: detect and delete unexpected links
    action_message = 'the link was deleted'
    headers = ['UUID source', 'UUID target', 'link type', 'link label']

    def delete_wrong_links(node_uuids, link_type, headers, warning_message, action_message):
        """delete links that are matching link_type and are going from nodes listed in node_uuids"""
        violations = []
        new_links_list = []
        for link in data['links_uuid']:
            if link['input'] in node_uuids and link['type'] == link_type:
                violations.append([link['input'], link['output'], link['type'], link['label']])
            else:
                new_links_list.append(link)
        data['links_uuid'] = new_links_list
        if violations:
            write_database_integrity_violation(violations, headers, warning_message, action_message)

    # calculations with outgoing CALL links
    calculation_uuids = {
        value['uuid'] for value in data['export_data'].get('Node', {}).values() if (
            value.get('type', '').startswith('calculation.job.') or
            value.get('type', '').startswith('calculation.inline.')
        )
    }
    warning_message = 'detected calculation nodes with outgoing `call` links.'
    delete_wrong_links(calculation_uuids, 'calllink', headers, warning_message, action_message)

    # calculations with outgoing RETURN links
    warning_message = 'detected calculation nodes with outgoing `return` links.'
    delete_wrong_links(calculation_uuids, 'returnlink', headers, warning_message, action_message)

    # outgoing CREATE links from FunctionCalculation and WorkCalculation nodes
    warning_message = 'detected outgoing `create` links from FunctionCalculation and/or WorkCalculation nodes.'
    work_uuids = {
        value['uuid'] for value in data['export_data'].get('Node', {}).values() if (
            value.get('type', '').startswith('calculation.function') or
            value.get('type', '').startswith('calculation.work')
        )
    }
    delete_wrong_links(work_uuids, 'createlink', headers, warning_message, action_message)

    for node_id, node in data['export_data'].get('Node', {}).items():
        # migrate very old `ProcessCalculation` to `WorkCalculation`
        if node.get('type', '') == 'calculation.process.ProcessCalculation.':
            node['type'] = 'calculation.work.WorkCalculation.'

        #  WorkCalculations that have a `function_name` attribute are FunctionCalculations
        if node.get('type', '') == 'calculation.work.WorkCalculation.':
            if (
                'function_name' in data['node_attributes'][node_id] and
                data['node_attributes'][node_id]['function_name'] is not None
            ):
                # for some reason for the workchains the 'function_name' attribute is present but has None value
                node['type'] = 'node.process.workflow.workfunction.WorkFunctionNode.'
            else:
                node['type'] = 'node.process.workflow.workchain.WorkChainNode.'

        # update type for JobCalculation nodes
        if node.get('type', '').startswith('calculation.job.'):
            node['type'] = 'node.process.calculation.calcjob.CalcJobNode.'

        # update type for InlineCalculation nodes
        if node.get('type', '') == 'calculation.inline.InlineCalculation.':
            node['type'] = 'node.process.calculation.calcfunction.CalcFunctionNode.'

        # update type for FunctionCalculation nodes
        if node.get('type', '') == 'calculation.function.FunctionCalculation.':
            node['type'] = 'node.process.workflow.workfunction.WorkFunctionNode.'

    uuid_node_type_mapping = {
        node['uuid']: node['type'] for node in data['export_data'].get('Node', {}).values() if 'type' in node
    }
    for link in data['links_uuid']:
        inp_uuid = link['output']
        # rename `createlink` to `create`
        if link['type'] == 'createlink':
            link['type'] = 'create'
        # rename `returnlink` to `return`
        elif link['type'] == 'returnlink':
            link['type'] = 'return'

        elif link['type'] == 'inputlink':
            # rename `inputlink` to `input_calc` if the target node is a calculation type node
            if uuid_node_type_mapping[inp_uuid].startswith('node.process.calculation'):
                link['type'] = 'input_calc'
            # rename `inputlink` to `input_work` if the target node is a workflow type node
            elif uuid_node_type_mapping[inp_uuid].startswith('node.process.workflow'):
                link['type'] = 'input_work'

        elif link['type'] == 'calllink':
            # rename `calllink` to `call_calc` if the target node is a calculation type node
            if uuid_node_type_mapping[inp_uuid].startswith('node.process.calculation'):
                link['type'] = 'call_calc'
            # rename `calllink` to `call_work` if the target node is a workflow type node
            elif uuid_node_type_mapping[inp_uuid].startswith('node.process.workflow'):
                link['type'] = 'call_work'


def migration_dbgroup_name_to_label_type_to_type_string(metadata, data):
    """Apply migrations: 0021 - REV. 1.0.21
    Rename dbgroup fields:
    name -> label
    type -> type_string
    """
    # For data.json
    for content in data['export_data'].get('Group', {}).values():
        if 'name' in content:
            content['label'] = content.pop('name')
        if 'type' in content:
            content['type_string'] = content.pop('type')
    # For metadata.json
    metadata_group = metadata['all_fields_info']['Group']
    if 'name' in metadata_group:
        metadata_group['label'] = metadata_group.pop('name')
    if 'type' in metadata_group:
        metadata_group['type_string'] = metadata_group.pop('type')


def migration_dbgroup_type_string_change_content(data):
    """Apply migrations: 0022 - REV. 1.0.22
    Change type_string according to the following rule:
    '' -> 'user'
    'data.upf.family' -> 'data.upf'
    'aiida.import' -> 'auto.import'
    'autogroup.run' -> 'auto.run'
    """
    for content in data['export_data'].get('Group', {}).values():
        key_mapper = {
            '': 'user',
            'data.upf.family': 'data.upf',
            'aiida.import': 'auto.import',
            'autogroup.run': 'auto.run'
        }
        if content['type_string'] in key_mapper:
            content['type_string'] = key_mapper[content['type_string']]


def migration_calc_job_option_attribute_keys(data):
    """Apply migrations: 0023 - REV. 1.0.23
    `custom_environment_variables` -> `environment_variables`
    `jobresource_params` -> `resources`
    `_process_label` -> `process_label`
    `parser` -> `parser_name`
    """

    # Helper function
    def _migration_calc_job_option_attribute_keys(attr_id, content):
        """Apply migration 0023 - REV. 1.0.23 for both `node_attributes*` dicts in `data.json`"""
        # For CalcJobNodes only
        if data['export_data']['Node'][attr_id]['type'] == 'node.process.calculation.calcjob.CalcJobNode.':
            key_mapper = {
                'custom_environment_variables': 'environment_variables',
                'jobresource_params': 'resources',
                'parser': 'parser_name'
            }
            # Need to loop over a clone because the `content` needs to be modified in place
            for key in copy.deepcopy(content):
                if key in key_mapper:
                    content[key_mapper[key]] = content.pop(key)

        # For all processes
        if data['export_data']['Node'][attr_id]['type'].startswith('node.process.'):
            if '_process_label' in content:
                content['process_label'] = content.pop('_process_label')

    # Update node_attributes and node_attributes_conversion
    attribute_dicts = ['node_attributes', 'node_attributes_conversion']
    for attribute_dict in attribute_dicts:
        for attr_id, content in data[attribute_dict].items():
            if 'type' in data['export_data'].get('Node', {}).get(attr_id, {}):
                _migration_calc_job_option_attribute_keys(attr_id, content)


def migration_move_data_within_node_module(data):
    """Apply migrations: 0025 - REV. 1.0.25
    The type string for `Data` nodes changed from `data.*` to `node.data.*`.
    """
    for value in data['export_data'].get('Node', {}).values():
        if value.get('type', '').startswith('data.'):
            value['type'] = value['type'].replace('data.', 'node.data.', 1)


def migration_trajectory_symbols_to_attribute(data: dict, folder: CacheFolder):
    """Apply migrations: 0026 - REV. 1.0.26 and 0027 - REV. 1.0.27
    Create the symbols attribute from the repository array for all `TrajectoryData` nodes.
    """
    from aiida.tools.importexport.common.config import NODES_EXPORT_SUBFOLDER

    path = folder.get_path(flush=False)

    for node_id, content in data['export_data'].get('Node', {}).items():
        if content.get('type', '') == 'node.data.array.trajectory.TrajectoryData.':
            uuid = content['uuid']
            symbols_path = path.joinpath(NODES_EXPORT_SUBFOLDER, uuid[0:2], uuid[2:4], uuid[4:], 'path', 'symbols.npy')
            symbols = np.load(os.path.abspath(symbols_path)).tolist()
            symbols_path.unlink()
            # Update 'node_attributes'
            data['node_attributes'][node_id].pop('array|symbols', None)
            data['node_attributes'][node_id]['symbols'] = symbols
            # Update 'node_attributes_conversion'
            data['node_attributes_conversion'][node_id].pop('array|symbols', None)
            data['node_attributes_conversion'][node_id]['symbols'] = [None] * len(symbols)


def migration_remove_node_prefix(data):
    """Apply migrations: 0028 - REV. 1.0.28
    Change node type strings:
    'node.data.' -> 'data.'
    'node.process.' -> 'process.'
    """
    for value in data['export_data'].get('Node', {}).values():
        if value.get('type', '').startswith('node.data.'):
            value['type'] = value['type'].replace('node.data.', 'data.', 1)
        elif value.get('type', '').startswith('node.process.'):
            value['type'] = value['type'].replace('node.process.', 'process.', 1)


def migration_rename_parameter_data_to_dict(data):
    """Apply migration: 0029 - REV. 1.0.29
    Update ParameterData to Dict
    """
    for value in data['export_data'].get('Node', {}).values():
        if value.get('type', '') == 'data.parameter.ParameterData.':
            value['type'] = 'data.dict.Dict.'


def migration_dbnode_type_to_dbnode_node_type(metadata, data):
    """Apply migration: 0030 - REV. 1.0.30
    Renaming DbNode.type to DbNode.node_type
    """
    # For data.json
    for content in data['export_data'].get('Node', {}).values():
        if 'type' in content:
            content['node_type'] = content.pop('type')
    # For metadata.json
    if 'type' in metadata['all_fields_info']['Node']:
        metadata['all_fields_info']['Node']['node_type'] = metadata['all_fields_info']['Node'].pop('type')


def migration_remove_dbcomputer_enabled(metadata, data):
    """Apply migration: 0031 - REV. 1.0.31
    Remove DbComputer.enabled
    """
    remove_fields(metadata, data, ['Computer'], ['enabled'])


def migration_replace_text_field_with_json_field(data):
    """Apply migration 0033 - REV. 1.0.33
    Store dict-values as JSON serializable dicts instead of strings
    NB! Specific for Django backend
    """
    for content in data['export_data'].get('Computer', {}).values():
        for value in ['metadata', 'transport_params']:
            if isinstance(content[value], str):
                content[value] = json.loads(content[value])
    for content in data['export_data'].get('Log', {}).values():
        if isinstance(content['metadata'], str):
            content['metadata'] = json.loads(content['metadata'])


def add_extras(data):
    """Update data.json with the new Extras
    Since Extras were not available previously and usually only include hashes,
    the Node ids will be added, but included as empty dicts
    """
    node_extras: dict = {}
    node_extras_conversion: dict = {}

    for node_id in data['export_data'].get('Node', {}):
        node_extras[node_id] = {}
        node_extras_conversion[node_id] = {}
    data.update({'node_extras': node_extras, 'node_extras_conversion': node_extras_conversion})


def migrate_v3_to_v4(folder: CacheFolder):
    """
    Migration of archive files from v0.3 to v0.4

    Note concerning migration 0032 - REV. 1.0.32:
    Remove legacy workflow tables: DbWorkflow, DbWorkflowData, DbWorkflowStep
    These were (according to Antimo Marrazzo) never exported.
    """
    old_version = '0.3'
    new_version = '0.4'

    _, metadata = folder.load_json('metadata.json')

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    _, data = folder.load_json('data.json')

    # Apply migrations in correct sequential order
    migration_base_data_plugin_type_string(data)
    migration_process_type(metadata, data)
    migration_code_sub_class_of_data(data)
    migration_add_node_uuid_unique_constraint(data)
    migration_migrate_builtin_calculations(data)
    migration_provenance_redesign(data)
    migration_dbgroup_name_to_label_type_to_type_string(metadata, data)
    migration_dbgroup_type_string_change_content(data)
    migration_calc_job_option_attribute_keys(data)
    migration_move_data_within_node_module(data)
    migration_trajectory_symbols_to_attribute(data, folder)
    migration_remove_node_prefix(data)
    migration_rename_parameter_data_to_dict(data)
    migration_dbnode_type_to_dbnode_node_type(metadata, data)
    migration_remove_dbcomputer_enabled(metadata, data)
    migration_replace_text_field_with_json_field(data)

    # Add Node Extras
    add_extras(data)

    # Update metadata.json with the new Log and Comment entities
    new_entities = {
        'Log': {
            'uuid': {},
            'time': {
                'convert_type': 'date'
            },
            'loggername': {},
            'levelname': {},
            'message': {},
            'metadata': {},
            'dbnode': {
                'related_name': 'dblogs',
                'requires': 'Node'
            }
        },
        'Comment': {
            'uuid': {},
            'ctime': {
                'convert_type': 'date'
            },
            'mtime': {
                'convert_type': 'date'
            },
            'content': {},
            'dbnode': {
                'related_name': 'dbcomments',
                'requires': 'Node'
            },
            'user': {
                'related_name': 'dbcomments',
                'requires': 'User'
            }
        }
    }
    metadata['all_fields_info'].update(new_entities)
    metadata['unique_identifiers'].update({'Log': 'uuid', 'Comment': 'uuid'})

    folder.write_json('metadata.json', metadata)
    folder.write_json('data.json', data)
