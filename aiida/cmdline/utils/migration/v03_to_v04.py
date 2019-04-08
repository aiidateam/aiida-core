# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-locals,too-many-statements,too-many-branches
"""Migration from v0.3 to v0.4, used by `verdi export migrate` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

import numpy as np

from aiida.cmdline.utils import echo
from aiida.cmdline.utils.migration.utils import verify_metadata_version, update_metadata


def migrate_provenance_redesign(data):
    """Utility function for `migrate_v3_to_v4` to handle REV. 1.0.20 (provenance redesign)"""
    # step1: rename the type column of process nodes
    from aiida.manage.database.integrity.plugins import infer_calculation_entry_point
    from aiida.manage.database.integrity import write_database_integrity_violation
    from aiida.plugins.entry_point import ENTRY_POINT_STRING_SEPARATOR

    fallback_cases = []
    nodes_to_migrate = {}

    for key, value in data['export_data']['Node'].items():
        if 'type' in value and value['type'].startswith('calculation.job.'):
            nodes_to_migrate[key] = value

    if not nodes_to_migrate:
        return

    mapping_node_entry = infer_calculation_entry_point(type_strings=[e['type'] for e in nodes_to_migrate.values()])
    for uuid, content in nodes_to_migrate.items():
        type_string = content['type']
        entry_point_string = mapping_node_entry[type_string]

        # If the entry point string does not contain the entry point string separator, the mapping function was not able
        # to map the type string onto a known entry point string. As a fallback it uses the modified type string itself.
        # All affected entries should be logged to file that the user can consult.
        if ENTRY_POINT_STRING_SEPARATOR not in entry_point_string:
            fallback_cases.append([uuid, type_string, entry_point_string])

        content['process_type'] = entry_point_string

    if fallback_cases:
        headers = ['UUID', 'type (old)', 'process_type (fallback)']
        warning_message = 'found calculation nodes with a type string that could not be mapped onto a known entry point'
        action_message = 'inferred `process_type` for all calculation nodes, using fallback for unknown entry points'
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
        value['uuid']
        for value in data['export_data']['Node'].values()
        if value['type'].startswith('calculation.job.') or value['type'].startswith('calculation.inline.')
    }
    warning_message = 'detected calculation nodes with outgoing `call` links.'
    delete_wrong_links(calculation_uuids, 'calllink', headers, warning_message, action_message)

    # calculations with outgoing RETURN links
    warning_message = 'detected calculation nodes with outgoing `return` links.'
    delete_wrong_links(calculation_uuids, 'returnlink', headers, warning_message, action_message)

    # outgoing CREATE links from FunctionCalculation and WorkCalculation nodes
    warning_message = 'detected outgoing `create` links from FunctionCalculation and/or WorkCalculation nodes.'
    work_uuids = {
        value['uuid']
        for value in data['export_data']['Node'].values()
        if value['type'].startswith('calculation.function') or value['type'].startswith('calculation.work')
    }
    delete_wrong_links(work_uuids, 'createlink', headers, warning_message, action_message)

    for node_id, node in data['export_data']['Node'].items():
        # migrate very old `ProcessCalculation` to `WorkCalculation`
        if node['type'] == 'calculation.process.ProcessCalculation.':
            node['type'] = 'calculation.work.WorkCalculation.'

        #  WorkCalculations that have a `function_name` attribute are FunctionCalculations
        if node['type'] == 'calculation.work.WorkCalculation.':
            if ('function_name' in data['node_attributes'][node_id] and
                    not data['node_attributes'][node_id]['function_name'] is None):
                # for some reason for the workchains the 'function_name' attribute is present but has None value
                node['type'] = 'node.process.workflow.workfunction.WorkFunctionNode.'
            else:
                node['type'] = 'node.process.workflow.workchain.WorkChainNode.'

        # update type for JobCalculation nodes
        if node['type'].startswith('calculation.job.'):
            node['type'] = 'node.process.calculation.calcjob.CalcJobNode.'

        # update type for InlineCalculation nodes
        if node['type'] == 'calculation.inline.InlineCalculation.':
            node['type'] = 'node.process.calculation.calcfunction.CalcFunctionNode.'

        # update type for FunctionCalculation nodes
        if node['type'] == 'calculation.function.FunctionCalculation.':
            node['type'] = 'node.process.workflow.workfunction.WorkFunctionNode.'

    uuid_node_type_mapping = {node['uuid']: node['type'] for node in data['export_data']['Node'].values()}
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


def migrate_v3_to_v4(metadata, data, folder):
    """
    Migration of export files from v0.3 to v0.4
    """
    old_version = '0.3'
    new_version = '0.4'

    verify_metadata_version(metadata, old_version)
    update_metadata(metadata, new_version)

    # Apply migration: 0009 - REV. 1.0.9
    # `DbNode.type` content changes:
    # 'data.base.Bool.'  -> 'data.bool.Bool.'
    # 'data.base.Float.' -> 'data.float.Float.'
    # 'data.base.Int.'   -> 'data.int.Int.'
    # 'data.base.Str.'   -> 'data.str.Str.'
    # 'data.base.List.'  -> 'data.list.List.'
    if 'Node' in data['export_data']:
        for content in data['export_data']['Node'].values():
            if 'type' in content and content['type'].startswith('data.base.'):
                type_str = content['type'].replace('data.base.', '')
                type_str = 'data.' + type_str.lower() + type_str
                content['type'] = type_str

    # Apply migrations: 0010 - REV. 1.0.10
    # Add `DbNode.process_type` column
    # For data.json
    if 'Node' in data['export_data']:
        for content in data['export_data']['Node'].values():
            if 'process_type' not in content:
                content['process_type'] = ''
    # For metadata.json
    metadata['all_fields_info']['Node']['process_type'] = {}

    # Apply migrations: 0016 - REV. 1.0.16
    # The Code class used to be just a sub class of Node but was changed to act like a Data node.
    # code.Code. -> data.code.Code.
    if 'Node' in data['export_data']:
        for content in data['export_data']['Node'].values():
            if 'type' in content and content['type'] == 'code.Code.':
                content['type'] = 'data.code.Code.'

    # Apply migration: 0014 - REV. 1.0.14, 0018 - REV. 1.0.18
    # Check that no entries with the same uuid are present in the export file
    # if yes - stop the import process
    for entry_type in ['Group', 'Computer', 'Node']:
        if not entry_type in data['export_data']:  # if a particular entry type is not present - skip
            continue
        all_uuids = [content['uuid'] for content in data['export_data'][entry_type].values()]
        unique_uuids = set(all_uuids)
        if len(all_uuids) != len(unique_uuids):
            echo.echo_critical("""{}s with exactly the same UUID found, cannot proceed further. Please contact AiiDA
            developers: http://www.aiida.net/mailing-list/ to help you resolve this issue.""".format(entry_type))

    # Apply migrations: 0019 - REV. 1.0.19
    # remove 'simpleplugin' from ArithmeticAddCalculation and TemplatereplacerCalculation type
    #
    # ATTENTION:
    #
    # The 'process_type' column did not exist before the migration 0010, consequently, it could not be present in any
    # export of the currently existing stable releases (0.12.*). Here, however, the migration acts
    # on the content of 'process_type' column which could only be introduced in alpha releases of AiiDA 1.0.
    # Assuming that 'add' and 'templateplacer' calculations are expected to have both 'type' and 'process_type' columns
    # I will add them based on 'type' column content solely (unlike it is done in the DB migration where the
    # 'type_string' content was also checked).
    if 'Node' in data['export_data']:
        for key, content in data['export_data']['Node'].items():
            if 'type' in content:
                if content['type'] == 'calculation.job.simpleplugins.arithmetic.add.ArithmeticAddCalculation.':
                    content['type'] = 'calculation.job.arithmetic.add.ArithmeticAddCalculation.'
                    content['process_type'] = 'aiida.calculations:arithmetic.add'
                elif content['type'] == 'calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation.':
                    content['type'] = 'calculation.job.templatereplacer.TemplatereplacerCalculation.'
                    content['process_type'] = 'aiida.calculations:templatereplacer'
                elif content['type'] == 'data.code.Code.':
                    if data['node_attributes'][key]['input_plugin'] == 'simpleplugins.arithmetic.add':
                        data['node_attributes'][key]['input_plugin'] = 'arithmetic.add'

                    elif data['node_attributes'][key]['input_plugin'] == 'simpleplugins.templatereplacer':
                        data['node_attributes'][key]['input_plugin'] = 'templatereplacer'

    # Apply migrations: 0020 - REV. 1.0.20
    if 'Node' in data['export_data']:
        migrate_provenance_redesign(data)

    # Apply migrations: 0021 - REV. 1.0.21
    # rename dbgroup fields:
    # name -> label
    # type -> type_string
    # For data.json
    if 'Group' in data['export_data']:
        for content in data['export_data']['Group'].values():
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

    # Apply migrations: 0022 - REV. 1.0.22
    # change type_string according to the following rule:
    # '' -> 'user'
    # 'data.upf.family' -> 'data.upf'
    # 'aiida.import' -> 'auto.import'
    # 'autogroup.run' -> 'auto.run'
    if 'Group' in data['export_data']:
        for key, content in data['export_data']['Group'].items():
            if content['type_string'] == '':
                content['type_string'] = 'user'
            elif content['type_string'] == 'data.upf.family':
                content['type_string'] = 'data.upf'
            elif content['type_string'] == 'aiida.import':
                content['type_string'] = 'auto.import'
            elif content['type_string'] == 'autogroup.run':
                content['type_string'] = 'auto.run'

    # Apply migrations: 0023 - REV. 1.0.23
    # `custom_environment_variables` -> `environment_variables`
    # `jobresource_params` -> `resources`
    # `_process_label` -> `process_label`
    # `parser` -> `parser_name`
    def migration_23(attr_id, content):
        """Apply migration 0023 - REV. 1.0.23 for both `node_attributes*` dicts in `data.json`"""
        if data['export_data']['Node'][attr_id]['type'] == 'node.process.calculation.calcjob.CalcJobNode.':
            for key in content:
                # custom_environment_variables -> environment_variables
                if key == 'custom_environment_variables':
                    content['environment_variables'] = content.pop('custom_environment_variables')
                elif key.startswith(r'custom\_environment\_variables'):
                    new_key = key.replace(r'custom\_environment\_variables', 'environment_variables', 1)
                    content[new_key] = content.pop(key)

                # jobresource_params -> resources
                elif key == 'jobresource_params':
                    content['resources'] = content.pop('jobresource_params')
                elif key.startswith(r'jobresource\_params.'):
                    new_key = key.replace(r'jobresource\_params', 'resources', 1)
                    content[new_key] = content.pop(key)

                # parser -> parser_name
                elif key == 'parser':
                    content['parser_name'] = content.pop('parser')

        # _process_label -> process_label
        elif data['export_data']['Node'][attr_id]['type'].startswith('node.process.'):
            if '_process_label' in content:
                content['process_label'] = content.pop('_process_label')

    # For node_attributes
    for attr_id, content in data['node_attributes'].items():
        if 'type' in data['export_data']['Node'][attr_id]:
            migration_23(attr_id, content)

    # For node_attributes_conversion
    for attr_id, content in data['node_attributes_conversion'].items():
        if 'type' in data['export_data']['Node'][attr_id]:
            migration_23(attr_id, content)

    # Apply migrations: 0025 - REV. 1.0.25
    # The type string for `Data` nodes changed from `data.*` to `node.data.*`.
    if 'Node' in data['export_data']:
        for value in data['export_data']['Node'].values():
            if 'type' in value and value['type'].startswith('data.'):
                value['type'] = value['type'].replace('data.', 'node.data.', 1)

    # Apply migrations: 0026 - REV. 1.0.26 and 0027 - REV. 1.0.27
    # Create the symbols attribute from the repository array for all `TrajectoryData` nodes.
    if 'Node' in data['export_data']:
        for node_id, content in data['export_data']['Node'].items():
            if 'type' in content and content['type'] == 'node.data.array.trajectory.TrajectoryData.':
                uuid = content['uuid']
                symbols_path = os.path.join(
                    folder.get_abs_path('nodes'), uuid[0:2], uuid[2:4], uuid[4:], 'path', 'symbols.npy')
                symbols = np.load(symbols_path).tolist()
                os.remove(symbols_path)
                data['node_attributes'][node_id].pop('array|symbols')
                data['node_attributes'][node_id]['symbols'] = symbols

    # Apply migrations: 0028 - REV. 1.0.28
    # change node type strings:
    # 'node.data.' -> 'data.'
    # 'node.process.' -> 'process.'
    if 'Node' in data['export_data']:
        for value in data['export_data']['Node'].values():
            if 'type' in value:
                if value['type'].startswith('node.data.'):
                    value['type'] = value['type'].replace('node.data.', 'data.', 1)
                elif value['type'].startswith('node.process.'):
                    value['type'] = value['type'].replace('node.process.', 'process.', 1)

    # Apply migration: 0029 - REV. 1.0.29
    # Update ParameterData to Dict
    if 'Node' in data['export_data']:
        for value in data['export_data']['Node'].values():
            if 'type' in value and value['type'] == 'data.parameter.ParameterData.':
                value['type'] = 'data.dict.Dict.'

    # Apply migration: 0030 - REV. 1.0.30
    # Renaming DbNode.type to DbNode.node_type
    # For data.json
    if 'Node' in data['export_data']:
        for content in data['export_data']['Node'].values():
            if 'type' in content:
                content['node_type'] = content.pop('type')
    # For metadata.json
    if 'type' in metadata['all_fields_info']['Node']:
        metadata['all_fields_info']['Node']['node_type'] = metadata['all_fields_info']['Node'].pop('type')

    # Apply migration: 0031 - REV. 1.0.31
    # Remove DbComputer.enabled
    # For data.json
    if 'Computer' in data['export_data']:
        for content in data['export_data']['Computer'].values():
            if 'enabled' in content:
                content.pop('enabled')
    # For metadata.json
    if 'enabled' in metadata['all_fields_info']['Computer']:
        metadata['all_fields_info']['Computer'].pop('enabled')

    # Apply migration 0032 - REV. 1.0.32
    # Remove legacy workflow tables: DbWorkflow, DbWorkflowData, DbWorkflowStep
    # These were (according to Antimo Marrazzo) never exported.

    # Apply migration 0033 - REV. 1.0.33
    # Store dict-values as JSON serializable dicts instead of strings
    # NB! Specific for Django backend
    import six
    from aiida.common import json
    if 'Computer' in data['export_data']:
        for content in data['export_data']['Computer'].values():
            for value in ['metadata', 'transport_params']:
                if isinstance(content[value], six.text_type):
                    content[value] = json.loads(content[value])
    if 'Log' in data['export_data']:
        for content in data['export_data']['Log'].values():
            if isinstance(content['metadata'], six.text_type):
                content['metadata'] = json.loads(content['metadata'])

    # Update metadata.json with the new Log and Comment entities
    new_entities = {
        "Log": {
            "uuid": {},
            "time": {
                "convert_type": "date"
            },
            "loggername": {},
            "levelname": {},
            "message": {},
            "metadata": {},
            "dbnode": {
                "related_name": "dblogs",
                "requires": "Node"
            }
        },
        "Comment": {
            "uuid": {},
            "ctime": {
                "convert_type": "date"
            },
            "mtime": {
                "convert_type": "date"
            },
            "content": {},
            "dbnode": {
                "related_name": "dbcomments",
                "requires": "Node"
            },
            "user": {
                "related_name": "dbcomments",
                "requires": "User"
            }
        }
    }
    metadata['all_fields_info'].update(new_entities)
    metadata['unique_identifiers'].update({"Log": "uuid", "Comment": "uuid"})

    # Update data.json with the new Extras
    # Since Extras were not available previously and usually only include hashes,
    # the Node ids will be added, but included as empty dicts
    node_extras = {}
    node_extras_conversion = {}

    if 'Node' in data['export_data']:
        for node_id in data['export_data']['Node']:
            node_extras[node_id] = {}
            node_extras_conversion[node_id] = {}
    data.update({'node_extras': node_extras, 'node_extras_conversion': node_extras_conversion})
