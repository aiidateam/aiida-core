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

import os
import tarfile
import time

from tqdm import tqdm

from aiida import get_version, orm
from aiida.common import json
from aiida.common.exceptions import LicensingException
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.orm.utils.repository import Repository

from aiida.tools.importexport.common import exceptions
from aiida.tools.importexport.common.config import EXPORT_VERSION, NODES_EXPORT_SUBFOLDER, BAR_FORMAT
from aiida.tools.importexport.common.config import (
    NODE_ENTITY_NAME, GROUP_ENTITY_NAME, COMPUTER_ENTITY_NAME, LOG_ENTITY_NAME, COMMENT_ENTITY_NAME
)
from aiida.tools.importexport.common.config import (
    get_all_fields_info, file_fields_to_model_fields, entity_names_to_entities, model_fields_to_file_fields
)
from aiida.tools.importexport.common.utils import export_shard_uuid
from aiida.tools.importexport.dbexport.utils import (
    check_licenses, fill_in_query, serialize_dict, check_process_nodes_sealed, summary, EXPORT_LOGGER
)

from .zip import ZipFolder

__all__ = ('export',)


def export(entities, filename=None, file_format=None, overwrite=False, silent=False, use_compression=True, **kwargs):
    """Export AiiDA data

    :param entities: a list of entity instances; they can belong to different models/entities.
    :type entities: list

    :param filename: the filename (possibly including the absolute path) of the file on which to export.
    :type filename: str

    :param file_format: Can be either 'zip' or 'tar' (Default: 'zip').
    :type file_format: str

    :param overwrite: if True, overwrite the output file without asking, if it exists. If False, raise an
        :py:class:`~aiida.tools.importexport.common.exceptions.ArchiveExportError` if the output file already exists.
    :type overwrite: bool

    :param silent: suppress prints.
    :type silent: bool

    :param use_compression: Whether or not to compress the archive file (only valid for the zip file format).
    :type use_compression: bool

    :param allowed_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type allowed_licenses: list

    :param forbidden_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type forbidden_licenses: list

    :param include_comments: In-/exclude export of comments for given node(s) in ``entities``.
        Default: True, *include* comments in export (as well as relevant users).
    :type include_comments: bool

    :param include_logs: In-/exclude export of logs for given node(s) in ``entities``.
        Default: True, *include* logs in export.
    :type include_logs: bool

    :param kwargs: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`: if there are any internal errors when
        exporting.
    :raises `~aiida.common.exceptions.LicensingException`: if any node is licensed under forbidden license.
    """
    if file_format is None:
        file_format = 'zip'
    elif file_format not in ('tar', 'zip'):
        raise exceptions.ArchiveExportError(
            'Can only export in either "tar" or "zip" format, please specify either for "file_format".'
        )

    filename = filename if filename is not None and isinstance(filename, str) else 'export_data.aiida'

    if not overwrite and os.path.exists(filename):
        raise exceptions.ArchiveExportError("The output file '{}' already exists".format(filename))

    if not silent:
        if file_format == 'tar':
            file_format_verbose = 'Gzipped tarball (compressed)'
        elif use_compression:
            file_format_verbose = 'Zip (compressed)'
        else:
            file_format_verbose = 'Zip (uncompressed)'
        summary(file_format_verbose, filename, **kwargs)

    try:
        if file_format == 'tar':
            times = export_tar(what=entities, outfile=filename, silent=silent, **kwargs)
        else:  # zip
            times = export_zip(
                what=entities, outfile=filename, use_compression=use_compression, silent=silent, **kwargs
            )
    except (exceptions.ArchiveExportError, LicensingException) as exc:
        if os.path.exists(filename):
            os.remove(filename)
        raise exc

    if len(times) == 2:
        export_start, export_end = times
        EXPORT_LOGGER.debug('Exported in %6.2g s.', export_end - export_start)
    elif len(times) == 4:
        export_start, export_end, compress_start, compress_end = times
        EXPORT_LOGGER.debug(
            'Exported in %6.2g s, compressed in %6.2g s, total: %6.2g s.', export_end - export_start,
            compress_end - compress_start, compress_end - export_start
        )
    else:
        EXPORT_LOGGER.debug('No information about the timing of the export.')


def export_zip(what, outfile, use_compression=True, **kwargs):
    """Export in a zipped folder

    :param what: a list of entity instances; they can belong to different models/entities.
    :type what: list

    :param outfile: the filename (possibly including the absolute path) of the file on which to export.
    :type outfile: str

    :param use_compression: Whether or not to compress the zip file.
    :type use_compression: bool
    """
    with ZipFolder(outfile, mode='w', use_compression=use_compression) as folder:
        time_start = time.time()
        export_tree(what, folder=folder, **kwargs)
        time_end = time.time()

    return (time_start, time_end)


def export_tar(what, outfile, **kwargs):
    """Export the entries passed in the 'what' list to a tar file.

    :param what: a list of entity instances; they can belong to different models/entities.
    :type what: list

    :param outfile: the filename (possibly including the absolute path) of the file on which to export.
    :type outfile: str
    """
    with SandboxFolder() as folder:
        time_export_start = time.time()
        export_tree(what, folder=folder, **kwargs)
        time_export_end = time.time()

        with tarfile.open(outfile, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as tar:
            time_compress_start = time.time()
            tar.add(folder.abspath, arcname='')
            time_compress_end = time.time()

    return (time_export_start, time_export_end, time_compress_start, time_compress_end)


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
    from aiida.tools.graph.graph_traversers import get_nodes_export

    EXPORT_LOGGER.debug('STARTING EXPORT...')

    all_fields_info, unique_identifiers = get_all_fields_info()

    entities_starting_set = defaultdict(set)

    # The set that contains the nodes ids of the nodes that should be exported
    given_node_entry_ids = set()
    given_log_entry_ids = set()
    given_comment_entry_ids = set()

    if not silent:
        # Instantiate progress bar - go through list of "what"
        pbar_total = len(what) + 1 if what else 1
        progress_bar = tqdm(total=pbar_total, bar_format=BAR_FORMAT, leave=True)
        progress_bar.set_description_str('Collecting chosen entities', refresh=False)

    # I store a list of the actual dbnodes
    for entry in what:
        if not silent:
            progress_bar.update()

        # This returns the class name (as in imports). E.g. for a model node:
        # aiida.backends.djsite.db.models.DbNode
        # entry_class_string = get_class_string(entry)
        # Now a load the backend-independent name into entry_entity_name, e.g. Node!
        # entry_entity_name = schema_to_entity_names(entry_class_string)
        if issubclass(entry.__class__, orm.Group):
            entities_starting_set[GROUP_ENTITY_NAME].add(entry.uuid)
        elif issubclass(entry.__class__, orm.Node):
            entities_starting_set[NODE_ENTITY_NAME].add(entry.uuid)
            given_node_entry_ids.add(entry.pk)
        elif issubclass(entry.__class__, orm.Computer):
            entities_starting_set[COMPUTER_ENTITY_NAME].add(entry.uuid)
        else:
            raise exceptions.ArchiveExportError(
                'I was given {} ({}), which is not a Node, Computer, or Group instance'.format(entry, type(entry))
            )

    # Add all the nodes contained within the specified groups
    if GROUP_ENTITY_NAME in entities_starting_set:

        if not silent:
            progress_bar.set_description_str('Retrieving Nodes from Groups ...', refresh=True)

        # Use single query instead of given_group.nodes iterator for performance.
        qh_groups = orm.QueryBuilder().append(
            orm.Group, filters={
                'uuid': {
                    'in': entities_starting_set[GROUP_ENTITY_NAME]
                }
            }, tag='groups'
        ).queryhelp

        # Delete this import once the dbexport.zip module has been renamed
        from builtins import zip  # pylint: disable=redefined-builtin

        node_results = orm.QueryBuilder(**qh_groups).append(orm.Node, project=['id', 'uuid'], with_group='groups').all()
        if node_results:
            pks, uuids = map(list, zip(*node_results))
            entities_starting_set[NODE_ENTITY_NAME].update(uuids)
            given_node_entry_ids.update(pks)
            del node_results, pks, uuids

        if not silent:
            progress_bar.update()

    # We will iteratively explore the AiiDA graph to find further nodes that should also be exported.
    # At the same time, we will create the links_uuid list of dicts to be exported

    if not silent:
        progress_bar.reset(total=1)
        progress_bar.set_description_str('Getting provenance and storing links ...', refresh=True)

    traverse_output = get_nodes_export(starting_pks=given_node_entry_ids, get_links=True, **kwargs)
    node_ids_to_be_exported = traverse_output['nodes']
    graph_traversal_rules = traverse_output['rules']

    # A utility dictionary for mapping PK to UUID.
    if node_ids_to_be_exported:
        qbuilder = orm.QueryBuilder().append(
            orm.Node,
            project=('id', 'uuid'),
            filters={'id': {
                'in': node_ids_to_be_exported
            }},
        )
        node_pk_2_uuid_mapping = dict(qbuilder.all())
    else:
        node_pk_2_uuid_mapping = {}

    # The set of tuples now has to be transformed to a list of dicts
    links_uuid = [{
        'input': node_pk_2_uuid_mapping[link.source_id],
        'output': node_pk_2_uuid_mapping[link.target_id],
        'label': link.link_label,
        'type': link.link_type
    } for link in traverse_output['links']]

    if not silent:
        progress_bar.update()

    if not silent:
        # Progress bar initialization - Entities
        progress_bar.reset(total=1)
        progress_bar.set_description_str('Initializing export of all entities', refresh=True)

    ## Universal "entities" attributed to all types of nodes
    # Logs
    if include_logs and node_ids_to_be_exported:
        # Get related log(s) - universal for all nodes
        builder = orm.QueryBuilder()
        builder.append(orm.Log, filters={'dbnode_id': {'in': node_ids_to_be_exported}}, project='uuid')
        res = set(builder.all(flat=True))
        given_log_entry_ids.update(res)

    # Comments
    if include_comments and node_ids_to_be_exported:
        # Get related log(s) - universal for all nodes
        builder = orm.QueryBuilder()
        builder.append(orm.Comment, filters={'dbnode_id': {'in': node_ids_to_be_exported}}, project='uuid')
        res = set(builder.all(flat=True))
        given_comment_entry_ids.update(res)

    # Here we get all the columns that we plan to project per entity that we would like to extract
    given_entities = set(entities_starting_set.keys())
    if node_ids_to_be_exported:
        given_entities.add(NODE_ENTITY_NAME)
    if given_log_entry_ids:
        given_entities.add(LOG_ENTITY_NAME)
    if given_comment_entry_ids:
        given_entities.add(COMMENT_ENTITY_NAME)

    if not silent:
        progress_bar.update()

    if not silent and given_entities:
        progress_bar.reset(total=len(given_entities))
        pbar_base_str = 'Preparing entities'

    entries_to_add = dict()
    for given_entity in given_entities:
        if not silent:
            progress_bar.set_description_str(pbar_base_str + ' - {}s'.format(given_entity), refresh=False)
            progress_bar.update()

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
        entry_uuids_to_add = entities_starting_set.get(given_entity, set())
        if not entry_uuids_to_add:
            if given_entity == LOG_ENTITY_NAME:
                entry_uuids_to_add = given_log_entry_ids
            elif given_entity == COMMENT_ENTITY_NAME:
                entry_uuids_to_add = given_comment_entry_ids
        elif given_entity == NODE_ENTITY_NAME:
            entry_uuids_to_add.update({node_pk_2_uuid_mapping[_] for _ in node_ids_to_be_exported})

        builder = orm.QueryBuilder()
        builder.append(
            entity_names_to_entities[given_entity],
            filters={'uuid': {
                'in': entry_uuids_to_add
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
        builder.append(
            orm.Node, project=['id', 'attributes.source.license'], filters={'id': {
                'in': node_ids_to_be_exported
            }}
        )
        # Skip those nodes where the license is not set (this is the standard behavior with Django)
        node_licenses = list((a, b) for [a, b] in builder.all() if b is not None)
        check_licenses(node_licenses, allowed_licenses, forbidden_licenses)

    ############################################################
    ##### Start automatic recursive export data generation #####
    ############################################################
    EXPORT_LOGGER.debug('GATHERING DATABASE ENTRIES...')

    if not silent and entries_to_add:
        progress_bar.reset(total=len(entries_to_add))

    export_data = defaultdict(dict)
    entity_separator = '_'
    for entity_name, partial_query in entries_to_add.items():

        if not silent:
            progress_bar.set_description_str('Exporting {}s'.format(entity_name), refresh=False)
            progress_bar.update()

        foreign_fields = {k: v for k, v in all_fields_info[entity_name].items() if 'requires' in v}

        for value in foreign_fields.values():
            ref_model_name = value['requires']
            fill_in_query(partial_query, entity_name, ref_model_name, [entity_name], entity_separator)

        for temp_d in partial_query.iterdict():
            for key in temp_d:
                # Get current entity
                current_entity = key.split(entity_separator)[-1]

                # This is a empty result of an outer join.
                # It should not be taken into account.
                if temp_d[key]['id'] is None:
                    continue

                export_data[current_entity].update({
                    temp_d[key]['id']:
                    serialize_dict(
                        temp_d[key], remove_fields=['id'], rename_fields=model_fields_to_file_fields[current_entity]
                    )
                })

    if not silent:
        # Close progress up until this point in order to print properly
        progress_bar.leave = False
        progress_bar.close()

    #######################################
    # Manually manage attributes and extras
    #######################################
    # Pointer. Renaming, since Nodes have now technically been retrieved and "stored"
    all_node_pks = node_ids_to_be_exported

    model_data = sum(len(model_data) for model_data in export_data.values())
    if not model_data:
        msg = 'Nothing to store, exiting...'
        if not silent:
            print(msg)
        EXPORT_LOGGER.debug(msg)
        return

    msg = 'Exporting a total of {} database entries, of which {} are Nodes.'.format(model_data, len(all_node_pks))
    if not silent:
        print(msg)
    EXPORT_LOGGER.debug(msg)

    if not silent:
        # Instantiate new progress bar
        progress_bar = tqdm(total=1, bar_format=BAR_FORMAT, leave=True)

    # ATTRIBUTES and EXTRAS
    EXPORT_LOGGER.debug('GATHERING NODE ATTRIBUTES AND EXTRAS...')
    node_attributes = {}
    node_extras = {}

    # Another QueryBuilder query to get the attributes and extras. TODO: See if this can be optimized
    if all_node_pks:
        all_nodes_query = orm.QueryBuilder().append(
            orm.Node, filters={'id': {
                'in': all_node_pks
            }}, project=['id', 'attributes', 'extras']
        )

        if not silent:
            progress_bar.reset(total=all_nodes_query.count())
            progress_bar.set_description_str('Exporting Attributes and Extras', refresh=False)

        for node_pk, attributes, extras in all_nodes_query.iterall():
            if not silent:
                progress_bar.update()

            node_attributes[str(node_pk)] = attributes
            node_extras[str(node_pk)] = extras

    EXPORT_LOGGER.debug('GATHERING GROUP ELEMENTS...')
    groups_uuid = defaultdict(list)
    # If a group is in the exported data, we export the group/node correlation
    if GROUP_ENTITY_NAME in export_data:
        group_uuids_with_node_uuids = orm.QueryBuilder().append(
            orm.Group, filters={
                'id': {
                    'in': export_data[GROUP_ENTITY_NAME]
                }
            }, project='uuid', tag='groups'
        ).append(orm.Node, project='uuid', with_group='groups')

        if not silent:
            total_node_uuids_for_groups = group_uuids_with_node_uuids.count()
            if total_node_uuids_for_groups:
                progress_bar.reset(total=total_node_uuids_for_groups)
                progress_bar.set_description_str('Exporting Groups ...', refresh=False)

        for group_uuid, node_uuid in group_uuids_with_node_uuids.iterall():
            if not silent:
                progress_bar.update()

            groups_uuid[group_uuid].append(node_uuid)

    #######################################
    # Final check for unsealed ProcessNodes
    #######################################
    process_nodes = set()
    for node_pk, content in export_data.get(NODE_ENTITY_NAME, {}).items():
        if content['node_type'].startswith('process.'):
            process_nodes.add(node_pk)

    check_process_nodes_sealed(process_nodes)

    ######################################
    # Now collecting and storing
    ######################################
    # subfolder inside the export package
    nodesubfolder = folder.get_subfolder(NODES_EXPORT_SUBFOLDER, create=True, reset_limit=True)

    EXPORT_LOGGER.debug('ADDING DATA TO EXPORT ARCHIVE...')

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

    # Turn sets into lists to be able to export them as JSON metadata.
    for entity, entity_set in entities_starting_set.items():
        entities_starting_set[entity] = list(entity_set)

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

    EXPORT_LOGGER.debug('ADDING REPOSITORY FILES TO EXPORT ARCHIVE...')

    # If there are no nodes, there are no repository files to store
    if all_node_pks:
        all_node_uuids = {node_pk_2_uuid_mapping[_] for _ in all_node_pks}

        if not silent:
            progress_bar.reset(total=len(all_node_uuids))
            pbar_base_str = 'Exporting repository - '

        for uuid in all_node_uuids:
            sharded_uuid = export_shard_uuid(uuid)

            if not silent:
                progress_bar.set_description_str(pbar_base_str + 'UUID={}'.format(uuid.split('-')[0]), refresh=False)
                progress_bar.update()

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

    if not silent:
        progress_bar.leave = False
        progress_bar.close()
