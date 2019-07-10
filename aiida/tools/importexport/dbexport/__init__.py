# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=fixme,protected-access,too-many-branches,too-many-locals,too-many-statements,too-many-arguments
"""Provides export functionalities."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import tarfile
import time

from aiida import get_version
from aiida.common import json
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.links import LinkType
from aiida.common.utils import export_shard_uuid
from aiida.orm import QueryBuilder, Node, Data, Group, Log, Comment, Computer, ProcessNode
from aiida.orm.utils.repository import Repository

from aiida.tools.importexport.dbexport.utils import (check_licences, fill_in_query, serialize_dict,
                                                     check_process_nodes_sealed)
from aiida.tools.importexport.config import (NODE_ENTITY_NAME, GROUP_ENTITY_NAME, COMPUTER_ENTITY_NAME, LOG_ENTITY_NAME,
                                             COMMENT_ENTITY_NAME, EXPORT_VERSION)
from aiida.tools.importexport.config import (get_all_fields_info, file_fields_to_model_fields, entity_names_to_entities,
                                             model_fields_to_file_fields)

from .zip import *  # pylint: disable=wildcard-import

__all__ = ('export_tree', 'export') + zip.__all__  # pylint: disable=no-member


def export_tree(what,
                folder,
                allowed_licenses=None,
                forbidden_licenses=None,
                silent=False,
                input_forward=False,
                create_reversed=True,
                return_reversed=False,
                call_reversed=False,
                include_comments=True,
                include_logs=True):
    """
    Export the entries passed in the 'what' list to a file tree.
    :todo: limit the export to finished or failed calculations.
    :param what: a list of entity instances; they can belong to
    different models/entities.
    :param folder: a :py:class:`Folder <aiida.common.folders.Folder>` object
    :param input_forward: Follow forward INPUT links (recursively) when
    calculating the node set to export.
    :param create_reversed: Follow reversed CREATE links (recursively) when
    calculating the node set to export.
    :param return_reversed: Follow reversed RETURN links (recursively) when
    calculating the node set to export.
    :param call_reversed: Follow reversed CALL links (recursively) when
    calculating the node set to export.
    :param allowed_licenses: a list or a function. If a list, then checks
    whether all licenses of Data nodes are in the list. If a function,
    then calls function for licenses of Data nodes expecting True if
    license is allowed, False otherwise.
    :param forbidden_licenses: a list or a function. If a list, then checks
    whether all licenses of Data nodes are in the list. If a function,
    then calls function for licenses of Data nodes expecting True if
    license is allowed, False otherwise.
    :param include_comments: Bool: In-/exclude export of comments for given node(s).
    Default: True, *include* comments in export (as well as relevant users).
    :param include_logs: Bool: In-/exclude export of logs for given node(s).
    Default: True, *include* logs in export.
    :param silent: suppress debug prints
    :raises LicensingException: if any node is licensed under forbidden
    license
    """
    if not silent:
        print("STARTING EXPORT...")

    all_fields_info, unique_identifiers = get_all_fields_info()

    # The set that contains the nodes ids of the nodes that should be exported
    to_be_exported = set()

    given_data_entry_ids = set()
    given_calculation_entry_ids = set()
    given_group_entry_ids = set()
    given_computer_entry_ids = set()
    given_groups = set()
    given_log_entry_ids = set()
    given_comment_entry_ids = set()

    # I store a list of the actual dbnodes
    for entry in what:
        # This returns the class name (as in imports). E.g. for a model node:
        # aiida.backends.djsite.db.models.DbNode
        # entry_class_string = get_class_string(entry)
        # Now a load the backend-independent name into entry_entity_name, e.g. Node!
        # entry_entity_name = schema_to_entity_names(entry_class_string)
        if issubclass(entry.__class__, Group):
            given_group_entry_ids.add(entry.id)
            given_groups.add(entry)
        elif issubclass(entry.__class__, Node):
            if issubclass(entry.__class__, Data):
                given_data_entry_ids.add(entry.pk)
            elif issubclass(entry.__class__, ProcessNode):
                given_calculation_entry_ids.add(entry.pk)
        elif issubclass(entry.__class__, Computer):
            given_computer_entry_ids.add(entry.pk)
        else:
            raise ValueError("I was given {} ({}), which is not a Node, Computer, or Group instance".format(
                entry, type(entry)))

    # Add all the nodes contained within the specified groups
    for group in given_groups:
        for entry in group.nodes:
            if issubclass(entry.__class__, Data):
                given_data_entry_ids.add(entry.pk)
            elif issubclass(entry.__class__, ProcessNode):
                given_calculation_entry_ids.add(entry.pk)

    # We will iteratively explore the AiiDA graph to find further nodes that
    # should also be exported.

    # We repeat until there are no further nodes to be visited
    while given_calculation_entry_ids or given_data_entry_ids:

        # If is is a calculation node
        if given_calculation_entry_ids:
            curr_node_id = given_calculation_entry_ids.pop()
            # If it is already visited continue to the next node
            if curr_node_id in to_be_exported:
                continue
            # Otherwise say that it is a node to be exported
            else:
                to_be_exported.add(curr_node_id)

            # INPUT(Data, ProcessNode) - Reversed
            builder = QueryBuilder()
            builder.append(Data, tag='predecessor', project=['id'])
            builder.append(
                ProcessNode,
                with_incoming='predecessor',
                filters={'id': {
                    '==': curr_node_id
                }},
                edge_filters={'type': {
                    'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]
                }})
            res = {_[0] for _ in builder.all()}
            given_data_entry_ids.update(res - to_be_exported)

            # INPUT(Data, ProcessNode) - Forward
            if input_forward:
                builder = QueryBuilder()
                builder.append(Data, tag='predecessor', project=['id'], filters={'id': {'==': curr_node_id}})
                builder.append(
                    ProcessNode,
                    with_incoming='predecessor',
                    edge_filters={'type': {
                        'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]
                    }})
                res = {_[0] for _ in builder.all()}
                given_data_entry_ids.update(res - to_be_exported)

            # CREATE/RETURN(ProcessNode, Data) - Forward
            builder = QueryBuilder()
            builder.append(ProcessNode, tag='predecessor', filters={'id': {'==': curr_node_id}})
            builder.append(
                Data,
                with_incoming='predecessor',
                project=['id'],
                edge_filters={'type': {
                    'in': [LinkType.CREATE.value, LinkType.RETURN.value]
                }})
            res = {_[0] for _ in builder.all()}
            given_data_entry_ids.update(res - to_be_exported)

            # CREATE(ProcessNode, Data) - Reversed
            if create_reversed:
                builder = QueryBuilder()
                builder.append(ProcessNode, tag='predecessor')
                builder.append(
                    Data,
                    with_incoming='predecessor',
                    project=['id'],
                    filters={'id': {
                        '==': curr_node_id
                    }},
                    edge_filters={'type': {
                        'in': [LinkType.CREATE.value]
                    }})
                res = {_[0] for _ in builder.all()}
                given_data_entry_ids.update(res - to_be_exported)

            # RETURN(ProcessNode, Data) - Reversed
            if return_reversed:
                builder = QueryBuilder()
                builder.append(ProcessNode, tag='predecessor')
                builder.append(
                    Data,
                    with_incoming='predecessor',
                    project=['id'],
                    filters={'id': {
                        '==': curr_node_id
                    }},
                    edge_filters={'type': {
                        'in': [LinkType.RETURN.value]
                    }})
                res = {_[0] for _ in builder.all()}
                given_data_entry_ids.update(res - to_be_exported)

            # CALL(ProcessNode, ProcessNode) - Forward
            builder = QueryBuilder()
            builder.append(ProcessNode, tag='predecessor', filters={'id': {'==': curr_node_id}})
            builder.append(
                ProcessNode,
                with_incoming='predecessor',
                project=['id'],
                edge_filters={'type': {
                    'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]
                }})
            res = {_[0] for _ in builder.all()}
            given_calculation_entry_ids.update(res - to_be_exported)

            # CALL(ProcessNode, ProcessNode) - Reversed
            if call_reversed:
                builder = QueryBuilder()
                builder.append(ProcessNode, tag='predecessor')
                builder.append(
                    ProcessNode,
                    with_incoming='predecessor',
                    project=['id'],
                    filters={'id': {
                        '==': curr_node_id
                    }},
                    edge_filters={'type': {
                        'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]
                    }})
                res = {_[0] for _ in builder.all()}
                given_calculation_entry_ids.update(res - to_be_exported)

        # If it is a Data node
        else:
            curr_node_id = given_data_entry_ids.pop()
            # If it is already visited continue to the next node
            if curr_node_id in to_be_exported:
                continue
            # Otherwise say that it is a node to be exported
            else:
                to_be_exported.add(curr_node_id)

            # Case 2:
            # CREATE(ProcessNode, Data) - Reversed
            if create_reversed:
                builder = QueryBuilder()
                builder.append(ProcessNode, tag='predecessor', project=['id'])
                builder.append(
                    Data,
                    with_incoming='predecessor',
                    filters={'id': {
                        '==': curr_node_id
                    }},
                    edge_filters={'type': {
                        'in': [LinkType.CREATE.value]
                    }})
                res = {_[0] for _ in builder.all()}
                given_calculation_entry_ids.update(res - to_be_exported)

            # Case 3:
            # RETURN(ProcessNode, Data) - Reversed
            if return_reversed:
                builder = QueryBuilder()
                builder.append(ProcessNode, tag='predecessor', project=['id'])
                builder.append(
                    Data,
                    with_incoming='predecessor',
                    filters={'id': {
                        '==': curr_node_id
                    }},
                    edge_filters={'type': {
                        'in': [LinkType.RETURN.value]
                    }})
                res = {_[0] for _ in builder.all()}
                given_calculation_entry_ids.update(res - to_be_exported)

    ## Universal "entities" attributed to all types of nodes
    # Logs
    if include_logs and to_be_exported:
        # Get related log(s) - universal for all nodes
        builder = QueryBuilder()
        builder.append(Log, filters={'dbnode_id': {'in': to_be_exported}}, project=['id'])
        res = {_[0] for _ in builder.all()}
        given_log_entry_ids.update(res)

    # Comments
    if include_comments and to_be_exported:
        # Get related log(s) - universal for all nodes
        builder = QueryBuilder()
        builder.append(Comment, filters={'dbnode_id': {'in': to_be_exported}}, project=['id'])
        res = {_[0] for _ in builder.all()}
        given_comment_entry_ids.update(res)

    # Here we get all the columns that we plan to project per entity that we
    # would like to extract
    given_entities = list()
    if given_group_entry_ids:
        given_entities.append(GROUP_ENTITY_NAME)
    if to_be_exported:
        given_entities.append(NODE_ENTITY_NAME)
    if given_computer_entry_ids:
        given_entities.append(COMPUTER_ENTITY_NAME)
    if given_log_entry_ids:
        given_entities.append(LOG_ENTITY_NAME)
    if given_comment_entry_ids:
        given_entities.append(COMMENT_ENTITY_NAME)

    entries_to_add = dict()
    for given_entity in given_entities:
        project_cols = ["id"]
        # The following gets a list of fields that we need,
        # e.g. user, mtime, uuid, computer
        entity_prop = all_fields_info[given_entity].keys()

        # Here we do the necessary renaming of properties
        for prop in entity_prop:
            # nprop contains the list of projections
            nprop = (file_fields_to_model_fields[given_entity][prop]
                     if prop in file_fields_to_model_fields[given_entity] else prop)
            project_cols.append(nprop)

        # Getting the ids that correspond to the right entity
        if given_entity == GROUP_ENTITY_NAME:
            entry_ids_to_add = given_group_entry_ids
        elif given_entity == NODE_ENTITY_NAME:
            entry_ids_to_add = to_be_exported
        elif given_entity == COMPUTER_ENTITY_NAME:
            entry_ids_to_add = given_computer_entry_ids
        elif given_entity == LOG_ENTITY_NAME:
            entry_ids_to_add = given_log_entry_ids
        elif given_entity == COMMENT_ENTITY_NAME:
            entry_ids_to_add = given_comment_entry_ids

        builder = QueryBuilder()
        builder.append(
            entity_names_to_entities[given_entity],
            filters={"id": {
                "in": entry_ids_to_add
            }},
            project=project_cols,
            tag=given_entity,
            outerjoin=True)
        entries_to_add[given_entity] = builder

    # TODO (Spyros) To see better! Especially for functional licenses
    # Check the licenses of exported data.
    if allowed_licenses is not None or forbidden_licenses is not None:
        builder = QueryBuilder()
        builder.append(Node, project=["id", "attributes.source.license"], filters={"id": {"in": to_be_exported}})
        # Skip those nodes where the license is not set (this is the standard behavior with Django)
        node_licenses = list((a, b) for [a, b] in builder.all() if b is not None)
        check_licences(node_licenses, allowed_licenses, forbidden_licenses)

    ############################################################
    ##### Start automatic recursive export data generation #####
    ############################################################
    if not silent:
        print("STORING DATABASE ENTRIES...")

    export_data = dict()
    entity_separator = '_'
    for entity_name, partial_query in entries_to_add.items():

        foreign_fields = {
            k: v
            for k, v in all_fields_info[entity_name].items()
            # all_fields_info[model_name].items()
            if 'requires' in v
        }

        for value in foreign_fields.values():
            ref_model_name = value['requires']
            fill_in_query(partial_query, entity_name, ref_model_name, [entity_name], entity_separator)

        for temp_d in partial_query.iterdict():
            for k in temp_d.keys():
                # Get current entity
                current_entity = k.split(entity_separator)[-1]

                # This is a empty result of an outer join.
                # It should not be taken into account.
                if temp_d[k]["id"] is None:
                    continue

                temp_d2 = {
                    temp_d[k]["id"]:
                    serialize_dict(
                        temp_d[k], remove_fields=['id'], rename_fields=model_fields_to_file_fields[current_entity])
                }
                try:
                    export_data[current_entity].update(temp_d2)
                except KeyError:
                    export_data[current_entity] = temp_d2

    ######################################
    # Manually manage links and attributes
    ######################################
    # I use .get because there may be no nodes to export
    all_nodes_pk = list()
    if NODE_ENTITY_NAME in export_data:
        all_nodes_pk.extend(export_data.get(NODE_ENTITY_NAME).keys())

    if sum(len(model_data) for model_data in export_data.values()) == 0:
        if not silent:
            print("No nodes to store, exiting...")
        return

    if not silent:
        print("Exporting a total of {} db entries, of which {} nodes.".format(
            sum(len(model_data) for model_data in export_data.values()), len(all_nodes_pk)))

    ## ATTRIBUTES
    if not silent:
        print("STORING NODE ATTRIBUTES...")
    node_attributes = {}

    # A second QueryBuilder query to get the attributes. See if this can be optimized
    if all_nodes_pk:
        all_nodes_query = QueryBuilder()
        all_nodes_query.append(Node, filters={"id": {"in": all_nodes_pk}}, project=["*"])
        for res in all_nodes_query.iterall():
            node_attributes[str(res[0].pk)] = res[0].attributes

    ## EXTRAS
    if not silent:
        print("STORING NODE EXTRAS...")
    node_extras = {}

    # A second QueryBuilder query to get the extras. See if this can be optimized
    if all_nodes_pk:
        all_nodes_query = QueryBuilder()
        all_nodes_query.append(Node, filters={"id": {"in": all_nodes_pk}}, project=["*"])
        for res in all_nodes_query.iterall():
            node_extras[str(res[0].pk)] = res[0].extras

    if not silent:
        print("STORING NODE LINKS...")

    links_uuid_dict = dict()
    if all_nodes_pk:
        # INPUT (Data, ProcessNode) - Forward, by the ProcessNode node
        if input_forward:
            # INPUT (Data, ProcessNode)
            links_qb = QueryBuilder()
            links_qb.append(Data, project=['uuid'], tag='input', filters={'id': {'in': all_nodes_pk}})
            links_qb.append(
                ProcessNode,
                project=['uuid'],
                tag='output',
                edge_filters={'type': {
                    'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]
                }},
                edge_project=['label', 'type'],
                with_incoming='input')
            for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
                val = {
                    'input': str(input_uuid),
                    'output': str(output_uuid),
                    'label': str(link_label),
                    'type': str(link_type)
                }
                links_uuid_dict[frozenset(val.items())] = val

        # INPUT (Data, ProcessNode) - Backward, by the ProcessNode node
        links_qb = QueryBuilder()
        links_qb.append(Data, project=['uuid'], tag='input')
        links_qb.append(
            ProcessNode,
            project=['uuid'],
            tag='output',
            filters={'id': {
                'in': all_nodes_pk
            }},
            edge_filters={'type': {
                'in': [LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value]
            }},
            edge_project=['label', 'type'],
            with_incoming='input')
        for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
            val = {
                'input': str(input_uuid),
                'output': str(output_uuid),
                'label': str(link_label),
                'type': str(link_type)
            }
            links_uuid_dict[frozenset(val.items())] = val

        # CREATE (ProcessNode, Data) - Forward, by the ProcessNode node
        links_qb = QueryBuilder()
        links_qb.append(ProcessNode, project=['uuid'], tag='input', filters={'id': {'in': all_nodes_pk}})
        links_qb.append(
            Data,
            project=['uuid'],
            tag='output',
            edge_filters={'type': {
                '==': LinkType.CREATE.value
            }},
            edge_project=['label', 'type'],
            with_incoming='input')
        for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
            val = {
                'input': str(input_uuid),
                'output': str(output_uuid),
                'label': str(link_label),
                'type': str(link_type)
            }
            links_uuid_dict[frozenset(val.items())] = val

        # CREATE (ProcessNode, Data) - Backward, by the Data node
        if create_reversed:
            links_qb = QueryBuilder()
            links_qb.append(ProcessNode, project=['uuid'], tag='input', filters={'id': {'in': all_nodes_pk}})
            links_qb.append(
                Data,
                project=['uuid'],
                tag='output',
                edge_filters={'type': {
                    '==': LinkType.CREATE.value
                }},
                edge_project=['label', 'type'],
                with_incoming='input')
            for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
                val = {
                    'input': str(input_uuid),
                    'output': str(output_uuid),
                    'label': str(link_label),
                    'type': str(link_type)
                }
                links_uuid_dict[frozenset(val.items())] = val

        # RETURN (ProcessNode, Data) - Forward, by the ProcessNode node
        links_qb = QueryBuilder()
        links_qb.append(ProcessNode, project=['uuid'], tag='input', filters={'id': {'in': all_nodes_pk}})
        links_qb.append(
            Data,
            project=['uuid'],
            tag='output',
            edge_filters={'type': {
                '==': LinkType.RETURN.value
            }},
            edge_project=['label', 'type'],
            with_incoming='input')
        for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
            val = {
                'input': str(input_uuid),
                'output': str(output_uuid),
                'label': str(link_label),
                'type': str(link_type)
            }
            links_uuid_dict[frozenset(val.items())] = val

        # RETURN (ProcessNode, Data) - Backward, by the Data node
        if return_reversed:
            links_qb = QueryBuilder()
            links_qb.append(ProcessNode, project=['uuid'], tag='input')
            links_qb.append(
                Data,
                project=['uuid'],
                tag='output',
                filters={'id': {
                    'in': all_nodes_pk
                }},
                edge_filters={'type': {
                    '==': LinkType.RETURN.value
                }},
                edge_project=['label', 'type'],
                with_incoming='input')
            for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
                val = {
                    'input': str(input_uuid),
                    'output': str(output_uuid),
                    'label': str(link_label),
                    'type': str(link_type)
                }
                links_uuid_dict[frozenset(val.items())] = val

        # CALL (ProcessNode [caller], ProcessNode [called]) - Forward, by
        # the ProcessNode node
        links_qb = QueryBuilder()
        links_qb.append(ProcessNode, project=['uuid'], tag='input', filters={'id': {'in': all_nodes_pk}})
        links_qb.append(
            ProcessNode,
            project=['uuid'],
            tag='output',
            edge_filters={'type': {
                'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]
            }},
            edge_project=['label', 'type'],
            with_incoming='input')
        for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
            val = {
                'input': str(input_uuid),
                'output': str(output_uuid),
                'label': str(link_label),
                'type': str(link_type)
            }
            links_uuid_dict[frozenset(val.items())] = val

        # CALL (ProcessNode [caller], ProcessNode [called]) - Backward,
        # by the ProcessNode [called] node
        if call_reversed:
            links_qb = QueryBuilder()
            links_qb.append(ProcessNode, project=['uuid'], tag='input')
            links_qb.append(
                ProcessNode,
                project=['uuid'],
                tag='output',
                filters={'id': {
                    'in': all_nodes_pk
                }},
                edge_filters={'type': {
                    'in': [LinkType.CALL_CALC.value, LinkType.CALL_WORK.value]
                }},
                edge_project=['label', 'type'],
                with_incoming='input')
            for input_uuid, output_uuid, link_label, link_type in links_qb.iterall():
                val = {
                    'input': str(input_uuid),
                    'output': str(output_uuid),
                    'label': str(link_label),
                    'type': str(link_type)
                }
                links_uuid_dict[frozenset(val.items())] = val

    links_uuid = list(links_uuid_dict.values())

    if not silent:
        print("STORING GROUP ELEMENTS...")
    groups_uuid = dict()
    # If a group is in the exported date, we export the group/node correlation
    if GROUP_ENTITY_NAME in export_data:
        for curr_group in export_data[GROUP_ENTITY_NAME]:
            group_uuid_qb = QueryBuilder()
            group_uuid_qb.append(
                entity_names_to_entities[GROUP_ENTITY_NAME],
                filters={'id': {
                    '==': curr_group
                }},
                project=['uuid'],
                tag='group')
            group_uuid_qb.append(entity_names_to_entities[NODE_ENTITY_NAME], project=['uuid'], with_group='group')
            for res in group_uuid_qb.iterall():
                if str(res[0]) in groups_uuid:
                    groups_uuid[str(res[0])].append(str(res[1]))
                else:
                    groups_uuid[str(res[0])] = [str(res[1])]

    #######################################
    # Final check for unsealed ProcessNodes
    #######################################
    process_nodes = set()
    for node_pk, content in export_data.get(NODE_ENTITY_NAME, {}).items():
        if content['node_type'].startswith('process.'):
            process_nodes.add(node_pk)

    check_process_nodes_sealed(process_nodes)

    ######################################
    # Now I store
    ######################################
    # subfolder inside the export package
    nodesubfolder = folder.get_subfolder('nodes', create=True, reset_limit=True)

    if not silent:
        print("STORING DATA...")

    data = {
        'node_attributes': node_attributes,
        'node_extras': node_extras,
        'export_data': export_data,
        'links_uuid': links_uuid,
        'groups_uuid': groups_uuid,
    }

    # N.B. We're really calling zipfolder.open
    with folder.open('data.json', mode='w') as fhandle:
        # fhandle.write(json.dumps(data, cls=UUIDEncoder))
        fhandle.write(json.dumps(data))

    # Add proper signature to unique identifiers & all_fields_info
    # Ignore if a key doesn't exist in any of the two dictionaries

    metadata = {
        'aiida_version': get_version(),
        'export_version': EXPORT_VERSION,
        'all_fields_info': all_fields_info,
        'unique_identifiers': unique_identifiers,
    }

    with folder.open('metadata.json', "w") as fhandle:
        fhandle.write(json.dumps(metadata))

    if silent is not True:
        print("STORING FILES...")

    # If there are no nodes, there are no files to store
    if all_nodes_pk:
        # Large speed increase by not getting the node itself and looping in memory
        # in python, but just getting the uuid
        uuid_query = QueryBuilder()
        uuid_query.append(Node, filters={"id": {"in": all_nodes_pk}}, project=["uuid"])
        for res in uuid_query.all():
            uuid = str(res[0])
            sharded_uuid = export_shard_uuid(uuid)

            # Important to set create=False, otherwise creates
            # twice a subfolder. Maybe this is a bug of insert_path??
            thisnodefolder = nodesubfolder.get_subfolder(sharded_uuid, create=False, reset_limit=True)
            # In this way, I copy the content of the folder, and not the folder itself
            src = RepositoryFolder(section=Repository._section_name, uuid=uuid).abspath
            thisnodefolder.insert_path(src=src, dest_name='.')


def export(what, outfile='export_data.aiida.tar.gz', overwrite=False, silent=False, **kwargs):
    """
    Export the entries passed in the 'what' list to a file tree.
    :todo: limit the export to finished or failed calculations.
    :param what: a list of entity instances; they can belong to
    different models/entities.
    :param input_forward: Follow forward INPUT links (recursively) when
    calculating the node set to export.
    :param create_reversed: Follow reversed CREATE links (recursively) when
    calculating the node set to export.
    :param return_reversed: Follow reversed RETURN links (recursively) when
    calculating the node set to export.
    :param call_reversed: Follow reversed CALL links (recursively) when
    calculating the node set to export.
    :param allowed_licenses: a list or a function. If a list, then checks
    whether all licenses of Data nodes are in the list. If a function,
    then calls function for licenses of Data nodes expecting True if
    license is allowed, False otherwise.
    :param forbidden_licenses: a list or a function. If a list, then checks
    whether all licenses of Data nodes are in the list. If a function,
    then calls function for licenses of Data nodes expecting True if
    license is allowed, False otherwise.
    :param outfile: the filename of the file on which to export
    :param overwrite: if True, overwrite the output file without asking.
    if False, raise an IOError in this case.
    :param silent: suppress debug print

    :raise IOError: if overwrite==False and the filename already exists.
    """
    if not overwrite and os.path.exists(outfile):
        raise IOError("The output file '{}' already exists".format(outfile))

    folder = SandboxFolder()
    time_export_start = time.time()
    export_tree(what, folder=folder, silent=silent, **kwargs)

    time_export_end = time.time()

    if not silent:
        print("COMPRESSING...")

    time_compress_start = time.time()
    with tarfile.open(outfile, "w:gz", format=tarfile.PAX_FORMAT, dereference=True) as tar:
        tar.add(folder.abspath, arcname="")
    time_compress_end = time.time()

    if not silent:
        filecr_time = time_export_end - time_export_start
        filecomp_time = time_compress_end - time_compress_start
        print("Exported in {:6.2g}s, compressed in {:6.2g}s, total: {:6.2g}s.".format(
            filecr_time, filecomp_time, filecr_time + filecomp_time))

    if not silent:
        print("DONE.")
