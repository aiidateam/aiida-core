# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=fixme,too-many-lines
"""Provides export functionalities."""
from abc import ABC, abstractmethod
from collections import defaultdict
import logging
import os
import tarfile
import time
from typing import (
    Any,
    Callable,
    ContextManager,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)
import warnings

from aiida import get_version, orm
from aiida.common import json
from aiida.common.exceptions import LicensingException
from aiida.common.folders import Folder, RepositoryFolder, SandboxFolder
from aiida.common.links import GraphTraversalRules
from aiida.common.lang import type_check
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.common.progress_reporter import get_progress_reporter
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.orm.utils._repository import Repository
from aiida.tools.importexport.common import (
    exceptions,
)
from aiida.tools.importexport.common.config import (
    COMMENT_ENTITY_NAME,
    COMPUTER_ENTITY_NAME,
    EXPORT_VERSION,
    GROUP_ENTITY_NAME,
    LOG_ENTITY_NAME,
    NODE_ENTITY_NAME,
    NODES_EXPORT_SUBFOLDER,
    entity_names_to_entities,
    file_fields_to_model_fields,
    get_all_fields_info,
    model_fields_to_file_fields,
)
from aiida.tools.graph.graph_traversers import get_nodes_export, validate_traversal_rules
from aiida.tools.importexport.archive.writers import ArchiveMetadata, ArchiveWriterAbstract, get_writer
from aiida.tools.importexport.common.config import ExportFileFormat
from aiida.tools.importexport.common.utils import export_shard_uuid
from aiida.tools.importexport.dbexport.utils import (
    EXPORT_LOGGER,
    check_licenses,
    check_process_nodes_sealed,
    deprecated_parameters,
    fill_in_query,
    serialize_dict,
    summary,
)

__all__ = ('export', 'EXPORT_LOGGER', 'ExportFileFormat')


def export(
    entities: Optional[Iterable[Any]] = None,
    filename: Optional[str] = None,
    file_format: Union[str, Type[ArchiveWriterAbstract]] = ExportFileFormat.ZIP,
    overwrite: bool = False,
    silent: Optional[bool] = None,
    use_compression: Optional[bool] = None,
    include_comments: bool = True,
    include_logs: bool = True,
    allowed_licenses: Optional[Union[list, Callable]] = None,
    forbidden_licenses: Optional[Union[list, Callable]] = None,
    writer_init: Optional[Dict[str, Any]] = None,
    batch_size: int = 100,
    **traversal_rules: bool,
) -> ArchiveWriterAbstract:
    """Export AiiDA data to an archive file.

    Note, the logging level and progress reporter should be set externally, for example::

        from aiida.common.progress_reporter import set_progress_bar_tqdm

        EXPORT_LOGGER.setLevel('DEBUG')
        set_progress_bar_tqdm(leave=True)
        export(...)

    .. deprecated:: 1.5.0
        Support for the parameter `silent` will be removed in `v2.0.0`.
        Please set the log level and progress bar implementation independently.

    .. deprecated:: 1.5.0
        Support for the parameter `use_compression` will be removed in `v2.0.0`.
        Please use `writer_init={'use_compression': True}`.

    .. deprecated:: 1.2.1
        Support for the parameters `what` and `outfile` will be removed in `v2.0.0`.
        Please use `entities` and `filename` instead, respectively.

    :param entities: a list of entity instances;
        they can belong to different models/entities.

    :param filename: the filename (possibly including the absolute path)
        of the file on which to export.

    :param file_format: 'zip', 'tar.gz' or 'folder' or a specific writer class.

    :param overwrite: if True, overwrite the output file without asking, if it exists.
        If False, raise an
        :py:class:`~aiida.tools.importexport.common.exceptions.ArchiveExportError`
        if the output file already exists.

    :param allowed_licenses: List or function.
        If a list, then checks whether all licenses of Data nodes are in the list. If a function,
        then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.

    :param forbidden_licenses: List or function. If a list,
        then checks whether all licenses of Data nodes are in the list. If a function,
        then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.

    :param include_comments: In-/exclude export of comments for given node(s) in ``entities``.
        Default: True, *include* comments in export (as well as relevant users).

    :param include_logs: In-/exclude export of logs for given node(s) in ``entities``.
        Default: True, *include* logs in export.

    :param writer_init: Additional key-word arguments to pass to the writer class init

    :param batch_size: batch database query results in sub-collections to reduce memory usage

    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules`
        what rule names are toggleable and what the defaults are.

    :returns: a dictionary of data regarding the export process (timings, etc)

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`:
        if there are any internal errors when exporting.
    :raises `~aiida.common.exceptions.LicensingException`:
        if any node is licensed under forbidden license.
    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements

    # Backwards-compatibility
    entities = cast(
        Iterable[Any],
        deprecated_parameters(
            old={
                'name': 'what',
                'value': traversal_rules.pop('what', None)
            },
            new={
                'name': 'entities',
                'value': entities
            },
        ),
    )
    filename = cast(
        str,
        deprecated_parameters(
            old={
                'name': 'outfile',
                'value': traversal_rules.pop('outfile', None)
            },
            new={
                'name': 'filename',
                'value': filename
            },
        ),
    )
    if silent is not None:
        warnings.warn(
            'silent keyword is deprecated and will be removed in AiiDA v2.0.0, set the logger level explicitly instead',
            AiidaDeprecationWarning
        )  # pylint: disable=no-member

    type_check(
        entities,
        (list, tuple, set),
        msg='`entities` must be specified and given as a list of AiiDA entities',
    )
    entities = list(entities)
    if type_check(filename, str, allow_none=True) is None:
        filename = 'export_data.aiida'

    if not overwrite and os.path.exists(filename):
        raise exceptions.ArchiveExportError(f"The output file '{filename}' already exists")

    # validate the traversal rules and generate a full set for reporting
    validate_traversal_rules(GraphTraversalRules.EXPORT, **traversal_rules)
    full_traversal_rules = {
        name: traversal_rules.get(name, rule.default) for name, rule in GraphTraversalRules.EXPORT.value.items()
    }

    # setup the archive writer
    writer_init = writer_init or {}
    if use_compression is not None:
        warnings.warn(
            'use_compression argument is deprecated and will be removed in AiiDA v2.0.0 (which will always compress)',
            AiidaDeprecationWarning
        )  # pylint: disable=no-member
        writer_init['use_compression'] = use_compression
    if isinstance(file_format, str):
        writer = get_writer(file_format)(filepath=filename, **writer_init)
    elif issubclass(file_format, ArchiveWriterAbstract):
        writer = file_format(filepath=filename, **writer_init)
    else:
        raise TypeError('file_format must be a string or ArchiveWriterAbstract class')

    summary(
        file_format=writer.file_format_verbose,
        export_version=writer.export_version,
        outfile=filename,
        include_comments=include_comments,
        include_logs=include_logs,
        traversal_rules=full_traversal_rules
    )

    EXPORT_LOGGER.debug('STARTING EXPORT...')

    all_fields_info, unique_identifiers = get_all_fields_info()
    entities_starting_set, given_node_entry_ids = _get_starting_node_ids(entities)

    # Initialize the writer
    with writer as writer_context:

        # Iteratively explore the AiiDA graph to find further nodes that should also be exported
        with get_progress_reporter()(desc='Traversing provenance via links ...', total=1) as progress:
            traverse_output = get_nodes_export(starting_pks=given_node_entry_ids, get_links=True, **traversal_rules)
            progress.update()
        node_ids_to_be_exported = traverse_output['nodes']

        EXPORT_LOGGER.debug('WRITING METADATA...')

        writer_context.write_metadata(
            ArchiveMetadata(
                export_version=EXPORT_VERSION,
                aiida_version=get_version(),
                unique_identifiers=unique_identifiers,
                all_fields_info=all_fields_info,
                graph_traversal_rules=traverse_output['rules'],
                # Turn sets into lists to be able to export them as JSON metadata.
                entities_starting_set={
                    entity: list(entity_set) for entity, entity_set in entities_starting_set.items()
                },
                include_comments=include_comments,
                include_logs=include_logs,
            )
        )

        # Create a mapping of node PK to UUID.
        node_pk_2_uuid_mapping: Dict[int, str] = {}
        if node_ids_to_be_exported:
            qbuilder = orm.QueryBuilder().append(
                orm.Node,
                project=('id', 'uuid'),
                filters={'id': {
                    'in': node_ids_to_be_exported
                }},
            )
            node_pk_2_uuid_mapping = dict(qbuilder.all(batch_size=batch_size))

        # check that no nodes are being exported with incorrect licensing
        _check_node_licenses(node_ids_to_be_exported, allowed_licenses, forbidden_licenses)

        # write the link data
        if traverse_output['links'] is not None:
            with get_progress_reporter()(total=len(traverse_output['links']), desc='Writing links') as progress:
                for link in traverse_output['links']:
                    progress.update()
                    writer_context.write_link({
                        'input': node_pk_2_uuid_mapping[link.source_id],
                        'output': node_pk_2_uuid_mapping[link.target_id],
                        'label': link.link_label,
                        'type': link.link_type,
                    })

        # generate a list of queries to encapsulate all required entities
        entity_queries = _collect_entity_queries(
            node_ids_to_be_exported,
            entities_starting_set,
            node_pk_2_uuid_mapping,
            include_comments,
            include_logs,
        )

        total_entities = sum(query.count() for query in entity_queries.values())

        # write all entity data fields
        if total_entities:
            exported_entity_pks = _write_entity_data(
                total_entities=total_entities,
                entity_queries=entity_queries,
                writer=writer_context,
                batch_size=batch_size
            )
        else:
            exported_entity_pks = defaultdict(set)
            EXPORT_LOGGER.info('No entities were found to export')

        # write mappings of groups to the nodes they contain
        if exported_entity_pks[GROUP_ENTITY_NAME]:

            EXPORT_LOGGER.debug('Writing group UUID -> [nodes UUIDs]')

            _write_group_mappings(
                group_pks=exported_entity_pks[GROUP_ENTITY_NAME], batch_size=batch_size, writer=writer_context
            )

        # copy all required node repositories
        if exported_entity_pks[NODE_ENTITY_NAME]:

            _write_node_repositories(
                node_pks=exported_entity_pks[NODE_ENTITY_NAME],
                node_pk_2_uuid_mapping=node_pk_2_uuid_mapping,
                writer=writer_context
            )

        EXPORT_LOGGER.info('Finalizing Export...')

    # summarize export
    export_summary = '\n  - '.join(f'{name:<6}: {len(pks)}' for name, pks in exported_entity_pks.items())
    if exported_entity_pks:
        EXPORT_LOGGER.info('Exported Entities:\n  - ' + export_summary + '\n')
    # TODO
    # EXPORT_LOGGER.info('Writer Information:\n %s', writer.export_info)

    return writer


def _get_starting_node_ids(entities: List[Any]) -> Tuple[DefaultDict[str, Set[str]], Set[int]]:
    """Get the starting node UUIDs and PKs

    :param entities: a list of entity instances

    :raises exceptions.ArchiveExportError:
    :return: entities_starting_set, given_node_entry_ids
    """
    entities_starting_set: DefaultDict[str, Set[str]] = defaultdict(set)
    given_node_entry_ids: Set[int] = set()

    # store a list of the actual dbnodes
    total = len(entities) + (1 if GROUP_ENTITY_NAME in entities_starting_set else 0)
    if not total:
        return entities_starting_set, given_node_entry_ids

    for entry in entities:

        if issubclass(entry.__class__, orm.Group):
            entities_starting_set[GROUP_ENTITY_NAME].add(entry.uuid)
        elif issubclass(entry.__class__, orm.Node):
            entities_starting_set[NODE_ENTITY_NAME].add(entry.uuid)
            given_node_entry_ids.add(entry.pk)
        elif issubclass(entry.__class__, orm.Computer):
            entities_starting_set[COMPUTER_ENTITY_NAME].add(entry.uuid)
        else:
            raise exceptions.ArchiveExportError(
                f'I was given {entry} ({type(entry)}),'
                ' which is not a Node, Computer, or Group instance'
            )

    # Add all the nodes contained within the specified groups
    if GROUP_ENTITY_NAME in entities_starting_set:

        # Use single query instead of given_group.nodes iterator for performance.
        qh_groups = (
            orm.QueryBuilder().append(
                orm.Group,
                filters={
                    'uuid': {
                        'in': entities_starting_set[GROUP_ENTITY_NAME]
                    }
                },
                tag='groups',
            ).queryhelp
        )
        node_query = orm.QueryBuilder(**qh_groups).append(orm.Node, project=['id', 'uuid'], with_group='groups')
        node_count = node_query.count()

        if node_count:
            with get_progress_reporter()(desc='Collecting nodes in groups', total=node_count) as progress:

                pks, uuids = [], []
                for pk, uuid in node_query.all():
                    progress.update()
                    pks.append(pk)
                    uuids.append(uuid)

            entities_starting_set[NODE_ENTITY_NAME].update(uuids)
            given_node_entry_ids.update(pks)

    return entities_starting_set, given_node_entry_ids


def _check_node_licenses(
    node_ids_to_be_exported: Set[int],
    allowed_licenses: Optional[Union[list, Callable]],
    forbidden_licenses: Optional[Union[list, Callable]],
) -> None:
    """Check the nodes to be archived for disallowed licences."""
    # TODO (Spyros) To see better! Especially for functional licenses
    # Check the licenses of exported data.
    if allowed_licenses is not None or forbidden_licenses is not None:
        builder = orm.QueryBuilder()
        builder.append(
            orm.Node,
            project=['id', 'attributes.source.license'],
            filters={'id': {
                'in': node_ids_to_be_exported
            }},
        )
        # Skip those nodes where the license is not set (this is the standard behavior with Django)
        node_licenses = [(a, b) for [a, b] in builder.all() if b is not None]
        check_licenses(node_licenses, allowed_licenses, forbidden_licenses)


def _get_model_fields(entity_name: str) -> List[str]:
    """Return a list of fields to retrieve for a particular entity

    :param entity_name: name of database entity, such as Node

    """
    all_fields_info, _ = get_all_fields_info()
    project_cols = ['id']
    entity_prop = all_fields_info[entity_name].keys()
    # Here we do the necessary renaming of properties
    for prop in entity_prop:
        # nprop contains the list of projections
        nprop = (
            file_fields_to_model_fields[entity_name][prop] if prop in file_fields_to_model_fields[entity_name] else prop
        )
        project_cols.append(nprop)
    return project_cols


def _collect_entity_queries(
    node_ids_to_be_exported: Set[int],
    entities_starting_set: DefaultDict[str, Set[str]],
    node_pk_2_uuid_mapping: Dict[int, str],
    include_comments: bool = True,
    include_logs: bool = True,
) -> Dict[str, orm.QueryBuilder]:
    """Gather partial queries for all entities to export."""
    # pylint: disable=too-many-locals
    given_log_entry_ids = set()
    given_comment_entry_ids = set()

    total = 2 + (((1 if include_logs else 0) + (1 if include_comments else 0)) if node_ids_to_be_exported else 0)
    with get_progress_reporter()(desc='Building entity database queries', total=total) as progress:

        # Logs
        if include_logs and node_ids_to_be_exported:
            # Get related log(s) - universal for all nodes
            builder = orm.QueryBuilder()
            builder.append(
                orm.Log,
                filters={'dbnode_id': {
                    'in': node_ids_to_be_exported
                }},
                project='uuid',
            )
            res = set(builder.all(flat=True))
            given_log_entry_ids.update(res)

            progress.update()

        # Comments
        if include_comments and node_ids_to_be_exported:
            # Get related log(s) - universal for all nodes
            builder = orm.QueryBuilder()
            builder.append(
                orm.Comment,
                filters={'dbnode_id': {
                    'in': node_ids_to_be_exported
                }},
                project='uuid',
            )
            res = set(builder.all(flat=True))
            given_comment_entry_ids.update(res)

            progress.update()

        # Here we get all the columns that we plan to project per entity that we would like to extract
        given_entities = set(entities_starting_set.keys())
        if node_ids_to_be_exported:
            given_entities.add(NODE_ENTITY_NAME)
        if given_log_entry_ids:
            given_entities.add(LOG_ENTITY_NAME)
        if given_comment_entry_ids:
            given_entities.add(COMMENT_ENTITY_NAME)

        progress.update()

        entities_to_add: Dict[str, orm.QueryBuilder] = {}
        if not given_entities:
            progress.update()
            return entities_to_add

        for given_entity in given_entities:

            project_cols = _get_model_fields(given_entity)

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
                outerjoin=True,
            )
            entities_to_add[given_entity] = builder

        progress.update()

    return entities_to_add


def _write_entity_data(
    total_entities: int, entity_queries: Dict[str, orm.QueryBuilder], writer: ArchiveWriterAbstract, batch_size: int
) -> Dict[str, Set[int]]:
    """Iterate through data returned from entity queries, serialize the DB fields, then write to the export."""
    all_fields_info, unique_identifiers = get_all_fields_info()
    entity_separator = '_'

    exported_entity_pks: Dict[str, Set[int]] = defaultdict(set)
    unsealed_node_pks: Set[int] = set()

    with get_progress_reporter()(total=total_entities, desc='Writing entity data') as progress:

        for entity_name, entity_query in entity_queries.items():

            foreign_fields = {k: v for k, v in all_fields_info[entity_name].items() if 'requires' in v}
            for value in foreign_fields.values():
                ref_model_name = value['requires']
                fill_in_query(
                    entity_query,
                    entity_name,
                    ref_model_name,
                    [entity_name],
                    entity_separator,
                )

            for query_results in entity_query.iterdict(batch_size=batch_size):

                progress.update()

                for key, value in query_results.items():

                    pk = value['id']

                    # This is an empty result of an outer join.
                    # It should not be taken into account.
                    if pk is None:
                        continue

                    # Get current entity
                    current_entity = key.split(entity_separator)[-1]

                    # don't allow duplication
                    if pk in exported_entity_pks[current_entity]:
                        continue

                    exported_entity_pks[current_entity].add(pk)

                    fields = serialize_dict(
                        value,
                        remove_fields=['id'],
                        rename_fields=model_fields_to_file_fields[current_entity],
                    )

                    if current_entity == NODE_ENTITY_NAME and fields['node_type'].startswith('process.'):
                        if fields['attributes'].get('sealed', False) is not True:
                            unsealed_node_pks.add(pk)

                    writer.write_entity_data(current_entity, pk, unique_identifiers[current_entity], fields)

    if unsealed_node_pks:
        raise exceptions.ExportValidationError(
            'All ProcessNodes must be sealed before they can be exported. '
            f"Node(s) with PK(s): {', '.join(str(pk) for pk in unsealed_node_pks)} is/are not sealed."
        )

    return exported_entity_pks


def _write_group_mappings(*, group_pks: Set[int], batch_size: int, writer: ArchiveWriterAbstract):
    """Query for node UUIDs in exported groups, and write these these mappings to the archive file."""
    group_uuid_query = orm.QueryBuilder().append(
        orm.Group,
        filters={
            'id': {
                'in': list(group_pks)
            }
        },
        project='uuid',
        tag='groups',
    ).append(orm.Node, project='uuid', with_group='groups')

    groups_uuid_to_node_uuids = defaultdict(set)
    for group_uuid, node_uuid in group_uuid_query.iterall(batch_size=batch_size):
        groups_uuid_to_node_uuids[group_uuid].add(node_uuid)

    for group_uuid, node_uuids in groups_uuid_to_node_uuids.items():
        writer.write_group_nodes(group_uuid, list(node_uuids))


def _write_node_repositories(
    *, node_pks: Set[int], node_pk_2_uuid_mapping: Dict[int, str], writer: ArchiveWriterAbstract
):
    """Write all exported node repositories to the archive file."""
    with get_progress_reporter()(total=len(node_pks), desc='Exporting node repositories: ') as progress:

        for pk in node_pks:

            uuid = node_pk_2_uuid_mapping[pk]

            progress.set_description_str(f'Exporting node repositories: {pk}', refresh=False)
            progress.update()

            src = RepositoryFolder(section=Repository._section_name, uuid=uuid)  # pylint: disable=protected-access
            if not src.exists():
                raise exceptions.ArchiveExportError(
                    f'Unable to find the repository folder for Node with UUID={uuid} '
                    'in the local repository'
                )
            writer.write_node_repo_folder(uuid, src._abspath)  # pylint: disable=protected-access


# THESE FUNCTIONS ARE ONLY ADDED FOR BACK-COMPATIBILITY


def export_tree(
    entities: Optional[Iterable[Any]] = None,
    folder: Optional[Folder] = None,
    allowed_licenses: Optional[Union[list, Callable]] = None,
    forbidden_licenses: Optional[Union[list, Callable]] = None,
    silent: Optional[bool] = None,
    include_comments: bool = True,
    include_logs: bool = True,
    **traversal_rules: bool,
) -> None:
    """Export the entries passed in the 'entities' list to a file tree.
    .. deprecated:: 1.2.1
        Support for the parameter `what` will be removed in `v2.0.0`. Please use `entities` instead.
    :param entities: a list of entity instances; they can belong to different models/entities.

    :param folder: a temporary folder to build the archive in.

    :param allowed_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.

    :param forbidden_licenses: List or function. If a list, then checks whether all licenses of Data nodes are in the
        list. If a function, then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.

    :param silent: suppress console prints and progress bar.

    :param include_comments: In-/exclude export of comments for given node(s) in ``entities``.
        Default: True, *include* comments in export (as well as relevant users).

    :param include_logs: In-/exclude export of logs for given node(s) in ``entities``.
        Default: True, *include* logs in export.

    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules` what rule names
        are toggleable and what the defaults are.

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`: if there are any internal errors when
        exporting.
    :raises `~aiida.common.exceptions.LicensingException`: if any node is licensed under forbidden license.
    """
    warnings.warn(
        'export_tree function is deprecated and will be removed in AiiDA v2.0.0, use `export` instead',
        AiidaDeprecationWarning
    )  # pylint: disable=no-member
    export(
        entities=entities,
        filename='none',
        overwrite=True,
        file_format='folder',
        allowed_licenses=allowed_licenses,
        forbidden_licenses=forbidden_licenses,
        silent=silent,
        include_comments=include_comments,
        include_logs=include_logs,
        writer_init={'folder': folder},
        **traversal_rules,
    )


def export_zip(
    entities: Optional[Iterable[Any]] = None,
    filename: Optional[str] = None,
    use_compression: bool = True,
    **kwargs: Any,
) -> Tuple[float, float]:
    """Export in a zipped folder

    .. deprecated:: 1.2.1
        Support for the parameters `what` and `outfile` will be removed in `v2.0.0`.
        Please use `entities` and `filename` instead, respectively.

    :param entities: a list of entity instances; they can belong to different models/entities.

    :param filename: the filename
        (possibly including the absolute path) of the file on which to export.

    :param use_compression: Whether or not to compress the zip file.

    """
    warnings.warn(
        'export_zip function is deprecated and will be removed in AiiDA v2.0.0, use `export` instead',
        AiidaDeprecationWarning
    )  # pylint: disable=no-member
    writer = export(
        entities=entities,
        filename=filename,
        file_format=ExportFileFormat.ZIP,
        use_compression=use_compression,
        **kwargs,
    )
    return writer.export_info['writer_entered'], writer.export_info['writer_exited']


def export_tar(
    entities: Optional[Iterable[Any]] = None,
    filename: Optional[str] = None,
    **kwargs: Any,
) -> Tuple[float, float, float, float]:
    """Export the entries passed in the 'entities' list to a gzipped tar file.

    .. deprecated:: 1.2.1
        Support for the parameters `what` and `outfile` will be removed in `v2.0.0`.
        Please use `entities` and `filename` instead, respectively.

    :param entities: a list of entity instances; they can belong to different models/entities.

    :param filename: the filename (possibly including the absolute path)
        of the file on which to export.
    """
    warnings.warn(
        'export_tar function is deprecated and will be removed in AiiDA v2.0.0, use `export` instead',
        AiidaDeprecationWarning
    )  # pylint: disable=no-member
    writer = export(
        entities=entities,
        filename=filename,
        file_format=ExportFileFormat.TAR_GZIPPED,
        **kwargs,
    )

    # the tar is now directly written to, so no compression start/stop time!
    return (
        writer.export_info['writer_entered'], writer.export_info['writer_exited'], writer.export_info['writer_exited'],
        writer.export_info['writer_exited']
    )
