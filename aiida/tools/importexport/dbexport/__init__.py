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
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
import logging
import os
import tarfile
import time
from typing import (
    Any,
    Callable,
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

from aiida import get_version, orm
from aiida.common import json
from aiida.common.exceptions import LicensingException
from aiida.common.folders import Folder, RepositoryFolder, SandboxFolder
from aiida.common.lang import type_check
from aiida.common.log import LOG_LEVEL_REPORT, override_log_formatter
from aiida.orm.utils._repository import Repository
from aiida.tools.importexport.common import (
    close_progress_bar,
    exceptions,
    get_progress_bar,
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
from aiida.tools.importexport.common.utils import export_shard_uuid
from aiida.tools.importexport.dbexport.utils import (
    EXPORT_LOGGER,
    ExportFileFormat,
    check_licenses,
    check_process_nodes_sealed,
    deprecated_parameters,
    fill_in_query,
    serialize_dict,
    summary,
)
from aiida.tools.importexport.dbexport.zip import ZipFolder

__all__ = ('export', 'EXPORT_LOGGER', 'ExportFileFormat')


@dataclass
class ExportData:
    """Class for storing data to export."""
    metadata: dict
    all_node_uuids: Set[str]
    entity_data: Dict[str, Dict[int, dict]]
    node_attributes: Dict[str, dict]
    node_extras: Dict[str, dict]
    groups_uuid: Dict[str, List[str]]
    links_uuid: List[dict]


class WriterAbstract(ABC):

    def __init__(self, filename: str, **kwargs: Any):
        """An archive writer

        :param filename: the filename (possibly including the absolute path)
            of the file on which to export.
        """
        # pylint: disable=unused-argument
        self._filename = filename

    @property
    def filename(self) -> str:
        return self._filename

    @property
    @abstractmethod
    def file_format_verbose(self) -> str:
        """The file format name."""

    @abstractmethod
    def write(
        self,
        export_data: ExportData,
        silent: bool = False,
    ) -> str:
        """write the archive and return a message."""


def _write_to_json_archive(folder: Union[Folder, ZipFolder], export_data: ExportData, silent: bool = False) -> None:
    """Store data to the archive."""
    # subfolder inside the export package
    nodesubfolder = folder.get_subfolder(NODES_EXPORT_SUBFOLDER, create=True, reset_limit=True)

    EXPORT_LOGGER.debug('ADDING DATA TO EXPORT ARCHIVE...')

    data = {
        'node_attributes': export_data.node_attributes,
        'node_extras': export_data.node_extras,
        'export_data': export_data.entity_data,
        'links_uuid': export_data.links_uuid,
        'groups_uuid': export_data.groups_uuid,
    }

    # N.B. We're really calling zipfolder.open (if exporting a zipfile)
    with folder.open('data.json', mode='w') as fhandle:
        # fhandle.write(json.dumps(data, cls=UUIDEncoder))
        fhandle.write(json.dumps(data))

    with folder.open('metadata.json', 'w') as fhandle:
        fhandle.write(json.dumps(export_data.metadata))

    EXPORT_LOGGER.debug('ADDING REPOSITORY FILES TO EXPORT ARCHIVE...')

    # If there are no nodes, there are no repository files to store
    if export_data.all_node_uuids:

        progress_bar = get_progress_bar(total=len(export_data.all_node_uuids), disable=silent)
        pbar_base_str = 'Exporting repository - '

        for uuid in export_data.all_node_uuids:
            sharded_uuid = export_shard_uuid(uuid)

            progress_bar.set_description_str(f"{pbar_base_str}UUID={uuid.split('-')[0]}", refresh=False)
            progress_bar.update()

            # Important to set create=False, otherwise creates twice a subfolder.
            # Maybe this is a bug of insert_path?
            thisnodefolder = nodesubfolder.get_subfolder(sharded_uuid, create=False, reset_limit=True)

            # Make sure the node's repository folder was not deleted
            src = RepositoryFolder(section=Repository._section_name, uuid=uuid)  # pylint: disable=protected-access
            if not src.exists():
                raise exceptions.ArchiveExportError(
                    f'Unable to find the repository folder for Node with UUID={uuid} '
                    'in the local repository'
                )

            # In this way, I copy the content of the folder, and not the folder itself
            thisnodefolder.insert_path(src=src.abspath, dest_name='.')


class WriterJsonZip(WriterAbstract):

    def __init__(self, filename: str, **kwargs: Any):
        """An archive writer

        :param filename: the filename (possibly including the absolute path)
            of the file on which to export.
        :param use_compression: Whether or not to compress the zip file.

        """
        super().__init__(filename, **kwargs)
        self._use_compression = kwargs.get('use_compression', True)

    @property
    def file_format_verbose(self) -> str:
        return 'Zip (compressed)' if self._use_compression else 'Zip (uncompressed)'

    def write(
        self,
        export_data: ExportData,
        silent: bool = False,
    ) -> str:
        """write the archive

        :param entities: a list of entity instances; they can belong to different models/entities.
        :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules`
            what rule names are toggleable and what the defaults are.

        """
        with ZipFolder(self.filename, mode='w', use_compression=self._use_compression) as folder:
            time_start = time.time()
            _write_to_json_archive(folder=folder, export_data=export_data, silent=silent)
            time_end = time.time()

        return f'Written in {time_end - time_start:6.2g} s.'


class WriterJsonTar(WriterAbstract):

    @property
    def file_format_verbose(self) -> str:
        return 'Gzipped tarball (compressed)'

    def write(
        self,
        export_data: ExportData,
        silent: bool = False,
    ) -> str:
        """write the archive

        :param entities: a list of entity instances; they can belong to different models/entities.
        :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules`
            what rule names are toggleable and what the defaults are.

        """
        with SandboxFolder() as folder:
            time_write_start = time.time()
            _write_to_json_archive(folder=folder, export_data=export_data, silent=silent)
            time_write_end = time.time()

            with tarfile.open(self.filename, 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as tar:
                time_compress_start = time.time()
                tar.add(folder.abspath, arcname='')
                time_compress_end = time.time()

        return (
            f'Written in {time_write_end - time_write_start:6.2g} s, '
            f'compressed in {time_compress_end - time_compress_start:6.2g} s, '
            f'total: {time_compress_end - time_write_start:6.2g} s.'
        )


def get_writers() -> Dict[str, Type[WriterAbstract]]:
    return {ExportFileFormat.ZIP: WriterJsonZip, ExportFileFormat.TAR_GZIPPED: WriterJsonTar}


def export(
    entities: Optional[Iterable[Any]] = None,
    filename: Optional[str] = None,
    file_format: str = ExportFileFormat.ZIP,
    overwrite: bool = False,
    silent: bool = False,
    use_compression: bool = True,
    **traversal_rules: bool,
) -> None:
    """Export AiiDA data

    .. deprecated:: 1.2.1
        Support for the parameters `what` and `outfile` will be removed in `v2.0.0`.
        Please use `entities` and `filename` instead, respectively.

    :param entities: a list of entity instances;
        they can belong to different models/entities.

    :param filename: the filename (possibly including the absolute path)
        of the file on which to export.

    :param file_format: See `ExportFileFormat` for complete list of valid values (default: 'zip').

    :param overwrite: if True, overwrite the output file without asking, if it exists.
        If False, raise an
        :py:class:`~aiida.tools.importexport.common.exceptions.ArchiveExportError`
        if the output file already exists.

    :param silent: suppress console prints and progress bar.

    :param use_compression: Whether or not to compress the archive file
        (only valid for the zip file format).

    :param allowed_licenses: List or function.
        If a list, then checks whether all licenses of Data nodes are in the list. If a function,
        then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type allowed_licenses: list

    :param forbidden_licenses: List or function. If a list,
        then checks whether all licenses of Data nodes are in the list. If a function,
        then calls function for licenses of Data nodes expecting True if license is allowed, False
        otherwise.
    :type forbidden_licenses: list

    :param include_comments: In-/exclude export of comments for given node(s) in ``entities``.
        Default: True, *include* comments in export (as well as relevant users).
    :type include_comments: bool

    :param include_logs: In-/exclude export of logs for given node(s) in ``entities``.
        Default: True, *include* logs in export.
    :type include_logs: bool

    :param traversal_rules: graph traversal rules. See :const:`aiida.common.links.GraphTraversalRules`
        what rule names are toggleable and what the defaults are.

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`:
        if there are any internal errors when exporting.
    :raises `~aiida.common.exceptions.LicensingException`:
        if any node is licensed under forbidden license.
    """
    writers = get_writers()

    if file_format not in list(writers):
        raise exceptions.ArchiveExportError(
            f'Can only export in the formats: {tuple(writers.keys())}, please specify one for "file_format".'
        )

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

    if silent:
        logging.disable(logging.CRITICAL)

    writer = writers[file_format](filename=filename, use_compression=use_compression)

    summary(writer.file_format_verbose, filename, **traversal_rules)

    time_extract_start = time.time()
    export_data = generate_data(entities=entities, silent=silent, **traversal_rules)
    time_extract_stop = time.time()

    if export_data is not None:

        EXPORT_LOGGER.debug(f'Data extracted in {time_extract_stop - time_extract_start:6.2g} s.')

        try:
            message = writer.write(export_data=export_data, silent=silent)
        except (exceptions.ArchiveExportError, LicensingException) as exc:
            if os.path.exists(filename):
                os.remove(filename)
            raise exc

        EXPORT_LOGGER.debug(message)

    # Reset logging level
    if silent:
        logging.disable(logging.NOTSET)


@override_log_formatter('%(message)s')
def generate_data(
    entities: Optional[Iterable[Any]] = None,
    allowed_licenses: Optional[Union[list, Callable]] = None,
    forbidden_licenses: Optional[Union[list, Callable]] = None,
    silent: bool = False,
    include_comments: bool = True,
    include_logs: bool = True,
    **traversal_rules: bool,
) -> Optional[ExportData]:
    """Export the entries passed in the 'entities' list to a file tree.

    .. deprecated:: 1.2.1
        Support for the parameter `what` will be removed in `v2.0.0`. Please use `entities` instead.

    :param entities: a list of entity instances; they can belong to different models/entities.

    :param allowed_licenses: List or function.
        If a list, then checks whether all licenses of Data nodes are in the list.
        If a function, then calls function for licenses of Data nodes,
        expecting True if license is allowed, False otherwise.

    :param forbidden_licenses: List or function.
        If a list, then checks whether all licenses of Data nodes are in the list.
        If a function, then calls function for licenses of Data nodes,
        expecting True if license is allowed, False otherwise.

    :param silent: suppress console prints and progress bar.

    :param include_comments: In-/exclude export of comments for given node(s) in ``entities``.
        Default: True, *include* comments in export (as well as relevant users).

    :param include_logs: In-/exclude export of logs for given node(s) in ``entities``.
        Default: True, *include* logs in export.

    :param traversal_rules: graph traversal rules.
        See :const:`aiida.common.links.GraphTraversalRules`
        what rule names are toggleable and what the defaults are.

    :raises `~aiida.tools.importexport.common.exceptions.ArchiveExportError`:
        if there are any internal errors when exporting.
    :raises `~aiida.common.exceptions.LicensingException`:
        if any node is licensed under forbidden license.
    """

    if silent:
        logging.disable(logging.CRITICAL)

    EXPORT_LOGGER.debug('STARTING EXPORT...')

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

    type_check(
        entities,
        (list, tuple, set),
        msg='`entities` must be specified and given as a list of AiiDA entities',
    )
    entities = list(entities)

    all_fields_info, unique_identifiers = get_all_fields_info()

    entities_starting_set, given_node_entry_ids = get_starting_node_ids(entities, silent)

    (
        node_ids_to_be_exported,
        node_pk_2_uuid_mapping,
        links_uuid,
        traversal_rules,
    ) = collect_export_nodes(given_node_entry_ids, silent, **traversal_rules)

    check_node_licenses(node_ids_to_be_exported, allowed_licenses, forbidden_licenses)

    entries_queries = get_entry_queries(
        node_ids_to_be_exported,
        entities_starting_set,
        node_pk_2_uuid_mapping,
        silent,
        include_comments,
        include_logs,
    )

    export_data = get_export_data(entries_queries, silent)

    # Close progress up until this point in order to print properly
    close_progress_bar(leave=False)

    # note this was originally below the attributes and group_uuid gather
    check_process_nodes_sealed({
        node_pk for node_pk, content in export_data.get(NODE_ENTITY_NAME, {}).items()
        if content['node_type'].startswith('process.')
    })

    model_data = sum(len(model_data) for model_data in export_data.values())
    if not model_data:
        EXPORT_LOGGER.log(msg='Nothing to store, exiting...', level=LOG_LEVEL_REPORT)
        return None
    EXPORT_LOGGER.log(
        msg=(
            f'Exporting a total of {model_data} database entries, '
            f'of which {len(node_ids_to_be_exported)} are Nodes.'
        ),
        level=LOG_LEVEL_REPORT,
    )

    node_attributes, node_extras = get_node_data(node_ids_to_be_exported, silent)
    groups_uuid = get_groups_uuid(export_data, silent)

    # Turn sets into lists to be able to export them as JSON metadata.
    for entity, entity_set in entities_starting_set.items():
        entities_starting_set[entity] = list(entity_set)  # type: ignore

    metadata = {
        'aiida_version': get_version(),
        'export_version': EXPORT_VERSION,
        'all_fields_info': all_fields_info,
        'unique_identifiers': unique_identifiers,
        'export_parameters': {
            'graph_traversal_rules': traversal_rules,
            'entities_starting_set': entities_starting_set,
            'include_comments': include_comments,
            'include_logs': include_logs,
        },
    }

    all_node_uuids = {node_pk_2_uuid_mapping[_] for _ in node_ids_to_be_exported}

    close_progress_bar(leave=False)

    # Reset logging level
    if silent:
        logging.disable(logging.NOTSET)

    return ExportData(
        metadata,
        all_node_uuids,
        export_data,
        node_attributes,
        node_extras,
        groups_uuid,
        links_uuid,
    )


def get_starting_node_ids(entities: List[Any], silent: bool) -> Tuple[DefaultDict[str, Set[str]], Set[int]]:
    """Get the starting node UUIDs and PKs

    :param entities: a list of entity instances
    :param silent: suppress console prints and progress bar.

    :raises exceptions.ArchiveExportError
    :return: entities_starting_set, given_node_entry_ids
    """
    # Instantiate progress bar - go through list of `entities`
    pbar_total = len(entities) + 1 if entities else 1
    progress_bar = get_progress_bar(total=pbar_total, leave=False, disable=silent)
    progress_bar.set_description_str('Collecting chosen entities', refresh=False)

    entities_starting_set = defaultdict(set)
    given_node_entry_ids = set()

    # I store a list of the actual dbnodes
    for entry in entities:
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
                f'I was given {entry} ({type(entry)}),'
                ' which is not a Node, Computer, or Group instance'
            )

    # Add all the nodes contained within the specified groups
    if GROUP_ENTITY_NAME in entities_starting_set:

        progress_bar.set_description_str('Retrieving Nodes from Groups ...', refresh=True)

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

        # Delete this import once the dbexport.zip module has been renamed
        from builtins import zip  # pylint: disable=redefined-builtin

        node_results = (
            orm.QueryBuilder(**qh_groups).append(orm.Node, project=['id', 'uuid'], with_group='groups').all()
        )
        if node_results:
            pks, uuids = map(list, zip(*node_results))
            entities_starting_set[NODE_ENTITY_NAME].update(uuids)
            given_node_entry_ids.update(pks)
            del node_results, pks, uuids

        progress_bar.update()

    return entities_starting_set, given_node_entry_ids


def collect_export_nodes(given_node_entry_ids: Set[int], silent: bool,
                         **traversal_rules: bool) -> Tuple[Set[int], Dict[int, str], List[dict], Dict[str, bool]]:
    """Iteratively explore the AiiDA graph to find further nodes that should also be exported

    At the same time, we will create the links_uuid list of dicts to be exported

    :param silent: suppress console prints and progress bar.
    """
    from aiida.tools.graph.graph_traversers import get_nodes_export

    progress_bar = get_progress_bar(total=1, disable=silent)
    progress_bar.set_description_str('Getting provenance and storing links ...', refresh=True)

    traverse_output = get_nodes_export(starting_pks=given_node_entry_ids, get_links=True, **traversal_rules)
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
        'type': link.link_type,
    } for link in traverse_output['links']]

    progress_bar.update()

    return (
        node_ids_to_be_exported,
        node_pk_2_uuid_mapping,
        links_uuid,
        graph_traversal_rules,
    )


def check_node_licenses(
    node_ids_to_be_exported: Set[int],
    allowed_licenses: Optional[Union[list, Callable]],
    forbidden_licenses: Optional[Union[list, Callable]],
) -> None:
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


def get_entry_queries(
    node_ids_to_be_exported: Set[int],
    entities_starting_set: DefaultDict[str, Set[str]],
    node_pk_2_uuid_mapping: Dict[int, str],
    silent: bool,
    include_comments: bool = True,
    include_logs: bool = True,
) -> Dict[str, orm.QueryBuilder]:
    """Gather partial queries for all entities to export."""
    # Progress bar initialization - Entities
    progress_bar = get_progress_bar(total=1, disable=silent)
    progress_bar.set_description_str('Initializing export of all entities', refresh=True)

    given_log_entry_ids = set()
    given_comment_entry_ids = set()
    all_fields_info, _ = get_all_fields_info()

    # Universal "entities" attributed to all types of nodes
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

    # Here we get all the columns that we plan to project per entity that we would like to extract
    given_entities = set(entities_starting_set.keys())
    if node_ids_to_be_exported:
        given_entities.add(NODE_ENTITY_NAME)
    if given_log_entry_ids:
        given_entities.add(LOG_ENTITY_NAME)
    if given_comment_entry_ids:
        given_entities.add(COMMENT_ENTITY_NAME)

    progress_bar.update()

    if given_entities:
        progress_bar = get_progress_bar(total=len(given_entities), disable=silent)
        pbar_base_str = 'Preparing entities'

    entries_to_add = {}
    for given_entity in given_entities:
        progress_bar.set_description_str(f'{pbar_base_str} - {given_entity}s', refresh=False)
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
            outerjoin=True,
        )
        entries_to_add[given_entity] = builder

    return entries_to_add


def get_export_data(entries_queries: Dict[str, orm.QueryBuilder], silent: bool) -> Dict[str, Dict[int, dict]]:
    """Start automatic recursive export data generation

    :param entries_queries: partial queries for all entities to export
    :param silent: suppress console prints and progress bar.

    :return: export data mappings by entity type -> pk -> db_columns, e.g.
        {'ENTITY_NAME': {<pk>: {'uuid': 'abc', ...}, ...}, ...}
        Note: this data does not yet contain attributes and extras

    """
    EXPORT_LOGGER.debug('GATHERING DATABASE ENTRIES...')

    all_fields_info, _ = get_all_fields_info()

    if entries_queries:
        progress_bar = get_progress_bar(total=len(entries_queries), disable=silent)

    export_data = defaultdict(dict)  # type: dict
    entity_separator = '_'
    for entity_name, partial_query in entries_queries.items():

        progress_bar.set_description_str(f'Exporting {entity_name}s', refresh=False)
        progress_bar.update()

        foreign_fields = {k: v for k, v in all_fields_info[entity_name].items() if 'requires' in v}

        for value in foreign_fields.values():
            ref_model_name = value['requires']
            fill_in_query(
                partial_query,
                entity_name,
                ref_model_name,
                [entity_name],
                entity_separator,
            )

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
                        temp_d[key],
                        remove_fields=['id'],
                        rename_fields=model_fields_to_file_fields[current_entity],
                    )
                })

    return export_data


def get_node_data(all_node_pks: Set[int], silent: bool) -> Tuple[Dict[str, dict], Dict[str, dict]]:
    """Gather attributes and extras for nodes

    :param export_data:  mappings by entity type -> pk -> db_columns
    :param all_node_pks: set of pks
    :param silent: for progress printing

    :return: attributes, extras

    """

    # Instantiate new progress bar
    progress_bar = get_progress_bar(total=1, leave=False, disable=silent)

    # ATTRIBUTES and EXTRAS
    EXPORT_LOGGER.debug('GATHERING NODE ATTRIBUTES AND EXTRAS...')
    node_attributes = {}
    node_extras = {}

    # Another QueryBuilder query to get the attributes and extras.
    # TODO: See if this can be optimized
    if all_node_pks:
        all_nodes_query = orm.QueryBuilder().append(
            orm.Node,
            filters={'id': {
                'in': all_node_pks
            }},
            project=['id', 'attributes', 'extras'],
        )

        progress_bar = get_progress_bar(total=all_nodes_query.count(), disable=silent)
        progress_bar.set_description_str('Exporting Attributes and Extras', refresh=False)

        for node_pk, attributes, extras in all_nodes_query.iterall():
            progress_bar.update()

            node_attributes[str(node_pk)] = attributes
            node_extras[str(node_pk)] = extras

    return node_attributes, node_extras


def get_groups_uuid(export_data: Dict[str, Dict[int, dict]], silent: bool) -> Dict[str, List[str]]:
    """Get node UUIDs per group."""
    EXPORT_LOGGER.debug('GATHERING GROUP ELEMENTS...')
    groups_uuid = defaultdict(list)
    # If a group is in the exported data, we export the group/node correlation
    if GROUP_ENTITY_NAME in export_data:
        group_uuids_with_node_uuids = (
            orm.QueryBuilder().append(
                orm.Group,
                filters={
                    'id': {
                        'in': export_data[GROUP_ENTITY_NAME]
                    }
                },
                project='uuid',
                tag='groups',
            ).append(orm.Node, project='uuid', with_group='groups')
        )

        # This part is _only_ for the progress bar
        total_node_uuids_for_groups = group_uuids_with_node_uuids.count()
        if total_node_uuids_for_groups:
            progress_bar = get_progress_bar(total=total_node_uuids_for_groups, disable=silent)
            progress_bar.set_description_str('Exporting Groups ...', refresh=False)

        for group_uuid, node_uuid in group_uuids_with_node_uuids.iterall():
            progress_bar.update()

            groups_uuid[group_uuid].append(node_uuid)

    return groups_uuid
