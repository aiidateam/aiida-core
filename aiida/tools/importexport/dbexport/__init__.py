# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=fixme,too-many-branches,too-many-locals,too-many-statements,too-many-arguments
"""Provides export functionalities."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import tarfile
import time

from aiida import get_version, orm
from aiida.common import json
from aiida.common.folders import RepositoryFolder
from aiida.orm.utils.repository import Repository

from aiida.tools.importexport.common import exceptions
from aiida.tools.importexport.common.config import EXPORT_VERSION, NODES_EXPORT_SUBFOLDER
from aiida.tools.importexport.common.config import (
    NODE_ENTITY_NAME, GROUP_ENTITY_NAME, COMPUTER_ENTITY_NAME, LOG_ENTITY_NAME, COMMENT_ENTITY_NAME
)
from aiida.tools.importexport.common.config import (
    get_all_fields_info, file_fields_to_model_fields, entity_names_to_entities, model_fields_to_file_fields
)
from aiida.tools.importexport.common.utils import export_shard_uuid
from aiida.tools.importexport.dbexport.utils import (
    check_licenses, fill_in_query, serialize_dict, check_process_nodes_sealed, retrieve_linked_nodes
)

from .zip import ZipFolder

__all__ = ('export', 'export_zip')


def export_zip(what, outfile='testzip', overwrite=False, silent=False, use_compression=True, **kwargs):
    """Export in a zipped folder

    :param what: a list of entity instances; they can belong to different models/entities.
    :type what: list

    :param outfile: the filename (possibly including the absolute path) of the file on which to export.
    :type outfile: str

    :param overwrite: if True, overwrite the output file without asking, if it exists. If False, raise an
        :py:class:`~aiida.tools.importexport.common.exceptions.ArchiveExportError` if the output file already exists.
    :type overwrite: bool

    :param silent: suppress prints.
    :type silent: bool

    :param use_compression: Whether or not to compress the zip file.
    :type use_compression: bool

    :param allowed_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type allowed_licenses: list

    :param forbidden_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type forbidden_licenses: list

    :param include_comments: In-/exclude export of comments for given node(s) in ``what``.
        Default: True, *include* comments in export (as well as relevant users).
    :type include_comments: bool

    :param include_logs: In-/exclude export of logs for given node(s) in ``what``.
        Default: True, *include* logs in export.
    :type include_logs: bool

    :param kwargs: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`: if there are any internal errors when
        exporting.
    :raises `~aiida.common.exceptions.LicensingException`: if any node is licensed under forbidden license.
    """
    if not overwrite and os.path.exists(outfile):
        raise exceptions.ArchiveExportError("the output file '{}' already exists".format(outfile))

    time_start = time.time()
    with ZipFolder(outfile, mode='w', use_compression=use_compression) as folder:
        export_tree(what, folder=folder, silent=silent, **kwargs)
    if not silent:
        print('File written in {:10.3g} s.'.format(time.time() - time_start))


def export_tree(
    what,
    folder,
    allowed_licenses=None,
    forbidden_licenses=None,
    silent=False,
    include_comments=True,
    include_logs=True,
    **kwargs
):
    """Export the entries passed in the 'what' list to a file tree.

    :param what: a list of entity instances; they can belong to different models/entities.
    :type what: list

    :param folder: a temporary folder to build the archive before compression.
    :type folder: :py:class:`~aiida.common.folders.Folder`

    :param allowed_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type allowed_licenses: list

    :param forbidden_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type forbidden_licenses: list

    :param silent: suppress prints.
    :type silent: bool

    :param include_comments: In-/exclude export of comments for given node(s) in ``what``.
        Default: True, *include* comments in export (as well as relevant users).
    :type include_comments: bool

    :param include_logs: In-/exclude export of logs for given node(s) in ``what``.
        Default: True, *include* logs in export.
    :type include_logs: bool

    :param kwargs: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`: if there are any internal errors when
        exporting.
    :raises `~aiida.common.exceptions.LicensingException`: if any node is licensed under forbidden license.
    """
    from collections import defaultdict

    if not silent:
        print('STARTING EXPORT...')

    all_fields_info, unique_identifiers = get_all_fields_info()

    entities_starting_set = defaultdict(set)

    # The set that contains the nodes ids of the nodes that should be exported
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
        if issubclass(entry.__class__, orm.Group):
            entities_starting_set[GROUP_ENTITY_NAME].add(entry.uuid)
            given_group_entry_ids.add(entry.id)
            given_groups.add(entry)
        elif issubclass(entry.__class__, orm.Node):
            entities_starting_set[NODE_ENTITY_NAME].add(entry.uuid)
            if issubclass(entry.__class__, orm.Data):
                given_data_entry_ids.add(entry.pk)
            elif issubclass(entry.__class__, orm.ProcessNode):
                given_calculation_entry_ids.add(entry.pk)
        elif issubclass(entry.__class__, orm.Computer):
            entities_starting_set[COMPUTER_ENTITY_NAME].add(entry.uuid)
            given_computer_entry_ids.add(entry.pk)
        else:
            raise exceptions.ArchiveExportError(
                'I was given {} ({}), which is not a Node, Computer, or Group instance'.format(entry, type(entry))
            )

    # Add all the nodes contained within the specified groups
    for group in given_groups:
        for entry in group.nodes:
            entities_starting_set[NODE_ENTITY_NAME].add(entry.uuid)
            if issubclass(entry.__class__, orm.Data):
                given_data_entry_ids.add(entry.pk)
            elif issubclass(entry.__class__, orm.ProcessNode):
                given_calculation_entry_ids.add(entry.pk)

    for entity, entity_set in entities_starting_set.items():
        entities_starting_set[entity] = list(entity_set)

    # We will iteratively explore the AiiDA graph to find further nodes that
    # should also be exported.
    # At the same time, we will create the links_uuid list of dicts to be exported

    if not silent:
        print('RETRIEVING LINKED NODES AND STORING LINKS...')

    to_be_exported, links_uuid, graph_traversal_rules = retrieve_linked_nodes(
        given_calculation_entry_ids, given_data_entry_ids, **kwargs
    )

    ## Universal "entities" attributed to all types of nodes
    # Logs
    if include_logs and to_be_exported:
        # Get related log(s) - universal for all nodes
        builder = orm.QueryBuilder()
        builder.append(orm.Log, filters={'dbnode_id': {'in': to_be_exported}}, project='id')
        res = {_[0] for _ in builder.all()}
        given_log_entry_ids.update(res)

    # Comments
    if include_comments and to_be_exported:
        # Get related log(s) - universal for all nodes
        builder = orm.QueryBuilder()
        builder.append(orm.Comment, filters={'dbnode_id': {'in': to_be_exported}}, project='id')
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
        project_cols = ['id']
        # The following gets a list of fields that we need,
        # e.g. user, mtime, uuid, computer
        entity_prop = all_fields_info[given_entity].keys()

        # Here we do the necessary renaming of properties
        for prop in entity_prop:
            # nprop contains the list of projections
            nprop = (
                file_fields_to_model_fields[given_entity][prop]
                if prop in file_fields_to_model_fields[given_entity] else prop
            )
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

        builder = orm.QueryBuilder()
        builder.append(
            entity_names_to_entities[given_entity],
            filters={'id': {
                'in': entry_ids_to_add
            }},
            project=project_cols,
            tag=given_entity,
            outerjoin=True
        )
        entries_to_add[given_entity] = builder

    # TODO (Spyros) To see better! Especially for functional licenses
    # Check the licenses of exported data.
    if allowed_licenses is not None or forbidden_licenses is not None:
        builder = orm.QueryBuilder()
        builder.append(orm.Node, project=['id', 'attributes.source.license'], filters={'id': {'in': to_be_exported}})
        # Skip those nodes where the license is not set (this is the standard behavior with Django)
        node_licenses = list((a, b) for [a, b] in builder.all() if b is not None)
        check_licenses(node_licenses, allowed_licenses, forbidden_licenses)

    ############################################################
    ##### Start automatic recursive export data generation #####
    ############################################################
    if not silent:
        print('STORING DATABASE ENTRIES...')

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
                if temp_d[k]['id'] is None:
                    continue

                temp_d2 = {
                    temp_d[k]['id']:
                    serialize_dict(
                        temp_d[k], remove_fields=['id'], rename_fields=model_fields_to_file_fields[current_entity]
                    )
                }
                try:
                    export_data[current_entity].update(temp_d2)
                except KeyError:
                    export_data[current_entity] = temp_d2

    #######################################
    # Manually manage attributes and extras
    #######################################
    # I use .get because there may be no nodes to export
    all_nodes_pk = list()
    if NODE_ENTITY_NAME in export_data:
        all_nodes_pk.extend(export_data.get(NODE_ENTITY_NAME).keys())

    if sum(len(model_data) for model_data in export_data.values()) == 0:
        if not silent:
            print('No nodes to store, exiting...')
        return

    if not silent:
        print(
            'Exporting a total of {} db entries, of which {} nodes.'.format(
                sum(len(model_data) for model_data in export_data.values()), len(all_nodes_pk)
            )
        )

    # ATTRIBUTES and EXTRAS
    if not silent:
        print('STORING NODE ATTRIBUTES AND EXTRAS...')
    node_attributes = {}
    node_extras = {}

    # A second QueryBuilder query to get the attributes and extras. See if this can be optimized
    if all_nodes_pk:
        all_nodes_query = orm.QueryBuilder()
        all_nodes_query.append(orm.Node, filters={'id': {'in': all_nodes_pk}}, project=['id', 'attributes', 'extras'])
        for res_pk, res_attributes, res_extras in all_nodes_query.iterall():
            node_attributes[str(res_pk)] = res_attributes
            node_extras[str(res_pk)] = res_extras

    if not silent:
        print('STORING GROUP ELEMENTS...')
    groups_uuid = dict()
    # If a group is in the exported date, we export the group/node correlation
    if GROUP_ENTITY_NAME in export_data:
        for curr_group in export_data[GROUP_ENTITY_NAME]:
            group_uuid_qb = orm.QueryBuilder()
            group_uuid_qb.append(
                entity_names_to_entities[GROUP_ENTITY_NAME],
                filters={'id': {
                    '==': curr_group
                }},
                project=['uuid'],
                tag='group'
            )
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
    nodesubfolder = folder.get_subfolder(NODES_EXPORT_SUBFOLDER, create=True, reset_limit=True)

    if not silent:
        print('STORING DATA...')

    data = {
        'node_attributes': node_attributes,
        'node_extras': node_extras,
        'export_data': export_data,
        'links_uuid': links_uuid,
        'groups_uuid': groups_uuid
    }

    # N.B. We're really calling zipfolder.open (if exporting a zipfile)
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
        'export_parameters': {
            'graph_traversal_rules': graph_traversal_rules,
            'entities_starting_set': entities_starting_set,
            'include_comments': include_comments,
            'include_logs': include_logs
        }
    }

    with folder.open('metadata.json', 'w') as fhandle:
        fhandle.write(json.dumps(metadata))

    if silent is not True:
        print('STORING REPOSITORY FILES...')

    # If there are no nodes, there are no repository files to store
    if all_nodes_pk:
        # Large speed increase by not getting the node itself and looping in memory in python, but just getting the uuid
        uuid_query = orm.QueryBuilder()
        uuid_query.append(orm.Node, filters={'id': {'in': all_nodes_pk}}, project=['uuid'])
        for res in uuid_query.all():
            uuid = str(res[0])
            sharded_uuid = export_shard_uuid(uuid)

            # Important to set create=False, otherwise creates twice a subfolder. Maybe this is a bug of insert_path?
            thisnodefolder = nodesubfolder.get_subfolder(sharded_uuid, create=False, reset_limit=True)

            # Make sure the node's repository folder was not deleted
            src = RepositoryFolder(section=Repository._section_name, uuid=uuid)  # pylint: disable=protected-access
            if not src.exists():
                raise exceptions.ArchiveExportError(
                    'Unable to find the repository folder for Node with UUID={} in the local repository'.format(uuid)
                )

            # In this way, I copy the content of the folder, and not the folder itself
            thisnodefolder.insert_path(src=src.abspath, dest_name='.')


def export(what, outfile='export_data.aiida.tar.gz', overwrite=False, silent=False, **kwargs):
    """Export the entries passed in the 'what' list to a file tree.

    :param what: a list of entity instances; they can belong to different models/entities.
    :type what: list

    :param outfile: the filename (possibly including the absolute path) of the file on which to export.
    :type outfile: str

    :param overwrite: if True, overwrite the output file without asking, if it exists. If False, raise an
        :py:class:`~aiida.tools.importexport.common.exceptions.ArchiveExportError` if the output file already exists.
    :type overwrite: bool

    :param silent: suppress prints.
    :type silent: bool

    :param allowed_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type allowed_licenses: list

    :param forbidden_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type forbidden_licenses: list

    :param include_comments: In-/exclude export of comments for given node(s) in ``what``.
        Default: True, *include* comments in export (as well as relevant users).
    :type include_comments: bool

    :param include_logs: In-/exclude export of logs for given node(s) in ``what``.
        Default: True, *include* logs in export.
    :type include_logs: bool

    :param kwargs: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`: if there are any internal errors when
        exporting.
    :raises `~aiida.common.exceptions.LicensingException`: if any node is licensed under forbidden license.
    """
    from aiida.common.folders import SandboxFolder

    if not overwrite and os.path.exists(outfile):
        raise exceptions.ArchiveExportError("The output file '{}' already exists".format(outfile))

    folder = SandboxFolder()
    time_export_start = time.time()
    export_tree(what, folder=folder, silent=silent, **kwargs)

    time_export_end = time.time()

    if not silent:
        print('COMPRESSING...')

    time_compress_start = time.time()
    with tarfile.open(outfile, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as tar:
        tar.add(folder.abspath, arcname='')
    time_compress_end = time.time()

    if not silent:
        filecr_time = time_export_end - time_export_start
        filecomp_time = time_compress_end - time_compress_start
        print(
            'Exported in {:6.2g}s, compressed in {:6.2g}s, total: {:6.2g}s.'.format(
                filecr_time, filecomp_time, filecr_time + filecomp_time
            )
        )

    if not silent:
        print('DONE.')
